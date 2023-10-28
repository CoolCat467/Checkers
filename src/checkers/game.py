#!/usr/bin/env python3
# Graphical Checkers Game

"Graphical Checkers Game"

# Programmed by CoolCat467

# Note: Tile Ids are chess board tile titles, A1 to H8
# A8 ... H8
# .........
# A1 ... H1

# 0 = False = Red   = 0, 2
# 1 = True  = Black = 1, 3

from __future__ import annotations

import os
import platform
import random
import struct
import traceback
from collections import deque
from functools import partial
from os import path
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar, cast

import pygame
import trio
from pygame.color import Color
from pygame.locals import K_ESCAPE, KEYUP, QUIT, WINDOWRESIZED
from pygame.rect import Rect

from . import base2d, objects, sprite
from .async_clock import Clock
from .base_io import StructFormat
from .buffer import Buffer
from .client import GameClient
from .component import (
    Component,
    ComponentManager,
    Event,
    ExternalRaiseManager,
)
from .network import NetworkEventComponent, Server, TimeoutException
from .network_shared import read_position, write_position
from .objects import Button, OutlinedText
from .state import ActionSet, State
from .statemachine import AsyncState
from .vector import Vector2

if TYPE_CHECKING:
    from collections.abc import (
        Awaitable,
        Callable,
        Generator,
        Iterable,
        Sequence,
    )

    from pygame.surface import Surface

__title__ = "Checkers"
__version__ = "0.0.5"
__author__ = "CoolCat467"

SCREEN_SIZE = (640, 480)

FPS = 48
VSYNC = True
PORT = 31613

PLAYERS = ["Red Player", "Black Player"]


BLACK = (0, 0, 0)
BLUE = (15, 15, 255)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
RED = (255, 0, 0)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)


T = TypeVar("T")

IS_WINDOWS = platform.system() == "Windows"

Pos: TypeAlias = tuple[int, int]


def render_text(
    font_name: str, font_size: int, text: str, color: tuple[int, int, int]
) -> Surface:
    "Render text with a given font at font_size with the text in the color of color"
    # Load the font at the size of font_size
    font = pygame.font.Font(font_name, font_size)
    # Using the loaded font, render the text in the color of color
    surf = font.render(text, False, color)
    return surf


class Piece(sprite.Sprite):
    "Piece Sprite"
    __slots__ = (
        "piece_type",
        "board_position",
        "position_name",
        "selected",
        "destination_tiles",
    )

    def __init__(
        self,
        piece_type: int,
        position: tuple[int, int],
        position_name: str,
        location: tuple[int, int] | Vector2,
    ) -> None:
        super().__init__(f"piece_{position_name}")

        self.piece_type = piece_type
        self.board_position = position
        self.position_name = position_name
        self.location = location

        self.selected = False
        self.destination_tiles: list[tuple[Pos, Pos, Pos]] = []

        self.update_location_on_resize = True

        self.add_components(
            (
                sprite.DragClickEventComponent(),
                sprite.MovementComponent(speed=120),
                sprite.TargetingComponent(),
            )
        )

    def bind_handlers(self) -> None:
        "Register handlers"
        if not self.manager_exists:
            return
        self.set_outlined(False)
        self.visible = True

        self.register_handlers(
            {
                "click": self.handle_click_event,
                f"piece_outline_{self.position_name}": self.handle_set_outline_event,
                f"destroy_piece_{self.position_name}": self.handle_self_destruct_event,
                f"piece_move_{self.position_name}": self.handle_move_event,
                "reached_destination": self.handle_reached_destination_event,
                f"piece_update_{self.position_name}": self.handle_update_event,
            }
        )

    def set_outlined(self, state: bool) -> None:
        "Update image given new outline state"
        manager_image: sprite.ImageComponent = self.manager.get_component(
            "image"
        )
        value = "_outlined" if state else ""
        self.image = manager_image.get_image(f"piece_{self.piece_type}{value}")

    async def handle_click_event(
        self, event: Event[dict[str, Pos | int]]
    ) -> None:
        "Raise gameboard_piece_clicked events when clicked"
        await self.raise_event(
            Event(
                "gameboard_piece_clicked",
                (
                    self.board_position,
                    self.piece_type,
                ),
                3,
            )
        )

    async def handle_set_outline_event(self, event: Event[bool]) -> None:
        "Update outlined state"
        self.set_outlined(event.data)

    async def handle_self_destruct_event(self, event: Event[None]) -> None:
        "Remove self from play"
        self.kill()
        self.manager.remove_component(self.name)

    async def handle_tick_event(
        self, event: Event[sprite.TickEventData]
    ) -> None:
        "Move toward destination"
        time_passed = event.data.time_passed
        targeting: sprite.TargetingComponent = self.get_component("targeting")
        await targeting.move_destination_time(time_passed)

    async def handle_move_event(
        self, event: Event[Iterable[tuple[Pos, Pos, Pos]]]
    ) -> None:
        "Handle movement animation to event position"
        targeting: sprite.TargetingComponent = self.get_component("targeting")
        self.destination_tiles.extend(event.data)
        targeting.destination = self.destination_tiles[0][0]

        # Only register tick handler when we need to.
        # This is because, as a tick event is fired every frame,
        # if we have like 30 things fireing every frame and they aren't
        # even moving, that's a lot of processing power wasted.
        if not self.has_handler("tick"):
            self.register_handler("tick", self.handle_tick_event)
        group = self.groups()[0]
        group.move_to_front(self)  # type: ignore[attr-defined]

    async def handle_reached_destination_event(
        self, event: Event[None]
    ) -> None:
        "Raise gameboard_piece_moved event"
        _, start_pos, end_pos = self.destination_tiles.pop(0)

        if self.destination_tiles:
            targeting: sprite.TargetingComponent = self.get_component(
                "targeting"
            )
            targeting.destination = self.destination_tiles[0][0]
        await self.raise_event(
            Event(
                "gameboard_piece_moved",
                (
                    self.position_name,
                    start_pos,
                    end_pos,
                    not self.destination_tiles,
                ),
                1,
            )
        )

    async def handle_update_event(self, event: Event[int]) -> None:
        """Update self during movement animation"""
        self.piece_type = event.data
        self.set_outlined(False)
        # Inform board that animation is complete
        await self.raise_event(Event("fire_next_animation", None, 1))


class Tile(sprite.Sprite):
    "Outlined tile sprite - Only exists for selecting destination"
    __slots__ = ("color", "board_position", "position_name")

    def __init__(
        self,
        color: int,
        position: tuple[int, int],
        position_name: str,
        location: tuple[int, int] | Vector2,
    ) -> None:
        super().__init__(f"tile_{position_name}")

        self.color = color
        self.board_position = position
        self.position_name = position_name
        self.location = location

        self.update_location_on_resize = True

        self.add_component(sprite.DragClickEventComponent())

    def bind_handlers(self) -> None:
        "Register handlers"
        if not self.manager_exists:
            return
        self.set_outlined(True)

        self.visible = True

        self.register_handlers(
            {
                "click": self.handle_click_event,
                f"self_destruct_tile_{self.position_name}": self.handle_self_destruct_event,
            }
        )

    def set_outlined(self, state: bool) -> None:
        "Update image given new outline state"
        manager_image: sprite.ImageComponent = self.manager.get_component(
            "image"
        )
        value = "_outlined" if state else ""
        self.image = manager_image.get_image(f"tile_{self.color}{value}")

    async def handle_click_event(
        self, event: Event[dict[str, Pos | int]]
    ) -> None:
        "Raise gameboard_tile_clicked events when clicked"
        await self.raise_event(
            Event(
                "gameboard_tile_clicked",
                self.board_position,
                3,
            )
        )

    async def handle_self_destruct_event(self, event: Event[None]) -> None:
        "Remove from all groups and remove self component"
        self.kill()
        self.manager.remove_component(self.name)


def generate_tile_image(
    color: Color
    | int
    | str
    | tuple[int, int, int]
    | tuple[int, int, int, int]
    | Sequence[int],
    size: tuple[int, int],
) -> Surface:
    "Generate the image used for a tile"
    surf = pygame.Surface(size)
    surf.fill(color)
    return surf


class GameBoard(sprite.Sprite):
    "Entity that stores data about the game board and renders it"
    __slots__ = (
        "board_size",
        "tile_size",
        "tile_surfs",
        "pieces",
        "animation_queue",
        "processing_animations",
    )

    # Define Tile Color Map and Piece Map
    tile_color_map = (BLACK, RED)

    # Define Black Pawn color to be more of a dark grey so you can see it
    black = (127, 127, 127)
    red = (160, 0, 0)

    # Define each piece by giving what color it should be and an image
    # to recolor
    piece_map = (
        (red, "data/Pawn.png"),
        (black, "data/Pawn.png"),
        (red, "data/King.png"),
        (black, "data/King.png"),
    )

    def __init__(
        self,
        board_size: tuple[int, int],
        tile_size: int,
    ) -> None:
        super().__init__("board")

        self.add_component(sprite.ImageComponent())

        # Store the Board Size and Tile Size
        self.board_size = board_size
        self.tile_size = tile_size

        self.update_location_on_resize = True

        self.pieces: dict[Pos, int] = {}

        self.animation_queue: deque[Event[object]] = deque()
        self.processing_animations = False

    def get_tile_name(self, x: int, y: int) -> str:
        """Get name of a given tile"""
        return chr(65 + x) + str(self.board_size[1] - y)

    def bind_handlers(self) -> None:
        "Register handlers"
        self.register_handlers(
            {
                "init": self.handle_init_event,
                "gameboard_create_piece": self.handle_create_piece_event,
                "gameboard_select_piece": self.handle_select_piece_event,
                "gameboard_create_tile": self.handle_create_tile_event,
                "gameboard_delete_tile": self.handle_delete_tile_event,
                "gameboard_delete_piece_animation": self.handle_delete_piece_animation_event,
                "gameboard_update_piece_animation": self.handle_update_piece_animation_event,
                "gameboard_move_piece_animation": self.handle_move_piece_animation_event,
                "gameboard_delete_piece": self.handle_delete_piece_event,
                "gameboard_update_piece": self.handle_update_piece_event,
                "gameboard_move_piece": self.handle_move_piece_event,
                "gameboard_animation_state": self.handle_animation_state,
                "game_winner": self.handle_game_winner,
                "fire_next_animation": self.handle_fire_next_animation,
                "gameboard_piece_moved": self.handle_piece_moved_event,
            }
        )

    async def handle_init_event(self, event: Event[None]) -> None:
        "Start up game"
        # Generate tile data
        self.generate_tile_images()
        self.image = self.generate_board_image()
        self.visible = True

    async def handle_select_piece_event(
        self, event: Event[tuple[Pos, bool]]
    ) -> None:
        """Send piece outline event"""
        piece_pos, outline_value = event.data
        piece_name = self.get_tile_name(*piece_pos)
        await self.raise_event(
            Event(f"piece_outline_{piece_name}", outline_value)
        )

    async def handle_piece_moved_event(
        self, event: Event[tuple[str, Pos, Pos, bool]]
    ) -> None:
        """Handle piece finishing one part of it's movement animation"""
        await self.raise_event(Event("fire_next_animation", None))

    async def handle_create_piece_event(
        self, event: Event[tuple[Pos, int]]
    ) -> None:
        """Handle create_piece event"""
        piece_pos, piece_type = event.data
        self.add_piece(piece_type, piece_pos)

    async def handle_create_tile_event(self, event: Event[Pos]) -> None:
        """Handle create_tile event"""
        tile_pos = event.data
        self.add_tile(tile_pos)

    async def handle_delete_tile_event(self, event: Event[Pos]) -> None:
        """Handle delete_tile event"""
        tile_pos = event.data
        tile_name = self.get_tile_name(*tile_pos)
        await self.raise_event(Event(f"self_destruct_tile_{tile_name}", None))

    async def handle_delete_piece_animation_event(
        self, event: Event[Pos]
    ) -> None:
        """Handle delete_animation_piece event"""
        self.animation_queue.append(
            Event(event.name.removesuffix("_animation"), event.data)
        )

    async def handle_delete_piece_event(self, event: Event[Pos]) -> None:
        """Handle delete_piece event"""
        piece_pos = event.data
        piece_name = self.get_tile_name(*piece_pos)
        await self.raise_event(Event(f"destroy_piece_{piece_name}", None))
        self.pieces.pop(piece_pos)
        await self.raise_event(Event("fire_next_animation", None))

    async def handle_update_piece_animation_event(
        self, event: Event[tuple[Pos, int]]
    ) -> None:
        """Handle update_piece_animation event"""
        self.animation_queue.append(
            Event(event.name.removesuffix("_animation"), event.data)
        )

    async def handle_update_piece_event(
        self, event: Event[tuple[Pos, int]]
    ) -> None:
        """Handle update_piece event"""
        piece_pos, piece_type = event.data
        self.pieces[piece_pos] = piece_type
        piece_name = self.get_tile_name(*piece_pos)
        await self.raise_event(Event(f"piece_update_{piece_name}", piece_type))

    async def handle_move_piece_animation_event(
        self, event: Event[tuple[Pos, Pos]]
    ) -> None:
        """Handle move_piece_animation event"""
        self.animation_queue.append(
            Event(event.name.removesuffix("_animation"), event.data)
        )

    async def handle_move_piece_event(
        self, event: Event[tuple[Pos, Pos]]
    ) -> None:
        """Handle move_piece event"""
        from_pos, to_pos = event.data

        from_name = self.get_tile_name(*from_pos)
        to_location = self.get_tile_location(to_pos)

        self.add_piece(
            self.pieces.pop(from_pos),  # Same type as parent
            to_pos,
            self.get_tile_location(from_pos),
        )

        await self.raise_event(Event(f"destroy_piece_{from_name}", None))

        to_name = self.get_tile_name(*to_pos)

        await self.raise_event(
            Event(
                f"piece_move_{to_name}",
                [(to_location, from_pos, to_pos)],
            )
        )

    async def new_animating_state(self, new_state: bool) -> None:
        """Process animation start or end."""
        # Add important start/end block information as an event to the queue
        self.animation_queue.append(Event("animation_state", new_state))

        if new_state:
            return

        # Stopping, end of animation block
        if not self.processing_animations:
            self.processing_animations = True
            await self.raise_event(Event("fire_next_animation", None))

    async def handle_animation_state(self, event: Event[bool]) -> None:
        """Handle animation_state event."""
        new_animating_state = event.data

        await self.new_animating_state(new_animating_state)

    async def handle_game_winner(self, _: Event[int] | None) -> None:
        """Handle game_winner event."""
        # Process end of final animation
        await self.new_animating_state(False)

    async def handle_fire_next_animation(
        self, _: Event[None] | None = None
    ) -> None:
        """Start next animation."""
        assert self.processing_animations

        if not self.animation_queue:
            self.processing_animations = False
            return

        queue_event = self.animation_queue.popleft()

        # If we find animation_state block
        if queue_event.name == "animation_state":
            # If start block or no more animations
            if queue_event.data or not self.animation_queue:
                # Handle one more tick to trigger stop
                await self.handle_fire_next_animation()
                return
            # Otherwise, state event is False, meaning just popped end of block.
            # This means next event should always be new block start event
            if self.animation_queue[0].name != "animation_state":
                raise RuntimeError("Expected animation_state block!")
            assert self.animation_queue[0].data, "expected start block"
            # Since we have a start block, make sure we have all the data
            # before we play the animation; Otherwise we can end up in a state
            # where we are still reading animations while they are playing,
            # which is a race condition waiting to happen.

            # Search queue for end block
            has_end = False
            for event in self.animation_queue:
                if event.name == "animation_state" and not event.data:
                    has_end = True
                    break
            if has_end:
                # Found end, keep ticking animations, we have all the data
                await self.handle_fire_next_animation()
                return
            # if ran through queue, still reading animations from
            # server.
            self.animation_queue.appendleft(queue_event)
            await trio.sleep(0)
            await self.handle_fire_next_animation()
            return
        await self.raise_event(queue_event)

    def generate_tile_images(self) -> None:
        """Load all the images"""
        image: sprite.ImageComponent = self.get_component("image")
        outline: sprite.OutlineComponent = image.get_component("outline")
        outline.size = 2

        base_folder = os.path.dirname(__file__)

        for index, color in enumerate(self.tile_color_map):
            name = f"tile_{index}"
            surface = generate_tile_image(
                color, (self.tile_size, self.tile_size)
            )

            if index == 0:
                image.add_image(name, surface)
            else:
                image.add_image_and_mask(name, surface, "tile_0")

            if index % 2 != 0:
                continue

            outline_color = GREEN
            outline_ident = outline.precalculate_outline(name, outline_color)
            image.add_image(f"{name}_outlined", outline_ident)

        # Generate a Piece Surface for each piece using a base image and a color
        for piece_type, piece_data in enumerate(self.piece_map):
            color, filename = piece_data
            real_path = os.path.join(base_folder, *filename.split("/"))

            name = f"piece_{piece_type}"
            surface = base2d.replace_with_color(
                pygame.transform.scale(
                    pygame.image.load(real_path),
                    (self.tile_size, self.tile_size),
                ),
                color,
            )

            if piece_type % 2 == 0:
                image.add_image(name, surface)
            else:
                image.add_image_and_mask(
                    name, surface, f"piece_{piece_type-1}"
                )

            outline_color = YELLOW
            outline_ident = outline.precalculate_outline(name, outline_color)
            image.add_image(f"{name}_outlined", outline_ident)

    def get_tile_location(self, position: Pos) -> Vector2:
        """Return the center point of a given tile position"""
        location = Vector2.from_iter(position) * self.tile_size
        center = self.tile_size // 2
        return location + (center, center) + self.rect.topleft  # noqa: RUF005

    def add_piece(
        self,
        piece_type: int,
        position: Pos,
        location: Pos | Vector2 | None = None,
    ) -> str:
        """Add piece given type and position"""
        group = self.groups()[-1]
        # Get the proper name of the tile we're creating ('A1' to 'H8')
        name = self.get_tile_name(*position)

        if location is None:
            location = self.get_tile_location(position)

        piece = Piece(
            piece_type=piece_type,
            position=position,
            position_name=name,
            location=location,
        )
        self.add_component(piece)
        group.add(piece)  # type: ignore[arg-type]

        self.pieces[position] = piece_type
        return piece.name

    def add_tile(self, position: Pos) -> str:
        """Add outlined tile given position"""
        group = self.groups()[-1]
        # Get the proper name of the tile we're creating ('A1' to 'H8')
        x, y = position
        name = self.get_tile_name(x, y)
        color = (x + y) % len(self.tile_color_map)

        tile = Tile(color, position, name, self.get_tile_location(position))
        self.add_component(tile)
        group.add(tile)  # type: ignore[arg-type]

        return tile.name

    def generate_board_image(self) -> Surface:
        """Generate an image of a game board"""
        image: sprite.ImageComponent = self.get_component("image")

        board_width, board_height = self.board_size

        # Get a surface the size of everything
        surf = pygame.Surface([x * self.tile_size for x in self.board_size])

        # Fill it with green so we know if anything is broken
        surf.fill(GREEN)

        # For each tile xy choordinate,
        loc_y = 0
        for y in range(board_height):
            loc_x = 0
            for x in range(board_width):
                color = (x + y) % len(self.tile_color_map)
                # Blit the tile image to the surface at the tile's location
                surf.blit(image.get_image(f"tile_{color}"), (loc_x, loc_y))
                ### Blit the id of the tile at the tile's location
                ##surf.blit(
                ##    render_text(
                ##        trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"),
                ##        20,
                ##        "".join(map(str, (x, y))),
                ##        GREEN
                ##    ),
                ##    (loc_x, loc_y)
                ##)
                loc_x += self.tile_size
            # Increment the y counter by tile_size
            loc_y += self.tile_size
        return surf


class ClickDestinationComponent(Component):
    "Component that will use targeting to go to wherever you click on the screen"
    __slots__ = ("selected",)
    outline = pygame.color.Color(255, 220, 0)

    def __init__(self) -> None:
        super().__init__("click_dest")

        self.selected = False

    def bind_handlers(self) -> None:
        "Register PygameMouseButtonDown and tick handlers"
        self.register_handlers(
            {
                "click": self.click,
                "drag": self.drag,
                "PygameMouseButtonDown": self.mouse_down,
                "tick": self.move_towards_dest,
                "init": self.cache_outline,
                "test": self.test,
            }
        )

    async def test(self, event: Event[Any]) -> None:
        print(f"{event = }")

    async def cache_outline(self, _: Event[Any]) -> None:
        "Precalculate outlined images"
        image: sprite.ImageComponent = self.get_component("image")
        outline: sprite.OutlineComponent = image.get_component("outline")
        outline.precalculate_all_outlined(self.outline)

    async def update_selected(self) -> None:
        "Update selected"
        image: sprite.ImageComponent = self.get_component("image")
        outline: sprite.OutlineComponent = image.get_component("outline")

        color = (None, self.outline)[int(self.selected)]
        outline.set_color(color)

        if not self.selected:
            movement: sprite.MovementComponent = self.get_component("movement")
            movement.speed = 0

    async def click(self, event: Event[dict[str, int]]) -> None:
        "Toggle selected"
        if event.data["button"] == 1:
            self.selected = not self.selected

            await self.update_selected()

    async def drag(self, event: Event[Any]) -> None:
        "Drag sprite"
        if not self.selected:
            self.selected = True
            await self.update_selected()
        movement: sprite.MovementComponent = self.get_component("movement")
        movement.speed = 0

    async def mouse_down(self, event: Event[dict[str, int | Pos]]) -> None:
        "Target click pos if selected"
        if not self.selected:
            return
        if event.data["button"] == 1:
            movement: sprite.MovementComponent = self.get_component("movement")
            movement.speed = 200
            target: sprite.TargetingComponent = self.get_component("targeting")
            assert isinstance(event.data["pos"], tuple)
            target.destination = Vector2.from_iter(event.data["pos"])

    async def move_towards_dest(self, event: Event[dict[str, float]]) -> None:
        "Move closer to destination"
        target: sprite.TargetingComponent = self.get_component("targeting")
        await target.move_destination_time(event.data["time_passed"])


class MrFloppy(sprite.Sprite):
    "Mr. Floppy test sprite"
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("MrFloppy")

        self.add_components(
            (
                sprite.MovementComponent(),
                sprite.TargetingComponent(),
                ClickDestinationComponent(),
                sprite.ImageComponent(),
                sprite.DragClickEventComponent(),
            )
        )

        movement = self.get_component("movement")
        targeting = self.get_component("targeting")
        image = self.get_component("image")

        movement.speed = 200

        floppy: pygame.surface.Surface = pygame.image.load(
            path.join(path.dirname(__file__), "data", "mr_floppy.png")
        )

        image.add_images(
            {
                0: floppy,
                # '1': pygame.transform.flip(floppy, False, True)
                1: pygame.transform.rotate(floppy, 270),
                2: pygame.transform.flip(floppy, True, True),
                3: pygame.transform.rotate(floppy, 90),
            }
        )

        self.update_location_on_resize = True

        anim = image.get_component("animation")
        anim.controller = self.controller(image.list_images())

        image.set_image(0)
        self.visible = True

        self.location = [x >> 1 for x in SCREEN_SIZE]
        targeting.destination = self.location

        self.register_handler("drag", self.drag)

    def controller(
        self, image_identifiers: list[str | int]
    ) -> Generator[str | int | None, None, None]:
        "Animation controller"
        cidx = 0
        while True:
            count = len(image_identifiers)
            if not count:
                yield None
                continue
            cidx = (cidx + 1) % count
            yield image_identifiers[cidx]

    async def drag(self, event: Event[dict[str, int | Pos]]) -> None:
        "Move by relative from drag"
        if event.data["button"] != 1:
            return
        sprite_component: sprite.Sprite = self.get_component("sprite")
        assert isinstance(event.data["rel"], tuple)
        sprite_component.location += event.data["rel"]
        sprite_component.dirty = 1


class FPSCounter(objects.Text):
    "FPS counter"
    __slots__ = ()

    def __init__(self) -> None:
        font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28
        )
        super().__init__("fps", font)

        self.location = Vector2.from_iter(self.image.get_size()) / 2 + (5, 5)

    async def on_tick(self, event: Event[dict[str, float]]) -> None:
        "Update text"
        # self.text = f'FPS: {event.data["fps"]:.2f}'
        self.text = f'FPS: {event.data["fps"]:.0f}'

    def bind_handlers(self) -> None:
        super().bind_handlers()
        self.register_handlers(
            {
                "tick": self.on_tick,
            }
        )


def generate_pieces(
    board_width: int, board_height: int, colors: int = 2
) -> dict[Pos, int]:
    """Generate data about each piece"""
    pieces: dict[Pos, int] = {}
    # Get where pieces should be placed
    z_to_1 = round(board_height / 3)  # White
    z_to_2 = (board_height - (z_to_1 * 2)) + z_to_1  # Black
    # For each xy position in the area of where tiles should be,
    for y in range(board_height):
        # Reset the x pos to 0
        for x in range(board_width):
            # Get the color of that spot by adding x and y mod the number of different colors
            color = (x + y) % colors
            # If a piece should be placed on that tile and the tile is not Red,
            if (not color) and ((y <= z_to_1 - 1) or (y >= z_to_2)):
                # Set the piece to White Pawn or Black Pawn depending on the current y pos
                piece_type = int(y <= z_to_1)
                pieces[(x, y)] = piece_type
    return pieces


class ServerClient(NetworkEventComponent):
    """Server Client Network Event Component.

    When clients connect to server, this class handles the incoming
    connections to the server in the way of reading and raising events
    that are transferred over the network."""

    __slots__ = ("client_id",)

    def __init__(self, client_id: int) -> None:
        self.client_id = client_id
        super().__init__(f"client_{client_id}")

        self.timeout = 3

        self.register_network_write_events(
            {
                "server[write]->no_actions": 0,
                "server[write]->create_piece": 1,
                "server[write]->select_piece": 2,
                "server[write]->create_tile": 3,
                "server[write]->delete_tile": 4,
                "server[write]->delete_piece_animation": 5,
                "server[write]->update_piece_animation": 6,
                "server[write]->move_piece_animation": 7,
                "server[write]->animation_state": 8,
                "server[write]->game_over": 9,
                "server[write]->action_complete": 10,
                "server[write]->initial_config": 11,
            }
        )
        self.register_read_network_events(
            {
                0: f"client[{self.client_id}]->select_piece",
                1: f"client[{self.client_id}]->select_tile",
            }
        )

    def bind_handlers(self) -> None:
        super().bind_handlers()
        self.register_handlers(
            {
                f"client[{self.client_id}]->select_piece": self.handle_raw_select_piece,
                f"client[{self.client_id}]->select_tile": self.handle_raw_select_tile,
                "create_piece->network": self.handle_create_piece,
                "select_piece->network": self.handle_piece_select,
                "create_tile->network": self.handle_create_tile,
                "delete_tile->network": self.handle_delete_tile,
                "delete_piece_animation->network": self.handle_delete_piece_animation,
                "update_piece_animation->network": self.handle_update_piece_animation,
                "move_piece_animation->network": self.handle_move_piece_animation,
                "animation_state->network": self.handle_animation_state,
                "game_over->network": self.handle_game_over,
                "action_complete->network": self.handle_action_complete,
                "initial_config->network": self.handle_initial_config,
            }
        )

    async def handle_raw_select_piece(self, event: Event[bytearray]) -> None:
        """Read raw select piece event and reraise as network->select_piece"""
        buffer = Buffer(event.data)

        pos_x, pos_y = read_position(buffer)

        await self.raise_event(
            Event("network->select_piece", (self.client_id, (pos_x, pos_y)))
        )

    async def handle_raw_select_tile(self, event: Event[bytearray]) -> None:
        """Read raw select tile event and reraise as network->select_tile"""
        buffer = Buffer(event.data)

        pos_x, pos_y = read_position(buffer)

        await self.raise_event(
            Event("network->select_tile", (self.client_id, (pos_x, pos_y)))
        )

    async def handle_create_piece(self, event: Event[tuple[Pos, int]]) -> None:
        """Read create piece event and reraise as server[write]->create_piece"""
        piece_pos, piece_type = event.data

        buffer = Buffer()

        write_position(buffer, piece_pos)
        buffer.write_value(StructFormat.UBYTE, piece_type)

        await self.write_event(Event("server[write]->create_piece", buffer))

    async def handle_piece_select(
        self, event: Event[tuple[Pos, bool]]
    ) -> None:
        """Read piece select event and reraise as server[write]->select_piece"""
        piece_pos, outline_value = event.data

        buffer = Buffer()

        write_position(buffer, piece_pos)
        buffer.write_value(StructFormat.BOOL, outline_value)

        await self.write_event(Event("server[write]->select_piece", buffer))

    async def handle_create_tile(self, event: Event[Pos]) -> None:
        """Read create tile event and reraise as server[write]->create_tile"""
        tile_pos = event.data

        buffer = Buffer()

        write_position(buffer, tile_pos)

        await self.write_event(Event("server[write]->create_tile", buffer))

    async def handle_delete_tile(self, event: Event[Pos]) -> None:
        """Read delete tile event and reraise as server[write]->delete_tile"""
        tile_pos = event.data

        buffer = Buffer()

        write_position(buffer, tile_pos)

        await self.write_event(Event("server[write]->delete_tile", buffer))

    async def handle_delete_piece_animation(self, event: Event[Pos]) -> None:
        """Read delete piece animation event and reraise as server[write]->delete_piece_animation"""
        piece_pos = event.data

        buffer = Buffer()

        write_position(buffer, piece_pos)

        await self.write_event(
            Event("server[write]->delete_piece_animation", buffer)
        )

    async def handle_update_piece_animation(
        self, event: Event[tuple[Pos, int]]
    ) -> None:
        """Read update piece animation event and reraise as server[write]->update_piece_animation"""
        piece_pos, piece_type = event.data

        buffer = Buffer()

        write_position(buffer, piece_pos)
        buffer.write_value(StructFormat.UBYTE, piece_type)

        await self.write_event(
            Event("server[write]->update_piece_animation", buffer)
        )

    async def handle_move_piece_animation(
        self, event: Event[tuple[Pos, Pos]]
    ) -> None:
        """Read move piece animation event and reraise as server[write]->move_piece_animation"""
        piece_current_pos, piece_new_pos = event.data

        buffer = Buffer()

        write_position(buffer, piece_current_pos)
        write_position(buffer, piece_new_pos)

        await self.write_event(
            Event("server[write]->move_piece_animation", buffer)
        )

    async def handle_animation_state(self, event: Event[bool]) -> None:
        """Read animation state change event and reraise as server[write]->animation_state"""
        state = event.data

        buffer = Buffer()

        buffer.write_value(StructFormat.BOOL, state)

        await self.write_event(Event("server[write]->animation_state", buffer))

    async def handle_game_over(self, event: Event[int]) -> None:
        """Read game over event and reraise as server[write]->game_over"""
        winner = event.data

        buffer = Buffer()

        buffer.write_value(StructFormat.UBYTE, winner)

        await self.write_event(Event("server[write]->game_over", buffer))

    async def handle_action_complete(
        self, event: Event[tuple[Pos, Pos, int]]
    ) -> None:
        """Read action complete event and reraise as server[write]->action_complete"""
        from_pos, to_pos, player_turn = event.data

        buffer = Buffer()

        write_position(buffer, from_pos)
        write_position(buffer, to_pos)
        buffer.write_value(StructFormat.UBYTE, player_turn)

        await self.write_event(Event("server[write]->action_complete", buffer))

    async def handle_initial_config(
        self, event: Event[tuple[Pos, int]]
    ) -> None:
        """Read initial config event and reraise as server[write]->initial_config"""
        board_size, player_turn = event.data

        buffer = Buffer()

        write_position(buffer, board_size)
        buffer.write_value(StructFormat.UBYTE, player_turn)

        await self.write_event(Event("server[write]->initial_config", buffer))


class CheckersState(State):
    """Subclass of State that keeps track of actions in `action_queue`"""

    __slots__ = ("action_queue",)

    def __init__(
        self,
        size: Pos,
        turn: bool,
        pieces: dict[Pos, int],
        /,
        pre_calculated_actions: dict[Pos, ActionSet] | None = None,
    ) -> None:
        super().__init__(size, turn, pieces, pre_calculated_actions)
        self.action_queue: deque[tuple[str, Iterable[Pos | int]]] = deque()

    def piece_kinged(self, piece_pos: Pos, new_type: int) -> None:
        super().piece_kinged(piece_pos, new_type)
        self.action_queue.append(("king", (piece_pos, new_type)))

    def piece_moved(self, start_pos: Pos, end_pos: Pos) -> None:
        super().piece_moved(start_pos, end_pos)
        self.action_queue.append(
            (
                "move",
                (
                    start_pos,
                    end_pos,
                ),
            )
        )

    def piece_jumped(self, jumped_piece_pos: Pos) -> None:
        super().piece_jumped(jumped_piece_pos)
        self.action_queue.append(("jump", (jumped_piece_pos,)))

    def get_action_queue(self) -> deque[tuple[str, Iterable[Pos | int]]]:
        """Return action queue"""
        return self.action_queue


class GameServer(Server):
    """Checkers server

    Handles accepting incoming connections from clients and handles
    main game logic via State subclass above."""

    __slots__ = (
        "client_count",
        "state",
        "client_players",
        "player_selections",
        "actions_queue",
        "players_can_interact",
        "internal_singleplayer_mode",
        "advertisement_scope",
    )

    board_size = (8, 8)
    max_clients = 4

    def __init__(self, internal_singleplayer_mode: bool = False) -> None:
        super().__init__("GameServer")

        self.client_count: int
        self.state: CheckersState = CheckersState(self.board_size, False, {})

        self.client_players: dict[int, int] = {}
        self.player_selections: dict[int, Pos] = {}
        self.players_can_interact: bool = False

        self.internal_singleplayer_mode = internal_singleplayer_mode
        self.advertisement_scope: trio.CancelScope | None = None

    def bind_handlers(self) -> None:
        """Register start_server and stop_server"""
        self.register_handlers(
            {
                "server_start": self.start_server,
                "network_stop": self.stop_server,
                "server_send_game_start": self.handle_server_start_new_game,
                "network->select_piece": self.handle_network_select_piece,
                "network->select_tile": self.handle_network_select_tile,
            }
        )

    async def stop_server(self, event: Event[None] | None = None) -> None:
        """Stop serving and disconnect all NetworkEventComponents"""
        self.stop_serving()
        self.stop_advertising()

        close_methods: deque[Callable[[], Awaitable[Any]]] = deque()
        for component in self.get_all_components():
            if isinstance(component, NetworkEventComponent):
                close_methods.append(component.close)
                self.remove_component(component.name)
        async with trio.open_nursery() as nursery:
            while close_methods:
                nursery.start_soon(close_methods.popleft())

    async def post_advertisement(
        self,
        udp_socket: trio._socket._SocketType,
        hosting_port: int,
    ) -> None:
        """Post server advertisement packet."""
        advertisement = (
            f"[AD]{hosting_port}[/AD][CHECKERS][/CHECKERS]"
        ).encode()
        await udp_socket.sendto(advertisement, ("224.0.2.60", 4445))
        ##        await udp_socket.sendto(advertisement, ("255.255.255.255", 4445))
        print("click")

    def stop_advertising(self) -> None:
        """Cancel self.advertisement_scope"""
        if self.advertisement_scope is None:
            return
        self.advertisement_scope.cancel()

    async def post_advertisements(self, hosting_port: int) -> None:
        """Post lan UDP packets so server can be found."""
        self.stop_advertising()
        self.advertisement_scope = trio.CancelScope()
        with trio.socket.socket(
            family=trio.socket.AF_INET,  # IPv4
            type=trio.socket.SOCK_DGRAM,  # UDP
            proto=trio.socket.IPPROTO_UDP,  # UDP
        ) as udp_socket:
            udp_socket.setsockopt(
                trio.socket.SOL_SOCKET, trio.socket.SO_BROADCAST, 1
            )
            # for all packets sent, after two hops on the network the packet will not
            # be re-sent/broadcast (see https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
            ##            udp_socket.setsockopt(
            ##                trio.socket.IPPROTO_IP,
            ##                trio.socket.IP_MULTICAST_TTL,
            ##                2,
            ##            )
            with self.advertisement_scope:
                while not self.can_start():
                    try:
                        await self.post_advertisement(udp_socket, hosting_port)
                        await read_advertisements()
                    except OSError as exc:
                        traceback.print_exception(exc)
                        print(
                            f"{self.__class__.__name__}: Failed to post server advertisement"
                        )
                        break
                    await trio.sleep(1.5)

    def setup_teams_internal(self, client_ids: list[int]) -> dict[int, int]:
        """Setup teams for internal server mode from sorted client ids."""
        players: dict[int, int] = {}
        for idx, client_id in enumerate(client_ids):
            if idx == 0:
                players[client_id] = 2
            else:
                players[client_id] = -1
        return players

    def setup_teams(self, client_ids: list[int]) -> dict[int, int]:
        """Setup teams from sorted client ids."""
        players: dict[int, int] = {}
        for idx, client_id in enumerate(client_ids):
            if idx < 2:
                players[client_id] = idx % 2
            else:
                players[client_id] = -1
        return players

    def new_game_init(self, turn: bool) -> None:
        """Start new game."""
        self.client_players.clear()
        self.player_selections.clear()

        pieces = generate_pieces(*self.board_size)
        self.state = CheckersState(self.board_size, turn, pieces)

        # Why keep track of another object just to know client ID numbers
        # if we already have that with the components? No need!
        client_ids: set[int] = set()
        for component in self.get_all_components():
            if isinstance(component, ServerClient):
                client_ids.add(component.client_id)

        sorted_client_ids = sorted(client_ids)
        if self.internal_singleplayer_mode:
            self.client_players = self.setup_teams_internal(sorted_client_ids)
        else:
            self.client_players = self.setup_teams(sorted_client_ids)

        self.players_can_interact = True

    async def start_server(self, event: Event[None] | None = None) -> None:
        """Serve clients"""
        print(f"{self.__class__.__name__}: Closing old server clients")
        await self.stop_server()
        print(f"{self.__class__.__name__}: Starting Server")
        self.client_count = 0
        port = PORT
        async with trio.open_nursery() as nursery:
            nursery.start_soon(partial(self.serve, port, backlog=0))
            # Do not post advertisements when using internal singleplayer mode
            if not self.internal_singleplayer_mode:
                nursery.start_soon(self.post_advertisements, port)

    async def handle_server_start_new_game(self, event: Event[None]) -> None:
        """Handle game start."""
        # Delete all pieces from last state (shouldn't be needed but still.)
        async with trio.open_nursery() as nursery:
            for piece_pos, _piece_type in self.state.get_pieces():
                nursery.start_soon(
                    self.raise_event,
                    Event("delete_piece->network", piece_pos),
                )

        # Choose which team plays first
        # Using non-cryptographically secure random because it doesn't matter
        self.new_game_init(bool(random.randint(0, 1)))  # noqa: S311

        # Send create_piece events for all pieces
        async with trio.open_nursery() as nursery:
            for piece_pos, piece_type in self.state.get_pieces():
                nursery.start_soon(
                    self.raise_event,
                    Event("create_piece->network", (piece_pos, piece_type)),
                )

        # Raise initial config event with board size and initial turn.
        await self.raise_event(
            Event(
                "initial_config->network", (self.board_size, self.state.turn)
            )
        )

    async def client_network_loop(self, client: ServerClient) -> None:
        """Network loop for given ServerClient."""
        while True:
            try:
                # print(f"{client.name} client_network_loop tick")
                try:
                    await client.write_event(
                        Event("server[write]->no_actions", bytearray())
                    )
                except (
                    trio.BrokenResourceError,
                    trio.ClosedResourceError,
                    RuntimeError,
                ):
                    break
                except Exception as exc:
                    traceback.print_exception(exc)
                    break
                try:
                    event = await client.read_event()
                except TimeoutException:
                    continue
                else:
                    await client.raise_event(event)
                # traceback.print_exception(exception)
            except (trio.ClosedResourceError, trio.BrokenResourceError):
                break

    def can_start(self) -> bool:
        """Return if game can start."""
        if self.internal_singleplayer_mode:
            return self.client_count >= 1
        return self.client_count >= 2

    def game_active(self) -> bool:
        """Return if game is active."""
        return self.state.check_for_win() is None

    async def handler(self, stream: trio.SocketStream) -> None:
        """Accept clients"""
        print(f"{self.__class__.__name__}: client connected")
        new_client_id = self.client_count
        self.client_count += 1

        can_start = self.can_start()
        if can_start:
            self.stop_serving()
        if self.client_count > self.max_clients:
            await stream.aclose()

        client = ServerClient.from_stream(new_client_id, stream=stream)
        self.add_component(client)

        if can_start:
            await self.raise_event(Event("server_send_game_start", None))

        try:
            await self.client_network_loop(client)
        finally:
            await client.close()
            if self.component_exists(client.name):
                self.remove_component(client.name)
            print(f"{self.__class__.__name__}: client disconnected")
            self.client_count -= 1

    async def handle_network_select_piece(
        self, event: Event[tuple[int, Pos]]
    ) -> None:
        """Handle piece event from client."""
        client_id, tile_pos = event.data

        player = self.client_players.get(client_id, -1)
        if player == 2:
            player = int(self.state.turn)

        if player != self.state.turn:
            print(
                f"{player = } cannot select piece {tile_pos = } because it is not that player's turn"
            )
            return

        if not self.players_can_interact:
            print(
                f"{player = } cannot select piece {tile_pos = } because players_can_interact is False"
            )
            return
        if not self.state.can_player_select_piece(player, tile_pos):
            print(f"{player = } cannot select piece {tile_pos = }")
            await self.player_select_piece(player, None)
            return
        if tile_pos == self.player_selections.get(player):
            # print(f"{player = } toggle select -> No select")
            await self.player_select_piece(player, None)
            return

        await self.player_select_piece(player, tile_pos)

    async def player_select_piece(
        self, player: int, piece_pos: Pos | None
    ) -> None:
        """Update glowing tiles from new selected piece"""
        ignore: set[Pos] = set()

        if piece_pos is not None:
            # Calculate actions if required
            new_action_set = self.state.get_actions_set(piece_pos)
            ignore = new_action_set.ends

        ignored: set[Pos] = set()

        # Remove outlined tiles from previous selection if existed
        if prev_selection := self.player_selections.get(player):
            action_set = self.state.get_actions_set(prev_selection)
            ignored = action_set.ends & ignore
            remove = action_set.ends - ignore
            async with trio.open_nursery() as nursery:
                for tile_position in remove:
                    nursery.start_soon(
                        self.raise_event,
                        Event("delete_tile->network", tile_position),
                    )
                if piece_pos != prev_selection:
                    nursery.start_soon(
                        self.raise_event,
                        Event(
                            "select_piece->network", (prev_selection, False)
                        ),
                    )

        if piece_pos is None:
            if prev_selection:
                del self.player_selections[player]
            return

        self.player_selections[player] = piece_pos

        # For each end point
        async with trio.open_nursery() as nursery:
            for tile_position in new_action_set.ends - ignored:
                nursery.start_soon(
                    self.raise_event,
                    Event("create_tile->network", tile_position),
                )
            # Sent select piece as well
            nursery.start_soon(
                self.raise_event,
                Event(
                    "select_piece->network",
                    (self.player_selections[player], True),
                ),
            )

    async def handle_move_animation(self, from_pos: Pos, to_pos: Pos) -> None:
        """Handle move animation."""
        await self.raise_event(
            Event("move_piece_animation->network", (from_pos, to_pos))
        )

    async def handle_jump_animation(self, jumped_pos: Pos) -> None:
        """Handle jump animation."""
        await self.raise_event(
            Event("delete_piece_animation->network", jumped_pos)
        )

    async def handle_king_animation(
        self, kinged_pos: Pos, piece_type: int
    ) -> None:
        """Handle jump animation."""
        await self.raise_event(
            Event("update_piece_animation->network", (kinged_pos, piece_type))
        )

    async def handle_action_animations(
        self, actions: deque[tuple[str, Iterable[Pos | int]]]
    ) -> None:
        """Handle action animations"""
        while actions:
            name, params = actions.popleft()
            if name == "move":
                await self.handle_move_animation(
                    *cast("Iterable[Pos]", params)
                )
            elif name == "jump":
                await self.handle_jump_animation(
                    *cast("Iterable[Pos]", params)
                )
            elif name == "king":
                await self.handle_king_animation(
                    *cast("tuple[Pos, int]", params)
                )
            else:
                raise NotImplementedError(f"Animation for action {name}")

    async def handle_network_select_tile(
        self, event: Event[tuple[int, Pos]]
    ) -> None:
        """Handle select tile event from network."""
        client_id, tile_pos = event.data

        player = self.client_players.get(client_id, -1)
        if player == 2:
            player = int(self.state.turn)

        if not self.players_can_interact:
            print(
                f"{player = } cannot select tile {tile_pos = } because players_can_interact is False"
            )
            return

        if player != self.state.turn:
            print(
                f"{player = } cannot select tile {tile_pos = } because it is not their turn."
            )
            return

        piece_pos = self.player_selections.get(player)
        if piece_pos is None:
            print(
                f"{player = } cannot select tile {tile_pos = } because has no selection"
            )
            return

        if tile_pos not in self.state.get_actions_set(piece_pos).ends:
            print(
                f"{player = } cannot select tile {piece_pos!r} because not valid move"
            )
            return

        self.players_can_interact = False  # No one moves during animation
        # Send animation state start event
        await self.raise_event(Event("animation_state->network", True))

        # Remove tile sprites and glowing effect
        await self.player_select_piece(player, None)

        action = self.state.action_from_points(piece_pos, tile_pos)
        # print(f"{action = }")
        # print(f'{self.state.turn = }')

        # Get new state after performing valid action
        new_state = self.state.preform_action(action)
        # Get action queue from old state
        action_queue = self.state.get_action_queue()
        self.state = new_state

        # Send action animations
        await self.handle_action_animations(action_queue)

        # Send action complete event
        await self.raise_event(
            Event(
                "action_complete->network",
                (piece_pos, tile_pos, self.state.turn),
            )
        )

        win_value = self.state.check_for_win()
        if win_value is not None:
            # If we have a winner, send game over event.
            await self.raise_event(Event("game_over->network", win_value))
            return

        # If not game over, allow interactions so next player can take turn
        self.players_can_interact = True
        await self.raise_event(Event("animation_state->network", False))

    def __del__(self) -> None:
        print(f"del {self.__class__.__name__}")
        super().__del__()


# Stolen from WOOF (Web Offer One File), Copyright (C) 2004-2009 Simon Budig,
# available at http://www.home.unix-ag.org/simon/woof
# with modifications

# Utility function to guess the IP (as a string) where the server can be
# reached from the outside. Quite nasty problem actually.


async def find_ip() -> str:
    """Guess the IP where the server can be found from the network."""
    # we get a UDP-socket for the TEST-networks reserved by IANA.
    # It is highly unlikely, that there is special routing used
    # for these networks, hence the socket later should give us
    # the IP address of the default route.
    # We're doing multiple tests, to guard against the computer being
    # part of a test installation.

    candidates: list[str] = []
    for test_ip in ("192.0.2.0", "198.51.100.0", "203.0.113.0"):
        sock = trio.socket.socket(trio.socket.AF_INET, trio.socket.SOCK_DGRAM)
        await sock.connect((test_ip, 80))
        ip_addr: str = sock.getsockname()[0]
        sock.close()
        if ip_addr in candidates:
            return ip_addr
        candidates.append(ip_addr)

    return candidates[0]


async def read_advertisements(
    network_adapter: str | None = None, timeout: int = 3
) -> list[tuple[str, str, int]]:
    """Read server advertisements from network."""
    if network_adapter is None:
        network_adapter = await find_ip()
    with trio.socket.socket(
        family=trio.socket.AF_INET,  # IPv4
        type=trio.socket.SOCK_DGRAM,  # UDP
        proto=trio.socket.IPPROTO_UDP,
    ) as udp_socket:
        # SO_REUSEADDR: allows binding to port potentially already in use
        udp_socket.setsockopt(
            trio.socket.SOL_SOCKET, trio.socket.SO_REUSEADDR, 1
        )

        ##        udp_socket.setsockopt(
        ##            trio.socket.IPPROTO_IP, trio.socket.IP_MULTICAST_TTL, 32
        ##        )
        ##        udp_socket.setsockopt(
        ##            trio.socket.IPPROTO_IP, trio.socket.IP_MULTICAST_LOOP,
        ##            1
        ##        )
        # linux binds to multicast address, windows to interface address
        ##        ip_bind = network_adapter if IS_WINDOWS else "224.0.2.60"
        ip_bind = ""
        await udp_socket.bind((ip_bind, 4445))

        ##        # Tell the kernel that we are a multicast socket
        ##        udp_socket.setsockopt(trio.socket.IPPROTO_IP, trio.socket.IP_MULTICAST_TTL, 255)

        # socket.IPPROTO_IP works on Linux and Windows
        ##        # IP_MULTICAST_IF: force sending network traffic over specific network adapter
        # IP_ADD_MEMBERSHIP: join multicast group
        ##        udp_socket.setsockopt(
        ##            trio.socket.IPPROTO_IP, trio.socket.IP_MULTICAST_IF,
        ##            trio.socket.inet_aton(network_adapter)
        ##        )
        udp_socket.setsockopt(
            trio.socket.IPPROTO_IP,
            trio.socket.IP_ADD_MEMBERSHIP,
            struct.pack(
                "4s4s",
                trio.socket.inet_aton("224.0.2.60"),
                trio.socket.inet_aton(network_adapter),
            ),
        )

        buffer = b""
        address = ""
        with trio.move_on_after(timeout):
            buffer, address = await udp_socket.recvfrom(32)
            print(f"{buffer = }")
            print(f"{address = }")

        response: list[tuple[str, str, int]] = []

        start = 0
        while True:
            ad_start = buffer.find(b"[AD]", start)
            if ad_start == -1:
                break
            ad_end = buffer.find(b"[AD]", ad_start)
            if ad_end == -1:
                break
            start_block = buffer.find(b"[CHECKERS]", ad_end)
            if start_block == -1:
                break
            start_end = buffer.find(b"[/CHECKERS]", start_block)
            if start_end == -1:
                break

            start = ad_end
            response.append(
                (
                    buffer[start_block + 10 : start_end].decode("utf-8"),
                    address,
                    buffer[ad_start + 4 : ad_end].decode("utf-8"),
                )
            )
        return response


class HaltState(AsyncState["CheckersClient"]):
    "Halt state to set state to None so running becomes False"
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("Halt")

    async def check_conditions(self) -> None:
        "Set active state to None."
        assert self.machine is not None
        await self.machine.set_state(None)


class GameState(AsyncState["CheckersClient"]):
    "Checkers Game Asynchronous State base class"
    __slots__ = ("id", "manager")

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.id: int = 0
        self.manager = ComponentManager(self.name)

    def add_actions(self) -> None:
        """Add internal component manager to statemachine's component manager."""
        assert self.machine is not None
        self.machine.manager.add_component(self.manager)

    def group_add(self, new_sprite: sprite.Sprite) -> None:
        """Add new sprite to statemachine's group."""
        assert self.machine is not None
        group = self.machine.get_group(self.id)
        assert group is not None, "Expected group from new group id"
        group.add(new_sprite)
        self.manager.add_component(new_sprite)

    async def exit_actions(self) -> None:
        """Remove group and unbind all components."""
        assert self.machine is not None
        self.machine.remove_group(self.id)
        self.manager.unbind_components()

    def change_state(
        self, new_state: str | None
    ) -> Callable[[Event[Any]], Awaitable[None]]:
        """Return an async function that will change state to `new_state`"""

        async def set_state(*args: object, **kwargs: object) -> None:
            if self.machine is None:
                return
            await self.machine.set_state(new_state)

        return set_state


class InitializeState(AsyncState["CheckersClient"]):
    "Initialize Checkers"
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("initialize")

    async def check_conditions(self) -> str:
        return "title"


class TestState(GameState):
    "Test state"
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("test")

    async def entry_actions(self) -> None:
        assert self.machine is not None
        self.id = self.machine.new_group("test")

        floppy = MrFloppy()
        self.group_add(floppy)
        self.group_add(FPSCounter())

        await self.machine.raise_event(Event("init", None))


class TitleState(GameState):
    "Game Title State"
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("title")

    async def entry_actions(self) -> None:
        """Add buttons."""
        assert self.machine is not None
        self.id = self.machine.new_group("title")

        button_font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28
        )
        title_font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 56
        )

        title_text = OutlinedText("title_text", title_font)
        title_text.visible = True
        title_text.color = Color(0, 0, 0)
        title_text.outline = (255, 0, 0)
        title_text.border_width = 4
        title_text.text = "CHECKERS"
        title_text.location = (SCREEN_SIZE[0] // 2, title_text.rect.h)
        self.group_add(title_text)

        hosting_button = Button("hosting_button", button_font)
        hosting_button.visible = True
        hosting_button.color = Color(0, 0, 0)
        hosting_button.text = "Host Networked Game"
        hosting_button.location = [x // 2 for x in SCREEN_SIZE]
        hosting_button.handle_click = self.change_state("play_hosting")
        self.group_add(hosting_button)

        join_button = Button("join_button", button_font)
        join_button.visible = True
        join_button.color = Color(0, 0, 0)
        join_button.text = "Join Networked Game"
        join_button.location = hosting_button.location + (  # noqa: RUF005
            0,
            hosting_button.rect.h + 10,
        )
        join_button.handle_click = self.change_state("play_joining")
        self.group_add(join_button)

        internal_button = Button("internal_hosting", button_font)
        internal_button.visible = True
        internal_button.color = Color(0, 0, 0)
        internal_button.text = "Singleplayer Game"
        internal_button.location = hosting_button.location - (
            0,
            hosting_button.rect.h + 10,
        )
        internal_button.handle_click = self.change_state(
            "play_internal_hosting"
        )
        self.group_add(internal_button)

        await self.machine.raise_event(Event("init", None))


##    async def check_conditions(self) -> str:
##        return "play_hosting"  # "play_hosting" # "play_joining"


class PlayHostingState(AsyncState["CheckersClient"]):
    "Start running server"
    __slots__ = ()

    internal_server = False

    def __init__(self) -> None:
        extra = "_internal" if self.internal_server else ""
        super().__init__(f"play{extra}_hosting")

    async def entry_actions(self) -> None:
        "Start hosting server"
        assert self.machine is not None
        self.machine.manager.add_component(GameServer(self.internal_server))

        await self.machine.raise_event(Event("server_start", None))
        await trio.sleep(0.1)  # Wait for server to start

    async def check_conditions(self) -> str:
        return "play_joining"


class PlayInternalHostingState(PlayHostingState):
    "Host server with internal server mode"
    __slots__ = ()

    internal_server = True


class PlayJoiningState(AsyncState["CheckersClient"]):
    "Start running client"
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("play_joining")

    def add_actions(self) -> None:
        "Add server component"
        assert self.machine is not None
        client = GameClient("network")

        self.machine.manager.add_component(client)

    async def exit_actions(self) -> None:
        "Have client connect"
        assert self.machine is not None
        await self.machine.raise_event(
            Event("client_connect", ("127.0.0.1", PORT))
        )
        await super().exit_actions()

    async def check_conditions(self) -> str:
        return "play"


class PlayState(GameState):
    "Game Play State"
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("play")

    def add_actions(self) -> None:
        super().add_actions()
        self.manager.register_handlers(
            {
                "client_disconnected": self.handle_client_disconnected,
                "game_winner": self.handle_game_over,
            }
        )

    async def entry_actions(self) -> None:
        assert self.machine is not None
        self.id = self.machine.new_group("play")

        # self.group_add(())
        gameboard = GameBoard(
            (8, 8),
            45,
        )
        gameboard.location = [x // 2 for x in SCREEN_SIZE]
        self.group_add(gameboard)

        await self.machine.raise_event(Event("init", None))

    async def exit_actions(self) -> None:
        assert self.machine is not None
        # Fire server stop event so server shuts down if it exists
        await self.machine.raise_event(Event("network_stop", None))

        if self.machine.manager.component_exists("network"):
            self.machine.manager.remove_component("network")
        if self.machine.manager.component_exists("GameServer"):
            self.machine.manager.remove_component("GameServer")

        # Unbind components and remove group
        await super().exit_actions()

    async def handle_game_over(self, event: Event[int]) -> None:
        """Handle game over event."""
        winner = event.data
        # print(f"Player {PLAYERS[winner]} ({winner}) Won")

        font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28
        )

        continue_button = Button("continue_button", font)
        continue_button.visible = True
        continue_button.color = Color(0, 0, 0)
        continue_button.text = f"{PLAYERS[winner]} Won - Return to Title"
        continue_button.location = [x // 2 for x in SCREEN_SIZE]
        continue_button.handle_click = self.change_state("title")
        self.group_add(continue_button)

        # Fire server stop event so server shuts down if it exists
        assert self.machine is not None
        await self.machine.raise_event(Event("network_stop", None))

    async def handle_client_disconnected(self, event: Event[str]) -> None:
        """Handle client disconnected error."""
        print("handle_client_disconnected")
        error = event.data

        font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28
        )

        title_button = Button("title_button", font)
        title_button.visible = True
        title_button.color = Color(0, 0, 0)
        title_button.text = "Client Disconnected - Return to Title"
        title_button.location = [x // 2 for x in SCREEN_SIZE]
        title_button.handle_click = self.change_state("title")
        self.group_add(title_button)

        error_text = OutlinedText("error_text", font)
        error_text.visible = True
        error_text.color = Color(255, 0, 0)
        error_text.border_width = 1
        error_text.text = error
        error_text.location = title_button.location + (  # noqa: RUF005
            0,
            title_button.rect.h + 10,
        )

        self.group_add(error_text)

        # Fire server stop event so server shuts down if it exists
        assert self.machine is not None
        await self.machine.raise_event(Event("network_stop", None))


class CheckersClient(sprite.GroupProcessor):
    """Checkers Game Client"""

    __slots__ = ("manager",)

    def __init__(self, manager: ComponentManager) -> None:
        super().__init__()
        self.manager = manager

        self.add_states(
            (
                HaltState(),
                InitializeState(),
                TitleState(),
                PlayHostingState(),
                PlayInternalHostingState(),
                PlayJoiningState(),
                PlayState(),
            )
        )

    @property
    def running(self) -> bool:
        "Boolean of if state machine is running."
        return self.active_state is not None

    async def raise_event(self, event: Event[Any]) -> None:
        "Raise component event in all groups"
        await self.manager.raise_event(event)


async def async_run() -> None:
    "Main loop of everything"
    # Set up globals
    global SCREEN_SIZE

    # Set up the screen
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 16, vsync=VSYNC)
    pygame.display.set_caption(f"{__title__} v{__version__}")
    pygame.key.set_repeat(1000, 30)
    screen.fill((0xFF, 0xFF, 0xFF))

    async with trio.open_nursery() as main_nursery:
        event_manager = ExternalRaiseManager(
            "checkers",
            main_nursery,  # "client"
        )
        client = CheckersClient(event_manager)

        background = pygame.image.load(
            path.join(path.dirname(__file__), "data", "background.png")
        ).convert()
        client.clear(screen, background)

        client.set_timing_threshold(1000 / FPS)

        await client.set_state("initialize")

        # clock = pygame.time.Clock()
        clock = Clock()

        while client.running:
            resized_window = False

            async with trio.open_nursery() as event_nursery:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        await client.set_state("Halt")
                    elif event.type == KEYUP and event.key == K_ESCAPE:
                        pygame.event.post(pygame.event.Event(QUIT))
                    elif event.type == WINDOWRESIZED:
                        SCREEN_SIZE = (event.x, event.y)
                        resized_window = True
                    sprite_event = sprite.convert_pygame_event(event)
                    # print(sprite_event)
                    event_nursery.start_soon(
                        event_manager.raise_event, sprite_event
                    )
                event_nursery.start_soon(client.think)
                event_nursery.start_soon(clock.tick, FPS)

            await client.raise_event(
                Event(
                    "tick",
                    sprite.TickEventData(
                        time_passed=clock.get_time() / 1000,
                        fps=clock.get_fps(),
                    ),
                )
            )

            if resized_window:
                screen.fill((0xFF, 0xFF, 0xFF))
                rects = [Rect((0, 0), SCREEN_SIZE)]
                client.repaint_rect(rects[0])
                rects.extend(client.draw(screen))
            else:
                rects = client.draw(screen)
            pygame.display.update(rects)
    client.clear_groups()


def run() -> None:
    "Run asynchronous side of everything"

    trio.run(async_run)


def cli_run() -> None:
    "Start game"
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")

    # If we're not imported as a module, run.
    # Make sure the game will display correctly on high DPI monitors on Windows.

    if IS_WINDOWS:
        from ctypes import windll  # type: ignore

        try:
            windll.user32.SetProcessDPIAware()
        except AttributeError:
            pass
        del windll

    try:
        pygame.init()
        run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    cli_run()
