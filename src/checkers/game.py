#!/usr/bin/env python3
# Graphical Checkers Game

"Graphical Checkers Game."

# Programmed by CoolCat467

# Note: Tile Ids are chess board tile titles, A1 to H8
# A8 ... H8
# .........
# A1 ... H1

# 0 = False = Red   = 0, 2
# 1 = True  = Black = 1, 3

from __future__ import annotations

import contextlib
import os
import platform
from collections import deque
from os import path
from typing import TYPE_CHECKING, Any, Final, TypeAlias, TypeVar

import pygame
import trio
from pygame.color import Color
from pygame.locals import K_ESCAPE, KEYUP, QUIT, WINDOWRESIZED
from pygame.rect import Rect

from checkers import base2d, objects, sprite
from checkers.async_clock import Clock
from checkers.client import GameClient, read_advertisements
from checkers.component import (
    Component,
    ComponentManager,
    Event,
    ExternalRaiseManager,
)
from checkers.objects import Button, OutlinedText
from checkers.server import GameServer
from checkers.statemachine import AsyncState
from checkers.vector import Vector2

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
__version__ = "2.0.1"
__author__ = "CoolCat467"

SCREEN_SIZE = (640, 480)

FPS: Final = 48
VSYNC = True
PORT: Final = 31613

PLAYERS: Final = ["Red Player", "Black Player"]


BLACK: Final = (0, 0, 0)
BLUE: Final = (15, 15, 255)
GREEN: Final = (0, 255, 0)
CYAN: Final = (0, 255, 255)
RED: Final = (255, 0, 0)
MAGENTA: Final = (255, 0, 255)
YELLOW: Final = (255, 255, 0)
WHITE: Final = (255, 255, 255)


T = TypeVar("T")

IS_WINDOWS: Final = platform.system() == "Windows"

Pos: TypeAlias = tuple[int, int]


def render_text(
    font_name: str, font_size: int, text: str, color: tuple[int, int, int],
) -> Surface:
    "Render text with a given font at font_size with the text in the color of color."
    # Load the font at the size of font_size
    font = pygame.font.Font(font_name, font_size)
    # Using the loaded font, render the text in the color of color
    return font.render(text, False, color)


class Piece(sprite.Sprite):
    "Piece Sprite."

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
            ),
        )

    def bind_handlers(self) -> None:
        "Register handlers."
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
            },
        )

    def set_outlined(self, state: bool) -> None:
        "Update image given new outline state."
        manager_image: sprite.ImageComponent = self.manager.get_component(
            "image",
        )
        value = "_outlined" if state else ""
        self.image = manager_image.get_image(f"piece_{self.piece_type}{value}")

    async def handle_click_event(
        self, event: Event[dict[str, Pos | int]],
    ) -> None:
        "Raise gameboard_piece_clicked events when clicked."
        await self.raise_event(
            Event(
                "gameboard_piece_clicked",
                (
                    self.board_position,
                    self.piece_type,
                ),
                3,
            ),
        )

    async def handle_set_outline_event(self, event: Event[bool]) -> None:
        "Update outlined state."
        self.set_outlined(event.data)

    async def handle_self_destruct_event(self, event: Event[None]) -> None:
        "Remove self from play."
        self.kill()
        self.manager.remove_component(self.name)

    async def handle_tick_event(
        self, event: Event[sprite.TickEventData],
    ) -> None:
        "Move toward destination."
        time_passed = event.data.time_passed
        targeting: sprite.TargetingComponent = self.get_component("targeting")
        await targeting.move_destination_time(time_passed)

    async def handle_move_event(
        self, event: Event[Iterable[tuple[Pos, Pos, Pos]]],
    ) -> None:
        "Handle movement animation to event position."
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
        self, event: Event[None],
    ) -> None:
        "Raise gameboard_piece_moved event."
        _, start_pos, end_pos = self.destination_tiles.pop(0)

        if self.destination_tiles:
            targeting: sprite.TargetingComponent = self.get_component(
                "targeting",
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
            ),
        )

    async def handle_update_event(self, event: Event[int]) -> None:
        """Update self during movement animation."""
        self.piece_type = event.data
        self.set_outlined(False)
        # Inform board that animation is complete
        await self.raise_event(Event("fire_next_animation", None, 1))


class Tile(sprite.Sprite):
    "Outlined tile sprite - Only exists for selecting destination."

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
        "Register handlers."
        if not self.manager_exists:
            return
        self.set_outlined(True)

        self.visible = True

        self.register_handlers(
            {
                "click": self.handle_click_event,
                f"self_destruct_tile_{self.position_name}": self.handle_self_destruct_event,
            },
        )

    def set_outlined(self, state: bool) -> None:
        "Update image given new outline state."
        manager_image: sprite.ImageComponent = self.manager.get_component(
            "image",
        )
        value = "_outlined" if state else ""
        self.image = manager_image.get_image(f"tile_{self.color}{value}")

    async def handle_click_event(
        self, event: Event[dict[str, Pos | int]],
    ) -> None:
        "Raise gameboard_tile_clicked events when clicked."
        await self.raise_event(
            Event(
                "gameboard_tile_clicked",
                self.board_position,
                3,
            ),
        )

    async def handle_self_destruct_event(self, event: Event[None]) -> None:
        "Remove from all groups and remove self component."
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
    "Generate the image used for a tile."
    surf = pygame.Surface(size)
    surf.fill(color)
    return surf


class GameBoard(sprite.Sprite):
    "Entity that stores data about the game board and renders it."

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
        tile_size: int,
    ) -> None:
        super().__init__("board")

        self.add_component(sprite.ImageComponent())

        # Store the Board Size and Tile Size
        self.board_size: tuple[int, int]
        self.tile_size = tile_size

        self.update_location_on_resize = True

        self.pieces: dict[Pos, int] = {}

        self.animation_queue: deque[Event[object]] = deque()
        self.processing_animations = False

        self.generate_tile_images()

    def get_tile_name(self, x: int, y: int) -> str:
        """Get name of a given tile."""
        return f"{x}_{y}"  # chr(65 + x) + str(self.board_size[1] - y)

    def bind_handlers(self) -> None:
        "Register handlers."
        self.register_handlers(
            {
                "game_initial_config": self.handle_initial_config_event,
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
            },
        )

    async def handle_initial_config_event(
        self, event: Event[tuple[Pos, int]],
    ) -> None:
        "Start up game."
        self.board_size, _current_turn = event.data

        # Generate tile data
        self.image = self.generate_board_image()
        self.visible = True

    async def handle_select_piece_event(
        self, event: Event[tuple[Pos, bool]],
    ) -> None:
        """Send piece outline event."""
        piece_pos, outline_value = event.data
        piece_name = self.get_tile_name(*piece_pos)
        await self.raise_event(
            Event(f"piece_outline_{piece_name}", outline_value),
        )

    async def handle_piece_moved_event(
        self, event: Event[tuple[str, Pos, Pos, bool]],
    ) -> None:
        """Handle piece finishing one part of it's movement animation."""
        await self.raise_event(Event("fire_next_animation", None))

    async def handle_create_piece_event(
        self, event: Event[tuple[Pos, int]],
    ) -> None:
        """Handle create_piece event."""
        if not self.visible:
            # If not visible, reraise until board is set up right
            await self.raise_event(event)
            return
        piece_pos, piece_type = event.data
        self.add_piece(piece_type, piece_pos)

    async def handle_create_tile_event(self, event: Event[Pos]) -> None:
        """Handle create_tile event."""
        tile_pos = event.data
        self.add_tile(tile_pos)

    async def handle_delete_tile_event(self, event: Event[Pos]) -> None:
        """Handle delete_tile event."""
        tile_pos = event.data
        tile_name = self.get_tile_name(*tile_pos)
        await self.raise_event(Event(f"self_destruct_tile_{tile_name}", None))

    async def handle_delete_piece_animation_event(
        self, event: Event[Pos],
    ) -> None:
        """Handle delete_animation_piece event."""
        self.animation_queue.append(
            Event(event.name.removesuffix("_animation"), event.data),
        )

    async def handle_delete_piece_event(self, event: Event[Pos]) -> None:
        """Handle delete_piece event."""
        piece_pos = event.data
        piece_name = self.get_tile_name(*piece_pos)
        await self.raise_event(Event(f"destroy_piece_{piece_name}", None))
        self.pieces.pop(piece_pos)
        await self.raise_event(Event("fire_next_animation", None))

    async def handle_update_piece_animation_event(
        self, event: Event[tuple[Pos, int]],
    ) -> None:
        """Handle update_piece_animation event."""
        self.animation_queue.append(
            Event(event.name.removesuffix("_animation"), event.data),
        )

    async def handle_update_piece_event(
        self, event: Event[tuple[Pos, int]],
    ) -> None:
        """Handle update_piece event."""
        piece_pos, piece_type = event.data
        self.pieces[piece_pos] = piece_type
        piece_name = self.get_tile_name(*piece_pos)
        await self.raise_event(Event(f"piece_update_{piece_name}", piece_type))

    async def handle_move_piece_animation_event(
        self, event: Event[tuple[Pos, Pos]],
    ) -> None:
        """Handle move_piece_animation event."""
        self.animation_queue.append(
            Event(event.name.removesuffix("_animation"), event.data),
        )

    async def handle_move_piece_event(
        self, event: Event[tuple[Pos, Pos]],
    ) -> None:
        """Handle move_piece event."""
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
            ),
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
        self, _: Event[None] | None = None,
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
        """Load all the images."""
        image: sprite.ImageComponent = self.get_component("image")
        outline: sprite.OutlineComponent = image.get_component("outline")
        outline.size = 2

        base_folder = os.path.dirname(__file__)

        for index, color in enumerate(self.tile_color_map):
            name = f"tile_{index}"
            surface = generate_tile_image(
                color, (self.tile_size, self.tile_size),
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
                    name, surface, f"piece_{piece_type-1}",
                )

            outline_color = YELLOW
            outline_ident = outline.precalculate_outline(name, outline_color)
            image.add_image(f"{name}_outlined", outline_ident)

    def get_tile_location(self, position: Pos) -> Vector2:
        """Return the center point of a given tile position."""
        location = Vector2.from_iter(position) * self.tile_size
        center = self.tile_size // 2
        return location + (center, center) + self.rect.topleft  # noqa: RUF005

    def add_piece(
        self,
        piece_type: int,
        position: Pos,
        location: Pos | Vector2 | None = None,
    ) -> str:
        """Add piece given type and position."""
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
        """Add outlined tile given position."""
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
        """Generate an image of a game board."""
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
    "Component that will use targeting to go to wherever you click on the screen."

    __slots__ = ("selected",)
    outline = pygame.color.Color(255, 220, 0)

    def __init__(self) -> None:
        super().__init__("click_dest")

        self.selected = False

    def bind_handlers(self) -> None:
        "Register PygameMouseButtonDown and tick handlers."
        self.register_handlers(
            {
                "click": self.click,
                "drag": self.drag,
                "PygameMouseButtonDown": self.mouse_down,
                "tick": self.move_towards_dest,
                "init": self.cache_outline,
                "test": self.test,
            },
        )

    async def test(self, event: Event[Any]) -> None:
        print(f"{event = }")

    async def cache_outline(self, _: Event[Any]) -> None:
        "Precalculate outlined images."
        image: sprite.ImageComponent = self.get_component("image")
        outline: sprite.OutlineComponent = image.get_component("outline")
        outline.precalculate_all_outlined(self.outline)

    async def update_selected(self) -> None:
        "Update selected."
        image: sprite.ImageComponent = self.get_component("image")
        outline: sprite.OutlineComponent = image.get_component("outline")

        color = (None, self.outline)[int(self.selected)]
        outline.set_color(color)

        if not self.selected:
            movement: sprite.MovementComponent = self.get_component("movement")
            movement.speed = 0

    async def click(self, event: Event[dict[str, int]]) -> None:
        "Toggle selected."
        if event.data["button"] == 1:
            self.selected = not self.selected

            await self.update_selected()

    async def drag(self, event: Event[Any]) -> None:
        "Drag sprite."
        if not self.selected:
            self.selected = True
            await self.update_selected()
        movement: sprite.MovementComponent = self.get_component("movement")
        movement.speed = 0

    async def mouse_down(self, event: Event[dict[str, int | Pos]]) -> None:
        "Target click pos if selected."
        if not self.selected:
            return
        if event.data["button"] == 1:
            movement: sprite.MovementComponent = self.get_component("movement")
            movement.speed = 200
            target: sprite.TargetingComponent = self.get_component("targeting")
            assert isinstance(event.data["pos"], tuple)
            target.destination = Vector2.from_iter(event.data["pos"])

    async def move_towards_dest(self, event: Event[dict[str, float]]) -> None:
        "Move closer to destination."
        target: sprite.TargetingComponent = self.get_component("targeting")
        await target.move_destination_time(event.data["time_passed"])


class MrFloppy(sprite.Sprite):
    "Mr. Floppy test sprite."

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
            ),
        )

        movement = self.get_component("movement")
        targeting = self.get_component("targeting")
        image = self.get_component("image")

        movement.speed = 200

        floppy: pygame.surface.Surface = pygame.image.load(
            path.join(path.dirname(__file__), "data", "mr_floppy.png"),
        )

        image.add_images(
            {
                0: floppy,
                # '1': pygame.transform.flip(floppy, False, True)
                1: pygame.transform.rotate(floppy, 270),
                2: pygame.transform.flip(floppy, True, True),
                3: pygame.transform.rotate(floppy, 90),
            },
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
        self, image_identifiers: list[str | int],
    ) -> Generator[str | int | None, None, None]:
        "Animation controller."
        cidx = 0
        while True:
            count = len(image_identifiers)
            if not count:
                yield None
                continue
            cidx = (cidx + 1) % count
            yield image_identifiers[cidx]

    async def drag(self, event: Event[dict[str, int | Pos]]) -> None:
        "Move by relative from drag."
        if event.data["button"] != 1:
            return
        sprite_component: sprite.Sprite = self.get_component("sprite")
        assert isinstance(event.data["rel"], tuple)
        sprite_component.location += event.data["rel"]
        sprite_component.dirty = 1


class FPSCounter(objects.Text):
    "FPS counter."

    __slots__ = ()

    def __init__(self) -> None:
        font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28,
        )
        super().__init__("fps", font)

        self.location = Vector2.from_iter(self.image.get_size()) / 2 + (5, 5)

    async def on_tick(self, event: Event[dict[str, float]]) -> None:
        "Update text."
        # self.text = f'FPS: {event.data["fps"]:.2f}'
        self.text = f'FPS: {event.data["fps"]:.0f}'

    def bind_handlers(self) -> None:
        super().bind_handlers()
        self.register_handlers(
            {
                "tick": self.on_tick,
            },
        )


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


class HaltState(AsyncState["CheckersClient"]):
    "Halt state to set state to None so running becomes False."

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("Halt")

    async def check_conditions(self) -> None:
        "Set active state to None."
        assert self.machine is not None
        await self.machine.set_state(None)


class GameState(AsyncState["CheckersClient"]):
    "Checkers Game Asynchronous State base class."

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
        self, new_state: str | None,
    ) -> Callable[[Event[Any]], Awaitable[None]]:
        """Return an async function that will change state to `new_state`."""

        async def set_state(*args: object, **kwargs: object) -> None:
            if self.machine is None:
                return
            await self.machine.set_state(new_state)

        return set_state


class InitializeState(AsyncState["CheckersClient"]):
    "Initialize Checkers."

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("initialize")

    async def check_conditions(self) -> str:
        return "title"


class TestState(GameState):
    "Test state."

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
    "Game Title State."

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("title")

    async def entry_actions(self) -> None:
        """Add buttons."""
        assert self.machine is not None
        self.id = self.machine.new_group("title")

        button_font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28,
        )
        title_font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 56,
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
            "play_internal_hosting",
        )
        self.group_add(internal_button)

        await self.machine.raise_event(Event("init", None))


##    async def check_conditions(self) -> str:
##        return "play_hosting"  # "play_hosting" # "play_joining"


class PlayHostingState(AsyncState["CheckersClient"]):
    "Start running server."

    __slots__ = ()

    internal_server = False

    def __init__(self) -> None:
        extra = "_internal" if self.internal_server else ""
        super().__init__(f"play{extra}_hosting")

    async def entry_actions(self) -> None:
        "Start hosting server."
        assert self.machine is not None
        self.machine.manager.add_components(
            (
                GameServer(self.internal_server),
                GameClient("network"),
            ),
        )

        await self.machine.raise_event(Event("server_start", None))

    async def exit_actions(self) -> None:
        "Have client connect."
        assert self.machine is not None
        await self.machine.raise_event(
            Event("client_connect", ("127.0.0.1", PORT)),
        )

    async def check_conditions(self) -> str | None:
        assert self.machine is not None
        server: GameServer = self.machine.manager.get_component("GameServer")
        return "play" if server.running else None


class PlayInternalHostingState(PlayHostingState):
    "Host server with internal server mode."

    __slots__ = ()

    internal_server = True


class JoinButton(Button):
    __slots__ = ()

    def __init__(self, id_: int, font: pygame.Font, motd: str) -> None:
        super().__init__(f"join_button_{id_}", font)
        self.text = motd
        self.location = [x // 2 for x in SCREEN_SIZE]

    async def handle_click(self, _: object) -> None:
        print(self.manager)


class PlayJoiningState(GameState):
    "Start running client."

    __slots__ = (
        "font",
        "buttons",
        "next_button",
    )

    def __init__(self) -> None:
        super().__init__("play_joining")

        self.next_button = 0
        self.buttons = {}

        self.font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28,
        )

    async def entry_actions(self) -> None:
        "Add game client component."
        await super().entry_actions()
        assert self.machine is not None
        self.id = self.machine.new_group("join")
        client = GameClient("network")

        self.machine.manager.add_component(client)

        self.buttons.clear()
        self.next_button = 0

        self.manager.register_handler(
            "update_listing", self.handle_update_listing,
        )

        await self.manager.raise_event(Event("update_listing", None))

    async def handle_update_listing(self, _: object) -> None:
        assert self.machine is not None
        for advertisement in await read_advertisements():
            motd, details = advertisement

            if details not in self.buttons:
                self.buttons[details] = self.next_button

                print(f"{motd = }  {details = }")
                ##                button = JoinButton(self.next_button, self.font, motd, details)
                ##                self.group_add(button)

                self.next_button += 1
                ####
                await self.machine.raise_event(
                    Event("client_connect", details, 1),
                )
                return "play"
        print("click")
        await self.manager.raise_event(Event("update_listing", None))
        return None


##    async def check_conditions(self) -> str | None:
##        return None


class PlayState(GameState):
    "Game Play State."

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("play")

    def register_handlers(self) -> None:
        self.manager.register_handlers(
            {
                "client_disconnected": self.handle_client_disconnected,
                "game_winner": self.handle_game_over,
            },
        )

    def add_actions(self) -> None:
        super().add_actions()
        self.register_handlers()

    async def entry_actions(self) -> None:
        assert self.machine is not None
        self.id = self.machine.new_group("play")

        # self.group_add(())
        gameboard = GameBoard(
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

        self.register_handlers()

        assert self.manager.has_handler("game_winner")

    async def handle_game_over(self, event: Event[int]) -> None:
        """Handle game over event."""
        winner = event.data
        # print(f"Player {PLAYERS[winner]} ({winner}) Won")

        font = pygame.font.Font(
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28,
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
            trio.Path(path.dirname(__file__), "data", "VeraSerif.ttf"), 28,
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
    """Checkers Game Client."""

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
            ),
        )

    @property
    def running(self) -> bool:
        "Boolean of if state machine is running."
        return self.active_state is not None

    async def raise_event(self, event: Event[Any]) -> None:
        "Raise component event in all groups."
        await self.manager.raise_event(event)


async def async_run() -> None:
    "Main loop of everything."
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
            path.join(path.dirname(__file__), "data", "background.png"),
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
                        event_manager.raise_event, sprite_event,
                    )
                event_nursery.start_soon(client.think)
                event_nursery.start_soon(clock.tick, FPS)

            await client.raise_event(
                Event(
                    "tick",
                    sprite.TickEventData(
                        time_passed=clock.get_time()
                        / 1e9,  # nanoseconds -> seconds
                        fps=clock.get_fps(),
                    ),
                ),
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
    "Run asynchronous side of everything."
    trio.run(async_run)


def cli_run() -> None:
    "Start game."
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")

    # If we're not imported as a module, run.
    # Make sure the game will display correctly on high DPI monitors on Windows.

    if IS_WINDOWS:
        from ctypes import windll  # type: ignore

        with contextlib.suppress(AttributeError):
            windll.user32.SetProcessDPIAware()
        del windll

    try:
        pygame.init()
        run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    cli_run()
