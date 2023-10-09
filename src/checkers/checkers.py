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

import math
import os
from collections.abc import Generator, Iterable, Sequence
from os import path
from random import randint
from typing import Any, NamedTuple, TypeVar, cast

import base2d
import objects
import pygame
import sprite
import trio
from async_clock import Clock
from base_io import StructFormat
from buffer import Buffer
from component import Component, ComponentManager, Event, ExternalRaiseManager
from network import NetworkEventComponent, Server
from pygame.color import Color
from pygame.locals import K_ESCAPE, KEYUP, QUIT, WINDOWRESIZED
from pygame.rect import Rect
from pygame.surface import Surface
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


def get_sides(xy: Pos) -> tuple[Pos, Pos, Pos, Pos]:
    "Returns the tile xy choordinates on the top left, top right, bottom left, and bottom right sides of given xy choordinates"
    cx, cy = xy
    sides = []
    for raw_dy in range(2):
        dy = raw_dy * 2 - 1
        ny = cy + dy
        for raw_dx in range(2):
            dx = raw_dx * 2 - 1
            nx = cx + dx
            sides.append((nx, ny))
    tuple_sides = tuple(sides)
    assert len(tuple_sides) == 4
    return cast(tuple[Pos, Pos, Pos, Pos], tuple_sides)


def pawn_modify(moves: tuple[T, ...], piece_type: int) -> tuple[T, ...]:
    "Modifies a list based on piece id to take out invalid moves for pawns"
    assert (
        len(moves) == 4
    ), "List size MUST be four for this to return valid results!"
    if (
        piece_type == 0
    ):  # If it's a white pawn, it can only move to top left and top right
        return moves[:2]
    if (
        piece_type == 1
    ):  # If it's a black pawn, it can only move to bottom left anf bottom right
        return moves[2:]
    return moves


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
                f"self_destruct_piece_{self.position_name}": self.handle_self_destruct_event,
                f"piece_move_{self.position_name}": self.handle_move_event,
                "reached_destination": self.handle_reached_destination_event,
                f"piece_king_{self.position_name}": self.handle_king_event,
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
                    self.position_name,
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

    async def handle_tick_event(self, event: Event[dict[str, float]]) -> None:
        "Move toward destination"
        time_passed = event.data["time_passed"]
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

    async def handle_king_event(self, event: Event[None]) -> None:
        """King self during movement animation"""
        self.piece_type += 2
        self.set_outlined(False)


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
            Event("gameboard_tile_clicked", self.position_name, 1)
        )

    async def handle_self_destruct_event(self, event: Event[None]) -> None:
        "Remove from all groups and remove self component"
        self.kill()
        self.manager.remove_component(self.name)


def generate_tile_image(
    color: Color  # type: ignore[valid-type]
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


class ActionSet(NamedTuple):
    """Represents a set of actions"""

    jumps: dict[Pos, list[Pos]]
    moves: tuple[Pos, ...]
    ends: set[Pos]


class GameBoard(sprite.Sprite):
    "Entity that stores data about the game board and renders it"
    __slots__ = (
        "board_size",
        "tile_size",
        "tile_color_map",
        "tile_surfs",
        "piece_map",
        "turn",
        "game_won",
        "selected_piece",
        "pieces",
        "actions",
        "ai_player",
    )

    def __init__(
        self,
        board_size: tuple[int, int],
        tile_size: int,
        turn: int,
        ai_player: int | None = None,
    ) -> None:
        super().__init__("board")

        self.add_component(sprite.ImageComponent())

        # Define Tile Color Map and Piece Map
        self.tile_color_map = (BLACK, RED)

        # Define Black Pawn color to be more of a dark grey so you can see it
        black = (127, 127, 127)
        red = (160, 0, 0)

        # Define each piece by giving what color it should be and an image
        # to recolor
        self.piece_map = (
            (red, "data/Pawn.png"),
            (black, "data/Pawn.png"),
            (red, "data/King.png"),
            (black, "data/King.png"),
        )

        # Store the Board Size and Tile Size
        self.board_size = board_size
        self.tile_size = tile_size

        # Set playing side
        self.turn = turn
        self.pieces: dict[Pos, int] = {}
        self.actions: dict[Pos, ActionSet] = {}
        self.game_won: int | None = None
        self.ai_player = ai_player

        self.selected_piece: str | None = None

        self.update_location_on_resize = True

    def get_tile_name(self, x: int, y: int) -> str:
        """Get name of a given tile"""
        return chr(65 + x) + str(self.board_size[1] - y)

    def get_tile_pos(self, name: str) -> Pos:
        """Get tile position from it's name"""
        x = ord(name[0]) - 65
        y = self.board_size[1] - int(name[1:])
        return (x, y)

    def does_piece_king(self, piece_type: int, position: Pos) -> bool:
        """Return if piece needs to be kinged given it's type and position"""
        _, y = position
        _, h = self.board_size
        return (piece_type == 0 and y == 0) or (piece_type == 1 and y == h - 1)

    def valid_location(self, position: Pos) -> bool:
        """Return if position is valid"""
        x, y = position
        w, h = self.board_size
        return 0 <= x and 0 <= y and x < w and y < h

    def get_jumps(
        self,
        position: Pos,
        piece_type: int | None = None,
        _recursion: int = 0,
    ) -> dict[Pos, list[Pos]]:
        """Gets valid jumps a piece can make

        position is a xy coordinate tuple pointing to a board position
            that may or may not have a piece on it.
        piece_type is the piece type at position. If not
            given, position must point to a tile with a piece on it

        Returns dictionary that maps end positions to
        jumped pieces to get there"""
        if piece_type is None:
            piece_type = self.pieces[position]

        # If we are kinged, get a pawn version of ourselves.
        # Take that plus one mod 2 to get the pawn of the enemy
        enemy_pawn = (piece_type + 1) % 2
        # Then get the pawn and the king in a list so we can see if a piece
        # is our enemy
        enemy_pieces = {enemy_pawn, enemy_pawn + 2}

        # Get the side choordinates of the tile and make them tuples so
        # the scan later works properly.
        sides = get_sides(position)
        # Make a dictionary to find what direction a tile is in if you
        # give it the tile.
        # end position : jumped pieces

        # Make a dictionary for the valid jumps and the pieces they jump
        valid: dict[Pos, list[Pos]] = {}

        # For each side tile in the jumpable tiles for this type of piece,
        for direction, side in pawn_modify(
            tuple(enumerate(sides)), piece_type
        ):
            side_piece = self.pieces.get(side)
            # Side piece must be one of our enemy's pieces
            if side_piece not in enemy_pieces:
                continue
            # Get the direction from the dictionary we made earlier
            # Get the coordiates of the tile on the side of the main tile's
            # side in the same direction as the main tile's side
            side_side = get_sides(side)[direction]
            side_side_piece = self.pieces.get(side_side)
            # If the side exists and it's open,
            if side_side_piece is None and self.valid_location(side_side):
                # Add it the valid jumps dictionary and add the tile
                # to the list of end tiles.
                valid[side_side] = [side]

        # For each end point tile in the list of end point tiles,
        for end_tile in tuple(valid):
            # Get the dictionary from the jumps you could make
            # from that end tile
            w, h = self.board_size
            if _recursion + 1 > math.ceil((w**2 + h**2) ** 0.25):
                break
            # If the piece has made it to the opposite side,
            piece_type_copy = piece_type
            if self.does_piece_king(piece_type_copy, end_tile):
                # King that piece
                piece_type_copy += 2
                _recursion = -1
            add_valid = self.get_jumps(
                end_tile, piece_type_copy, _recursion=_recursion + 1
            )
            # For each key in the new dictionary of valid tile's keys,
            for end_pos, jumped_pieces in add_valid.items():
                # If the key is not already existant in the list of
                # valid destinations,
                if end_pos not in valid:
                    # Add that destination to the dictionary and every
                    # tile you have to jump to get there.
                    no_duplicates = [
                        p for p in jumped_pieces if p not in valid[end_tile]
                    ]
                    valid[end_pos] = valid[end_tile] + no_duplicates

        return valid

    def get_moves(self, position: Pos) -> tuple[Pos, ...]:
        "Gets valid moves piece at position can make, not including jumps"
        piece_type = self.pieces[position]
        # Get the side xy choords of the tile's xy pos,
        # then modify results for pawns
        moves = pawn_modify(get_sides(position), piece_type)
        return tuple(
            [
                m
                for m in filter(self.valid_location, moves)
                if m not in self.pieces
            ]
        )

    def calculate_actions(self, position: Pos) -> ActionSet:
        "Calculate all the actions the piece at given position can make"
        jumps = self.get_jumps(position)
        moves = self.get_moves(position)
        ends = set(jumps)
        ends.update(moves)
        return ActionSet(jumps, moves, ends)

    def bind_handlers(self) -> None:
        "Register handlers"
        self.register_handlers(
            {
                "init": self.handle_init_event,
                "gameboard_piece_clicked": self.handle_piece_clicked_event,
                "gameboard_select_piece": self.handle_select_piece_event,
                "gameboard_tile_clicked": self.handle_tile_clicked_event,
                "gameboard_select_tile": self.handle_select_tile_event,
                "gameboard_piece_moved": self.handle_piece_moved_event,
                "gameboard_restart": self.handle_restart_event,
                "gameboard_preform_turn": self.handle_preform_turn_event,
            }
        )

    async def handle_init_event(self, event: Event[None]) -> None:
        "Start up game"
        # Generate tile data
        self.generate_tile_images()
        self.image = self.generate_board_image()
        self.visible = True
        await self.handle_restart_event(event)

    async def handle_restart_event(self, event: Event[None]) -> None:
        """Reset board"""
        async with trio.open_nursery() as nursery:
            for piece_position in self.pieces:
                if piece_position in self.actions:
                    tiles = self.actions[piece_position].ends
                    for tile_position in tiles:
                        tile_name = self.get_tile_name(*tile_position)
                        event = Event(f"self_destruct_tile_{tile_name}", None)
                        nursery.start_soon(self.raise_event, event)
                piece_name = self.get_tile_name(*piece_position)
                event = Event(f"self_destruct_piece_{piece_name}", None)
                nursery.start_soon(self.raise_event, event)

        self.actions.clear()
        self.pieces.clear()
        self.game_won = None
        self.selected_piece = None

        self.generate_pieces()

    async def handle_select_piece_event(self, event: Event[str]) -> None:
        """Seperate event to handle selection of a piece

        Seperated so AIs can call select piece without
        interference from screen click events"""
        piece_name = event.data

        selected_piece: str | None

        if piece_name != self.selected_piece:
            if self.selected_piece is not None:
                await self.raise_event(
                    Event(f"piece_outline_{self.selected_piece}", False)
                )
            selected_piece = piece_name
            await self.raise_event(Event(f"piece_outline_{piece_name}", True))
        else:
            await self.raise_event(
                Event(f"piece_outline_{self.selected_piece}", False)
            )
            selected_piece = None
        await self.select_piece(selected_piece)

    async def handle_piece_clicked_event(
        self, event: Event[tuple[str, int]]
    ) -> None:
        """Update selected piece and outlines accordingly"""
        piece_name, piece_type = event.data

        if piece_type % 2 != self.turn:
            return
        if self.turn == self.ai_player:
            return

        # CHANGE to piece_click_serverbound
        await self.raise_event(Event("gameboard_select_piece", piece_name))

    def get_actions_set(self, piece_position: Pos) -> ActionSet:
        """Calculate and return ActionSet if required"""
        if piece_position in self.actions:
            new_action_set = self.actions[piece_position]
        else:
            new_action_set = self.calculate_actions(piece_position)
            self.actions[piece_position] = new_action_set
        return new_action_set

    async def select_piece(self, piece_name: str | None) -> None:
        """Update glowing tiles from new selected piece"""
        ignore: set[tuple[int, int]] = set()

        if piece_name is not None:
            # Calculate actions if required
            new_action_set = self.get_actions_set(
                self.get_tile_pos(piece_name)
            )
            ignore = new_action_set.ends

        ignored: set[tuple[int, int]] = set()

        # Remove outlined tiles from previous selection if existed
        if self.selected_piece is not None:
            action_set = self.get_actions_set(
                self.get_tile_pos(self.selected_piece)
            )
            ignored = action_set.ends & ignore
            remove = action_set.ends - ignore
            async with trio.open_nursery() as nursery:
                for tile_position in remove:
                    tile_name = self.get_tile_name(*tile_position)
                    event = Event(f"self_destruct_tile_{tile_name}", None)
                    nursery.start_soon(self.raise_event, event)

        if piece_name is None:
            self.selected_piece = None
            return

        # For each end point
        for tile_position in new_action_set.ends - ignored:
            self.add_tile(tile_position)

        self.selected_piece = piece_name

    async def handle_tile_clicked_event(self, event: Event[str]) -> None:
        """Preform move if it's not the AI player's turn"""
        if self.turn == self.ai_player:
            return

        await self.raise_event(Event("gameboard_select_tile", event.data))

    async def handle_select_tile_event(self, event: Event[str]) -> None:
        """Start preforming move"""
        # No one allowed to move during animation
        self.turn += 2

        tile_name = event.data
        piece_name = self.selected_piece

        assert piece_name is not None

        tile_position = self.get_tile_pos(tile_name)
        piece_position = self.get_tile_pos(piece_name)

        assert tile_position in self.actions[piece_position].ends

        await self.raise_event(Event(f"piece_outline_{piece_name}", False))
        await self.select_piece(None)

        if tile_position in self.actions[piece_position].moves:
            tile_location = self.get_tile_location(tile_position)

            await self.raise_event(
                Event(
                    f"piece_move_{piece_name}",
                    [(tile_location, piece_position, tile_position)],
                )
            )

        if tile_position in self.actions[piece_position].jumps:
            jumped = self.actions[piece_position].jumps[tile_position]
            positions: list[tuple[Vector2, Pos, Pos]] = []

            cur_x, cur_y = piece_position
            for jumped_pos in jumped:
                start_pos = (cur_x, cur_y)

                jumped_x, jumped_y = jumped_pos
                # Rightshift 1 is more efficiant way to multiply by 2
                cur_x += (jumped_x - cur_x) << 1
                cur_y += (jumped_y - cur_y) << 1

                tile_location = self.get_tile_location((cur_x, cur_y))
                positions.append((tile_location, start_pos, (cur_x, cur_y)))
            await self.raise_event(
                Event(f"piece_move_{piece_name}", positions)
            )

    async def handle_piece_moved_event(
        self, event: Event[tuple[str, Pos, Pos, bool]]
    ) -> None:
        """Handle piece finishing one part of it's movement animation"""
        piece_name, start_pos, end_pos, done = event.data

        piece_type = self.pieces.pop(start_pos)

        if self.does_piece_king(piece_type, end_pos):
            piece_type += 2
            await self.raise_event(Event(f"piece_king_{piece_name}", None))

        self.pieces[end_pos] = piece_type

        start_x, start_y = start_pos
        end_x, end_y = end_pos

        delta_x = end_x - start_x
        delta_y = end_y - start_y
        if abs(delta_x) > 1 and abs(delta_y) > 1:
            # Leftshift 1 is more efficiant way to divide by 2
            jumped_x = start_x + (delta_x >> 1)
            jumped_y = start_y + (delta_y >> 1)

            if self.pieces.pop((jumped_x, jumped_y), None) is not None:
                jumped_name = self.get_tile_name(jumped_x, jumped_y)
                await self.raise_event(
                    Event(f"self_destruct_piece_{jumped_name}", None)
                )

        if done:
            await self.raise_event(
                Event(f"self_destruct_piece_{piece_name}", None)
            )

            self.add_piece(self.pieces[end_pos], end_pos)

            await self.turn_over()

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

    def add_piece(self, piece_type: int, position: Pos) -> str:
        """Add piece given type and position"""
        group = self.groups()[-1]
        # Get the proper name of the tile we're creating ('A1' to 'H8')
        name = self.get_tile_name(*position)

        piece = Piece(
            piece_type=piece_type,
            position=position,
            position_name=name,
            location=self.get_tile_location(position),
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

    def generate_pieces(self) -> None:
        """Generate data about each tile"""
        board_width, board_height = self.board_size
        # Reset tile data
        loc_y = 0
        # Get where pieces should be placed
        z_to_1 = round(board_height / 3)  # White
        z_to_2 = (board_height - (z_to_1 * 2)) + z_to_1  # Black
        # For each xy position in the area of where tiles should be,
        for y in range(board_height):
            # Reset the x pos to 0
            loc_x = 0
            for x in range(board_width):
                # Get the color of that spot by adding x and y mod the number of different colors
                color = (x + y) % len(self.tile_color_map)
                # If a piece should be placed on that tile and the tile is not Red,
                if (not color) and ((y <= z_to_1 - 1) or (y >= z_to_2)):
                    # Set the piece to White Pawn or Black Pawn depending on the current y pos
                    piece = int(y <= z_to_1)
                    self.add_piece(piece, (x, y))
                # Increment the x counter by tile_size
                loc_x += self.tile_size
            # Increment the y counter by tile_size
            loc_y += self.tile_size

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

    def check_for_win(self) -> int | None:
        """Return player number if they won else None"""
        # For each of the two players,
        for player in range(2):
            # Get that player's possible pieces
            player_pieces = {player, player + 2}
            # For each tile in the playable tiles,
            for position, piece_type in self.pieces.items():
                # If the tile's piece is one of the player's pieces,
                if piece_type in player_pieces:
                    if self.get_actions_set(position).ends:
                        # Player has at least one move, no need to continue
                        break
            else:
                # Continued without break, so player either has no moves
                # or no possible moves, so their opponent wins
                return (player + 1) % 2
        return None

    async def turn_over(self) -> None:
        """Continue to next player's turn"""
        # Clear actions
        self.actions.clear()

        # Toggle the active player
        self.turn = (self.turn + 1) % 2

        # If no one has won,
        if self.game_won is None:
            # Check for wins
            win = self.check_for_win()
            # If someone has won,
            if win is not None:
                # Don't let anybody move
                self.turn = 2
                # The winner is the person check_for_win found.
                self.game_won = win
                await self.raise_event(Event("game_over", self.game_won, 1))
        elif self.turn == self.ai_player:
            await self.raise_event(Event("game_ready_for_next", None, 1))

    async def handle_preform_turn_event(
        self, event: Event[tuple[str, str]]
    ) -> None:
        """Preform a turn"""
        piece_name, tile_name = event.data
        await self.raise_event(Event("gameboard_select_piece", piece_name))
        await self.raise_event(Event("gameboard_select_tile", tile_name))


def find_ais() -> list[str]:
    "Returns the filename without the '.py' extention of any python files with 'AI' in their filename"
    ais = []
    # For each filename in the current directory,
    for filename in os.listdir(os.getcwd()):
        # If it's a python file and the word 'AI' is in it's filename,
        if filename.endswith(".py") and "AI" in filename:
            # Add the filename without the exention to the list of ais
            ais.append(filename.split(".py", 1)[0])
    # Return all the AI filenames we found
    return ais


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

    async def drag(
        self, event: Event[dict[str, int | tuple[int, int]]]
    ) -> None:
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


class GameClient(NetworkEventComponent):
    __slots__ = ("reading",)

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.reading = False

        self.register_network_write_events(
            {
                "piece_click_serverbound": 0,
                "tile_click_serverbound": 1,
            }
        )
        self.register_read_network_events(
            {
                0: "select_piece_clientbound",
                1: "select_tile_clientbound",
                2: "no_actions_from_server",
                ##            0: "gameboard_select_piece",
                ##            1: "gameboard_select_tile",
            }
        )

    def bind_handlers(self) -> None:
        super().bind_handlers()
        self.register_handlers(
            {
                "gameboard_piece_clicked": self.write_piece_click,
                "gameboard_tile_clicked": self.write_tile_click,
                "select_piece_clientbound": self.read_piece_select,
                "select_tile_clientbound": self.read_tile_select,
                "network_stop": self.handle_network_stop,
                "client_connect": self.handle_client_connect,
                "tick": self.handle_tick,
            }
        )

    async def handle_tick(self, event: Event[dict[str, float]]) -> None:
        """Raise events from server"""
        if hasattr(self, "stream") and not self.reading:
            self.reading = True
            await self.raise_event_from_read_network()
            self.reading = False

    async def handle_client_connect(
        self, event: Event[tuple[str, int]]
    ) -> None:
        "Have client connect to address"
        if not hasattr(self, "stream"):
            print(f"{self.__class__.__name__}: start connect")
            await self.connect(*event.data)

    async def write_piece_click(self, event: Event[tuple[str, int]]) -> None:
        """Write piece click event"""
        if not hasattr(self, "stream"):
            return
        piece_name, piece_type = event.data

        buffer = Buffer()
        buffer.write_utf(piece_name)
        buffer.write_value(StructFormat.UINT, piece_type)

        print(f"{self.__class__.__name__}: writing piece_click_serverbound")

        await self.write_event(Event("piece_click_serverbound", buffer))

    async def write_tile_click(self, event: Event[str]) -> None:
        """Write tile click event"""
        tile_name = event.data

        buffer = Buffer()
        buffer.write_utf(tile_name)

        print(f"{self.__class__.__name__}: writing tile_click_serverbound")

        await self.write_event(Event("tile_click_serverbound", buffer))

    async def read_piece_select(self, event: Event[bytearray]) -> None:
        buffer = Buffer(event.data)

        piece_name = buffer.read_utf()

        print(f"{self.__class__.__name__}: reading gameboard_select_piece")

        await self.raise_event(Event("gameboard_select_piece", piece_name))

    async def read_tile_select(self, event: Event[bytearray]) -> None:
        buffer = Buffer(event.data)

        piece_name = buffer.read_utf()

        print(f"{self.__class__.__name__}: reading gameboard_select_tile")

        await self.raise_event(Event("gameboard_select_tile", piece_name))

    async def handle_network_stop(self, event: Event[None]) -> None:
        if hasattr(self, "stream"):
            print(f"{self.__class__.__name__}: close")
            await self.close()

    def __del__(self) -> None:
        print(f"del {self.__class__.__name__}")


class ServerClient(NetworkEventComponent):
    __slots__ = ()

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.timeout = 2

        self.register_network_write_events(
            {
                "select_piece_clientbound": 0,
                ##                "select_tile_clientbound": 1,
                "no_data_from_server": 2,
            }
        )
        self.register_read_network_events(
            {
                0: "client_select_piece",
            }
        )

    async def handle_debug_print_event(self, event: Event) -> None:
        print(f"handle_debug_print_event {event = }")

    def bind_handlers(self) -> None:
        super().bind_handlers()
        self.register_handlers(
            {
                "client_select_piece": self.read_piece_select,
                "select_tile_clientbound": self.read_tile_select,
                "network_stop": self.handle_network_stop,
                "read_piece_select": self.read_piece_select,
                ##                "debug_print_event": self.handle_debug_print_event,
            }
        )

    async def write_piece_click(self, event: Event[tuple[str, int]]) -> None:
        """Write piece click event"""
        piece_name, piece_type = event.data

        buffer = Buffer()
        buffer.write_utf(piece_name)
        buffer.write_value(StructFormat.UINT, piece_type)

        print(f"{self.__class__.__name__} writing piece_click_serverbound")

        await self.write_event(Event("piece_click_serverbound", buffer))

    async def write_tile_click(self, event: Event[str]) -> None:
        """Write tile click event"""
        tile_name = event.data

        buffer = Buffer()
        buffer.write_utf(tile_name)

        print(f"{self.__class__.__name__} writing tile_click_serverbound")

        await self.write_event(Event("tile_click_serverbound", buffer))

    async def read_piece_select(self, event: Event[bytearray]) -> None:
        buffer = Buffer(event.data)

        piece_name = buffer.read_utf()

        print(f"{self.__class__.__name__} reading gameboard_select_piece")

        await self.raise_event(Event("gameboard_select_piece", piece_name, 1))

    ##        await self.write_event(Event("select_piece_clientbound", event.data))

    async def read_tile_select(self, event: Event[bytearray]) -> None:
        buffer = Buffer(event.data)

        piece_name = buffer.read_utf()

        print(f"{self.__class__.__name__} reading gameboard_select_tile")

        await self.raise_event(Event("gameboard_select_tile", piece_name))

    async def handle_network_stop(self, event: Event[None]) -> None:
        print(f"{self.__class__.__name__}: close")
        await self.close()

    def __del__(self) -> None:
        print(f"del {self.__class__.__name__}")


class GameServer(Server):
    """Checkers server"""

    __slots__ = ("client_count",)

    def __init__(self) -> None:
        super().__init__("gameserver")
        self.client_count = 0

    def bind_handlers(self) -> None:
        """Register start_server and stop_server"""
        self.register_handlers(
            {
                "server_start": self.start_server,
                "network_stop": self.stop_server,
                "select_piece_clientbound": self.handle_select_piece,
                "select_tile_clientbound": self.handle_select_tile,
            }
        )

    async def stop_server(self, event: Event[None] | None = None) -> None:
        """Stop serving and disconnect all NetworkEventComponents"""
        self.stop_serving()
        component_names = []
        async with trio.open_nursery() as nursery:
            for component in self.get_all_components():
                if isinstance(component, NetworkEventComponent):
                    nursery.start_soon(component.stream.aclose)
                    component_names.append(component.name)
        for component_name in component_names:
            self.remove_component(component_name)

    async def start_server(self, event: Event[None] | None = None) -> None:
        """Serve clients"""
        print(f"{self.__class__.__name__}: starting server")
        await self.stop_server()
        self.client_count = 0
        await self.serve(PORT, backlog=0)

    async def handler(self, stream: trio.SocketStream) -> None:
        """Accept clients"""
        self.client_count += 1
        if self.client_count >= 2:
            self.stop_serving()
        if self.client_count > 2:
            await stream.aclose()
        print(f"{self.__class__.__name__}: client connected")

        client = ServerClient.from_stream(
            f"client_{self.client_count}", stream
        )
        self.add_component(client)

        while True:
            try:
                ##                print(f"{self.__class__.__name__}: waiting for client event")
                await client.write_event(
                    Event("no_data_from_server", bytearray())
                )
                await client.raise_event_from_read_network()
            except trio.ClosedResourceError:
                break

    ##        finally:
    ##            self.client_count -= 1
    ##            await stream.aclose()

    async def handle_select_piece(self, event: Event[bytearray]) -> None:
        print(event)

    async def handle_select_tile(self, event: Event[bytearray]) -> None:
        print(event)

    def __del__(self) -> None:
        print(f"del {self.__class__.__name__}")


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
        assert self.machine is not None
        self.machine.manager.add_component(self.manager)

    def group_add(self, new_sprite: sprite.Sprite) -> None:
        assert self.machine is not None
        group = self.machine.get_group(self.id)
        assert group is not None, "Expected group from new group id"
        group.add(new_sprite)
        self.manager.add_component(new_sprite)

    async def exit_actions(self) -> None:
        assert self.machine is not None
        self.machine.remove_group(self.id)
        self.manager.unbind_components()


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
        assert self.machine is not None
        self.id = self.machine.new_group("title")

        # self.group_add()

        await self.machine.raise_event(Event("init", None))

    async def check_conditions(self) -> str:
        return "play"  # "play_hosting" # "play_joining"


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
    __slots__ = ("winner",)

    def __init__(self) -> None:
        super().__init__("play")

        self.winner: int | None = None

    def add_actions(self) -> None:
        super().add_actions()
        self.manager.register_handlers(
            {
                "game_over": self.handle_game_over,
                # "game_ready_for_next": self.handle_ready_for_next,
                # "game_preform_turn": self.hande_preform_turn,
            }
        )

    async def entry_actions(self) -> None:
        self.winner = None

        assert self.machine is not None
        self.id = self.machine.new_group("play")

        # self.group_add(())
        gameboard = GameBoard(
            (8, 8),
            45,
            randint(  # noqa: S311  # Not important to be cryptographically safe
                0, 1
            ),
        )
        gameboard.location = [x // 2 for x in SCREEN_SIZE]
        self.group_add(gameboard)

        await self.machine.raise_event(Event("init", None))

    async def exit_actions(self) -> None:
        assert self.machine is not None
        await super().exit_actions()
        # Fire server stop event so server shuts down if it exists
        await self.machine.raise_event(Event("network_stop", None))

    async def check_conditions(self) -> str | None:
        if self.winner is None:
            return None
        return "title"

    async def handle_game_over(self, event: Event[int]) -> None:
        """Handle game over event."""
        self.winner = event.data
        print(f"Player {self.winner} Won")

    async def handle_preform_turn(self, event: Event[tuple[str, str]]) -> None:
        "Handle preform turn action"
        assert self.machine is not None
        data = event.data
        if len(data) != 2:
            return
        for item in data:
            if not isinstance(item, str):
                return
        await self.machine.raise_event(Event("gameboard_preform_turn", data))


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
                    {
                        "time_passed": clock.get_time() / 1000,
                        "fps": clock.get_fps(),
                    },
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
