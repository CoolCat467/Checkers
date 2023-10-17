#!/usr/bin/env python3
# Graphical Checkers Game with AI support
# Programmed by CoolCat467

# For AI Support, the python file has to have the text
# 'AI' in it somewhere, and has to have the '.py' extention.
# The game calls update(boardData) and tells the AI about
# the current state of the game board from gameboard.get_data(),
# turn() to get the target piece tile id and target destination
# tile id from the AI to make a move, and calls init() after the
# AI is imported for it to initalize anything.

# IMPORTANT NOTE:
# The updating and turn calls halt execution, including display
# updates. This would be fixed with multiprocessing, but I am not
# very familiar with it and it also might cause some dy-syncronization
# problems.

# Note: Tile Ids are chess board tile titles, A1 to H8
# A8 ... H8
# .........
# A1 ... H1

# from __future__ import annotations

import os
import random
import traceback
from collections import deque
from collections.abc import Awaitable, Callable, Generator, Iterable, Sequence
from os import path
from typing import Any, TypeVar

import base2d
import objects
import pygame
import sprite
import trio
from async_clock import Clock
from base_io import StructFormat
from buffer import Buffer
from component import Component, ComponentManager, Event, ExternalRaiseManager
from network import NetworkEventComponent, Server, TimeoutException
from objects import Button
from pygame.color import Color
from pygame.locals import K_ESCAPE, KEYUP, QUIT, WINDOWRESIZED
from pygame.rect import Rect
from pygame.surface import Surface
from state import ActionSet, State
from statemachine import AsyncState
from vector import Vector2

__title__ = "Checkers"
__version__ = "0.0.5"
__author__ = "CoolCat467"

SCREEN_SIZE = (640, 480)

FPS = 60
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

Pos = tuple[int, int]


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


# 0 = False = Red   = 0, 2
# 1 = True  = Black = 1, 3


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

        self.animation_queue: deque[Event] = deque()
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

    async def handle_animation_state(self, event: Event[bool]) -> None:
        """Handle animation_state event."""
        new_animating_state = event.data

        # Add important start/end block information as an event to the queue
        self.animation_queue.append(
            Event("animation_state", new_animating_state)
        )

        if new_animating_state:
            return

        # Stopping, end of animation block
        if not self.processing_animations:
            self.processing_animations = True
            await self.raise_event(Event("fire_next_animation", None))

    async def handle_fire_next_animation(self, _: Event[None] = None) -> None:
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

        # Generate a Pice Surface for each piece using a base image and a color
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
        location: Pos | None = None,
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
                ##        "VeraSerif.ttf",
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
            path.join("data", "mr_floppy.png")
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
        font = pygame.font.Font("data/VeraSerif.ttf", 28)
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


def read_position(buffer: Buffer) -> Pos:
    """Read a position tuple from buffer."""
    pos_x = buffer.read_value(StructFormat.UBYTE)
    pos_y = buffer.read_value(StructFormat.UBYTE)

    return pos_x, pos_y


def write_position(buffer: Buffer, pos: Pos) -> None:
    """Write a position tuple to buffer."""
    pos_x, pos_y = pos
    buffer.write_value(StructFormat.UBYTE, pos_x)
    buffer.write_value(StructFormat.UBYTE, pos_y)


class GameClient(NetworkEventComponent):
    """Game Client Network Event Component.

    This class handles connecting to the game server, transmitting events
    to the server, and reading and raising incoming events from the server."""

    __slots__ = ()

    def __init__(self, name: str) -> None:
        super().__init__(name)

        # Five seconds until timeout is generous, but it gives server end wiggle
        # room.
        self.timeout = 5

        self.register_network_write_events(
            {
                "select_piece->server": 0,
                "select_tile->server": 1,
            }
        )
        self.register_read_network_events(
            {
                0: "no_actions->client",
                1: "server->create_piece",
                2: "server->select_piece",
                3: "server->create_tile",
                4: "server->delete_tile",
                5: "server->delete_piece_animation",
                6: "server->update_piece_animation",
                7: "server->move_piece_animation",
                8: "server->animation_state",
                9: "server->game_over",
                10: "server->action_complete",
                11: "server->initial_config",
            }
        )

    def bind_handlers(self) -> None:
        super().bind_handlers()
        self.register_handlers(
            {
                # "no_actions->client": self.print_no_actions,
                "gameboard_piece_clicked": self.write_piece_click,
                "gameboard_tile_clicked": self.write_tile_click,
                "server->create_piece": self.read_create_piece,
                "server->select_piece": self.read_select_piece,
                "server->create_tile": self.read_create_tile,
                "server->delete_tile": self.read_delete_tile,
                "server->delete_piece_animation": self.read_delete_piece_animation,
                "server->update_piece_animation": self.read_update_piece_animation,
                "server->move_piece_animation": self.read_move_piece_animation,
                "server->animation_state": self.read_animation_state,
                "server->game_over": self.read_game_over,
                "server->action_complete": self.read_action_complete,
                "server->initial_config": self.read_initial_config,
                "network_stop": self.handle_network_stop,
                "client_connect": self.handle_client_connect,
                "tick": self.handle_tick,
            }
        )

    async def print_no_actions(self, event: Event[bytearray]) -> None:
        """Print recieved `no_actions` event from server.

        This event is used as a sort of keepalive heartbeat, because
        it stops the connection from timing out."""
        print(f"print_no_actions {event = }")

    async def handle_tick(self, event: Event[dict[str, float]]) -> None:
        """Raise events from server"""
        if self.not_connected:
            return
        success, exception = await self.raise_event_from_read_network()
        if success:
            return

        if isinstance(exception, trio.ClosedResourceError):
            return

        traceback.print_exception(exception)
        print(
            f"{self.__class__.__name__}: Failed to read event from network, stopping"
        )

        await self.raise_event(Event("network_stop", None))

    async def handle_client_connect(
        self, event: Event[tuple[str, int]]
    ) -> None:
        """Have client connect to address specified in event"""
        if not self.not_connected:
            return
        await self.connect(*event.data)

    async def read_create_piece(self, event: Event[bytearray]) -> None:
        """Read create_piece event from server"""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        piece_type = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("gameboard_create_piece", (piece_pos, piece_type))
        )

    async def read_select_piece(self, event: Event[bytearray]) -> None:
        """Read create_piece event from server"""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        outline_value = buffer.read_value(StructFormat.BOOL)

        await self.raise_event(
            Event("gameboard_select_piece", (piece_pos, outline_value))
        )

    async def read_create_tile(self, event: Event[bytearray]) -> None:
        """Read create_tile event from server"""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(Event("gameboard_create_tile", tile_pos))

    async def read_delete_tile(self, event: Event[bytearray]) -> None:
        """Read delete_tile event from server"""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(Event("gameboard_delete_tile", tile_pos))

    async def write_piece_click(self, event: Event[tuple[Pos, int]]) -> None:
        """Write piece click event to server"""
        if self.not_connected:
            return
        piece_position, piece_type = event.data

        buffer = Buffer()
        write_position(buffer, piece_position)
        buffer.write_value(StructFormat.UINT, piece_type)

        await self.write_event(Event("select_piece->server", buffer))

    async def write_tile_click(self, event: Event[Pos]) -> None:
        """Write tile click event to server"""
        tile_position = event.data

        buffer = Buffer()
        write_position(buffer, tile_position)

        await self.write_event(Event("select_tile->server", buffer))

    async def read_delete_piece_animation(
        self, event: Event[bytearray]
    ) -> None:
        """Read delete_piece_animation event from server"""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(
            Event("gameboard_delete_piece_animation", tile_pos)
        )

    async def read_update_piece_animation(
        self, event: Event[bytearray]
    ) -> None:
        """Read update_piece_animation event from server"""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        piece_type = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("gameboard_update_piece_animation", (piece_pos, piece_type))
        )

    async def read_move_piece_animation(self, event: Event[bytearray]) -> None:
        """Read move_piece_animation event from server"""
        buffer = Buffer(event.data)

        piece_current_pos = read_position(buffer)
        piece_new_pos = read_position(buffer)

        await self.raise_event(
            Event(
                "gameboard_move_piece_animation",
                (piece_current_pos, piece_new_pos),
            )
        )

    async def read_animation_state(self, event: Event[bytearray]) -> None:
        """Read animation_state event from server"""
        buffer = Buffer(event.data)

        animation_state = buffer.read_value(StructFormat.BOOL)

        await self.raise_event(
            Event("gameboard_animation_state", animation_state)
        )

    async def read_game_over(self, event: Event[bytearray]) -> None:
        """Read update_piece event from server"""
        buffer = Buffer(event.data)

        winner = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(Event("game_winner", winner))

    async def read_action_complete(self, event: Event[bytearray]) -> None:
        """Read action_complete event from server.

        Sent when last action from client is done, great for AIs.
        As of writing, not used for main client."""
        buffer = Buffer(event.data)

        from_pos = read_position(buffer)
        to_pos = read_position(buffer)
        current_turn = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("game_action_complete", (from_pos, to_pos, current_turn))
        )

    async def read_initial_config(self, event: Event[bytearray]) -> None:
        """Read initial_config event from server"""
        buffer = Buffer(event.data)

        board_size = read_position(buffer)
        current_turn = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("game_initial_config", (board_size, current_turn))
        )

    async def handle_network_stop(self, event: Event[None]) -> None:
        """Send EOF if connected and close socket."""
        if self.not_connected:
            return
        else:
            await self.send_eof()
        await self.close()


class ServerClient(NetworkEventComponent):
    """Server Client Network Event Component.

    When clients connect to server, this class handles the incoming
    connections to the server in the way of reading and raising events
    that are transfered over the network."""

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
        self, event: Event[tuple[Pos, Pos, int]]
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
    )

    board_size = (8, 8)

    def __init__(self) -> None:
        super().__init__("gameserver")

        self.client_count: int
        self.state: CheckersState = CheckersState(self.board_size, False, {})

        self.client_players: dict[int, int] = {}
        self.player_selections: dict[int, Pos] = {}
        self.players_can_interact: bool = False

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
        async with trio.open_nursery() as nursery:
            for component in self.get_all_components():
                if isinstance(component, NetworkEventComponent):
                    nursery.start_soon(component.close)
        for component in self.get_all_components():
            if isinstance(component, NetworkEventComponent):
                self.remove_component(component.name)

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

        self.client_players = self.setup_teams(sorted(client_ids))

        self.players_can_interact = True

    async def start_server(self, event: Event[None] | None = None) -> None:
        """Serve clients"""
        print(f"{self.__class__.__name__}: starting server")
        await self.stop_server()
        self.client_count = 0
        await self.serve(PORT, backlog=0)

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
                await client.write_event(
                    Event("server[write]->no_actions", bytearray())
                )
                (
                    success,
                    exception,
                ) = await client.raise_event_from_read_network()
                if isinstance(exception, TimeoutException):
                    continue
                if not success:
                    break
            except (trio.ClosedResourceError, trio.BrokenResourceError):
                break

    def can_start(self) -> bool:
        """Return if game can start."""
        return self.client_count >= 2

    async def handler(self, stream: trio.SocketStream) -> None:
        """Accept clients"""
        print(f"{self.__class__.__name__}: client connected")
        new_client_id = self.client_count
        self.client_count += 1
        if self.client_count >= 2:
            self.stop_serving()
        if self.client_count > 2:
            await stream.aclose()

        client = ServerClient.from_stream(new_client_id, stream=stream)
        self.add_component(client)

        if self.can_start():
            await self.raise_event(Event("server_send_game_start", None))

        try:
            await self.client_network_loop(client)
        finally:
            await client.close()
            self.remove_component(client.name)
            print(f"{self.__class__.__name__}: client disconnected")

    async def handle_network_select_piece(
        self, event: Event[tuple[int, Pos]]
    ) -> None:
        """Handle piece event from client."""
        client_id, tile_pos = event.data

        player = self.client_players[client_id]

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
        self, actions: deque[tuple[str, Iterable[Pos]]]
    ) -> None:
        """Handle action animations"""
        while actions:
            name, params = actions.popleft()
            if name == "move":
                await self.handle_move_animation(*params)
            elif name == "jump":
                await self.handle_jump_animation(*params)
            elif name == "king":
                await self.handle_king_animation(*params)
            else:
                raise NotImplementedError(f"Animation for action {name}")

    async def handle_network_select_tile(
        self, event: Event[tuple[int, Pos]]
    ) -> None:
        """Handle select tile event from network."""
        client_id, tile_pos = event.data

        player = self.client_players[client_id]

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

        # Get new state after preforming valid action
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

        await self.raise_event(Event("animation_state->network", False))

        win_value = self.state.check_for_win()
        if win_value is not None:
            # If we have a winner, send game over event.
            await self.raise_event(Event("game_over->network", win_value))
            return

        # If not game over, allow interactions so next player can take turn
        self.players_can_interact = True


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
    ) -> Callable[[], Awaitable[None]]:
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

        font = pygame.font.Font(trio.Path("data", "VeraSerif.ttf"), 28)

        hosting_button = Button("hosting_button", font)
        hosting_button.visible = True
        hosting_button.color = (0, 0, 0)
        hosting_button.text = "Host Checkers Game"
        hosting_button.location = [x // 2 for x in SCREEN_SIZE]
        hosting_button.handle_click = self.change_state("play_hosting")
        self.group_add(hosting_button)

        join_button = Button("join_button", font)
        join_button.visible = True
        join_button.color = (0, 0, 0)
        join_button.text = "Join Checkers Game"
        join_button.location = hosting_button.location + (  # noqa: RUF005
            0,
            hosting_button.rect.h + 10,
        )
        join_button.handle_click = self.change_state("play_joining")
        self.group_add(join_button)

        await self.machine.raise_event(Event("init", None))


##    async def check_conditions(self) -> str:
##        return "play_hosting"  # "play_hosting" # "play_joining"


class PlayHostingState(AsyncState["CheckersClient"]):
    "Start running server"
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("play_hosting")

    def add_actions(self) -> None:
        "Add server component"
        assert self.machine is not None
        self.machine.manager.add_component(GameServer())

    async def entry_actions(self) -> None:
        "Start hosting server"
        assert self.machine is not None
        await self.machine.raise_event(Event("server_start", None))
        await trio.sleep(0.1)  # Wait for server to start
        await self.machine.raise_event(
            Event("client_connect", ("127.0.0.1", PORT))
        )

    async def check_conditions(self) -> str:
        return "play"


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

    async def entry_actions(self) -> None:
        "Start hosting server"
        assert self.machine is not None
        await self.machine.raise_event(
            Event("client_connect", ("127.0.0.1", PORT))
        )

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
        # Unbind components and remove group
        await super().exit_actions()

    async def handle_game_over(self, event: Event[int]) -> None:
        """Handle game over event."""
        winner = event.data
        # print(f"Player {PLAYERS[winner]} ({winner}) Won")

        font = pygame.font.Font("data/VeraSerif.ttf", 28)

        continue_button = Button("continue_button", font)
        continue_button.visible = True
        continue_button.color = (0, 0, 0)
        continue_button.text = f"{PLAYERS[winner]} Won - Return to Title"
        continue_button.location = [x // 2 for x in SCREEN_SIZE]
        continue_button.handle_click = self.change_state("title")
        self.group_add(continue_button)

        # Fire server stop event so server shuts down if it exists
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
    ##    computer = play_ai()
    # Set up globals
    global SCREEN_SIZE
    ##    global IMAGES, PLAYERS, aiData, RUNNING

    # Set up the screen
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 16, vsync=VSYNC)
    pygame.display.set_caption(f"{__title__} v{__version__}")
    pygame.key.set_repeat(1000, 30)
    screen.fill((0xFF, 0xFF, 0xFF))

    async with trio.open_nursery() as main_nursery:
        event_manager = ExternalRaiseManager(
            "checkers", main_nursery, "client"
        )
        client = CheckersClient(event_manager)

        background = pygame.image.load(
            path.join("data", "background.png")
        ).convert()
        client.clear(screen, background)

        client.set_timing_threshold(1000 / FPS)

        await client.set_state("initialize")

        # clock = pygame.time.Clock()
        clock = Clock()

        ##
        ##    # Set up players
        ##    if computer:
        ##        PLAYERS = ["Player", "Computer"]
        ##        if aiData and hasattr(aiData, "keys"):
        ##            keys = aiData.keys()
        ##            if "player_names" in keys:
        ##                if len(aiData["player_names"]) == 2:
        ##                    PLAYERS = base2d.to_str(list(aiData["player_names"]))
        ##    else:
        ##        PLAYERS = ["Red Player", "Black Player"]
        ##
        ##    # Get the screen width and height for a lot of things
        ##    w, h = SCREEN_SIZE
        ##
        ##
        ##    if computer and isinstance(aiData, dict):
        ##        keys = aiData.keys()
        ##        if "starting_turn" in keys:
        ##            world.get_type("board")[0].playing = int(aiData["starting_turn"])
        ##        if "must_quit" in keys:
        ##            world.get_type("button")[0].do_reset = not bool(
        ##                aiData["must_quit"]
        ##            )
        ##
        ##    ai_has_been_told_game_is_won = False
        ##
        ##    # If we are playing against a computer,
        ##    if computer:
        ##        # If it's the AI's turn,
        ##        if board.playing == 0:
        ##            # Reset game is won tracker since presumabley a new game has started
        ##            if ai_has_been_told_game_is_won:
        ##                ai_has_been_told_game_is_won = False
        ##            try:
        ##                # Send board data to the AI
        ##                AI.update(board.get_data())
        ##                # Get the target piece id and destination piece id from the AI
        ##                rec_data = AI.turn()
        ##                if rec_data != "QUIT":
        ##                    if rec_data is not None:
        ##                        target, dest = rec_data
        ##                        # Play play the target piece id to the destination tile id
        ##                        # on the game board
        ##                        success = ai_play(
        ##                            str(target), str(dest), board
        ##                        )
        ##                        if hasattr(AI, "turn_success"):
        ##                            AI.turn_success(bool(success))
        ##                    # else:
        ##                    #     print('AI Played None. Still AI\'s Turn.')
        ##                else:
        ##                    # Don't use this as an excuse if your AI can't win
        ##                    print(
        ##                        "AI wishes to hault execution. Exiting game."
        ##                    )
        ##                    RUNNING = False
        ##            except Exception as ex:
        ##                traceback.print_exception(ex)
        ##                RUNNING = False
        ##        elif board.playing == 2 and not ai_has_been_told_game_is_won:
        ##            # If the game has been won, tell the AI about it
        ##            AI.update(board.get_data())
        ##            ai_has_been_told_game_is_won = True
        ##    # If we have an AI going and it has the stop function,
        ##    if computer and hasattr(AI, "stop"):
        ##        # Tell the AI to stop
        ##        AI.stop()
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


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")

    # If we're not imported as a module, run.
    # Make sure the game will display correctly on high DPI monitors on Windows.
    import platform

    if platform.system() == "Windows":
        from ctypes import windll  # type: ignore

        try:
            windll.user32.SetProcessDPIAware()
        except AttributeError:
            pass
        del windll
    del platform

    try:
        pygame.init()
        run()
    finally:
        pygame.quit()
