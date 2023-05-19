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

from __future__ import annotations

import os
import traceback
from collections.abc import Collection, Sequence
from math import sqrt
from random import randint
from typing import Any

import pygame
from base2d import *
from pygame.locals import *
from pygame.surface import Surface
from Vector2 import Vector2

__title__ = "Checkers"
__version__ = "0.0.5"

SCREEN_SIZE = (640, 480)

PIC_PATH = "pic/"

FPS = 60

PLAYERS = ["Red Player", "Black Player"]


def blit_text(
    font_name: str,
    font_size: int,
    text: str,
    color: tuple[int, int, int],
    xy: Vector2 | tuple[int, int],
    dest: Surface,
    middle: bool = True,
) -> None:
    "Blit rendered text to dest with the font at font_size colored color at x, y"
    # Get a surface of the rendered text
    surf = render_text(font_name, font_size, text, color)
    # If rendering in the middle of the text,
    if middle:
        # Modify the xy choordinates to be in the middle
        w: int
        h: int
        w, h = surf.get_size()
        xy = (xy[0] - w // 2, xy[1] - h // 2)
    # Blit the text surface to the destination surface at the xy position
    dest.blit(surf, to_int(xy))


def render_text(
    font_name: str, font_size: int, text: str, color: tuple[int, int, int]
) -> Surface:
    "Render text with a given font at font_size with the text in the color of color"
    # Load the font at the size of font_size
    font = pygame.font.Font(font_name, font_size)
    # Using the loaded font, render the text in the color of color
    surf = font.render(text, False, color)
    return surf


class World(WorldBase):
    "This is the world. All entities are stored here."

    def __init__(self, background: Surface) -> None:
        super().__init__()
        self.background = background.convert()

    def render(self, surface: Surface) -> None:
        "Draw the background and render all entities"
        # Prepare surface for additions
        surface.unlock()

        # Put the background on the display, covering everything
        surface.blit(self.background, (0, 0))

        render_list = {}
        render_val = 0
        # For every entity we know about,
        for entity in self.entities.values():
            # If it has the 'render_priority' attribute,
            if hasattr(entity, "render_priority"):
                # add it to the render list at the spot it want to be in
                render_list[entity.render_priority] = entity
            else:
                # Otherwise, add it to the next avalable spot.
                render_list[render_val] = entity
                render_val += 1

        # For each render value in order from lowest to greatest,
        for render_val in sorted(render_list.keys()):
            # Render the entity of that value
            render_list[render_val].render(surface)

        # Modifications to the surface are done, so re-lock it
        surface.lock()


class Cursor(GameEntity):
    "This is the Cursor! It follows the mouse cursor!"

    def __init__(self, world: World, **kwargs: Any) -> None:
        GameEntity.__init__(self, world, "cursor", None, **kwargs)

        # Create instances of each brain state
        follow_state = CursorStateFollowing(self)

        # Add states to brain
        self.brain.add_state(follow_state)

        # Set brain to the following state
        self.brain.set_state("following")

        # We are not carrying anything
        self.carry_image = None
        self.carry_tile = None

        # We should be on top of everything
        self.render_priority = 100

    def render(self, surface: Surface) -> None:
        "Render Carry Image if carrying anything"
        # If we're carrying something,
        if self.is_carry():
            # Do stuff so it renders the image's middle to our location
            x, y = self.location
            w, h = self.carry_image.get_size()
            x -= w // 2
            y -= h // 2
            xy = int(x), int(y)
            surface.blit(self.carry_image, xy)

    def get_pressed(self) -> bool:
        "Return True if the right mouse button is pressed"
        return bool(pygame.mouse.get_pressed()[0])

    def carry(self, image: Surface | None) -> None:
        "Set the image we should be carrying to image"
        self.carry_image = image

    def is_carry(self) -> bool:
        "Return True if we are carrying something"
        return not self.carry_image is None

    def drag(self, tile: Tile, image: Surface | None) -> None:
        "Grab the piece from a tile and carry it"
        self.carry_tile = tile
        self.carry(image)

    def drop(self) -> None:
        "Drop the image we're carrying"
        self.carry_tile = None
        self.carry_image = None


class CursorStateFollowing(State):
    "Cursor's main state, where it teleports to the mouse location"

    def __init__(self, cursor: Cursor) -> None:
        # Set up self as a state, with the __title__ of 'following'
        State.__init__(self, "following")
        # Store the cursor entity we're doing brain stuff for
        self.cursor = cursor

    def do_actions(self) -> None:
        "Move the cursor entity to the xy location of the mouse pointer"
        self.cursor.location = Vector2(*pygame.mouse.get_pos())
        # also set destination to mouse pointer location in case
        # anything wants to know where we're going
        self.cursor.destination = self.cursor.location


def get_sides(xy: tuple[int, int]) -> list[tuple[int, int]]:
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
    return sides


##    # Convert xy coords tuple to a list of strings, and join the strings to a stringed number, convert that to an int, and add ten because of zero positions
##    atnum = int("".join(to_str(xy))) + 10
##    # Get the xy choords plus 1 on x for top left, top right,
##    # bottom left, bottom right
##    nums = [atnum - 11, atnum + 9, atnum - 9, atnum + 11]
##    # If any errored choordinates exist, delete them
##    for i in range(len(nums) - 1, -1, -1):
##        if nums[i] < 10:
##            nums[i] = "0" + str(abs(nums[i]))
##    # Make the numbers back into usable xy choordinates by
##    # splitting each number into two seperate digits, taking the x
##    # minus one to fix the zero thing, and return a list of tuples
##    return [to_int([int(i[0]) - 1, i[1]]) for i in to_str(nums)]


def get_tile_from_coords(
    coords: tuple[int, int], gameboard: GameBoard, replace: object = ""
) -> str | object:
    "Ask the gameboard for the tiles at the xy choords given and replaces None with ''"
    tile = gameboard.get_tile("xy", tuple(coords))
    if tile is None:
        tile = replace
    return tile


def get_tiles_from_coords(
    choords: tuple[int, int], gameboard: GameBoard, replace: str | object = ""
) -> object:
    "Returns a list of tiles from the target gameboard based on xy coords and replaces blanks with ''"
    tiles = gameboard.get_tiles("xy", tuple(choords))
    for tile in tiles:
        if tile is None:
            tile = replace
    return tiles


def pawn_modify(
    lst: list[list[int]] | list[tuple[int, int]], piece_id: int
) -> list[list[int]] | list[tuple[int, int]]:
    "Modifies a list based on piece id to take out invalid moves for pawns"
    assert (
        len(lst) == 4
    ), "List size MUST be four for this to return valid results!"
    if (
        piece_id == 0
    ):  # If it's a white pawn, it can only move to top left and top right
        lst = lst[:2]
    if (
        piece_id == 1
    ):  # If it's a black pawn, it can only move to bottom left anf bottom right
        lst = lst[2:]
    return lst


def get_jumps(
    gameboard: GameBoard, piece_id: int | None, tile: Tile, _rec: int = 0
) -> tuple[list[Any], dict[Any, Any]] | tuple[list[Any], dict[Any, list[Any]]]:
    "Gets valid jumps a piece can make"
    # If the tile is None or the piece_id is invalid, return nothing for jumps.
    if tile is None or piece_id not in range(4):
        return [], {}

    # If we are kinged, get a pawn version of ourselves.
    # Take that plus one mod 2 to get the pawn of the enemy
    enemy_pawn = ((piece_id % 2) + 1) % 2
    # Then get the pawn and the king in a list so we can see if a piece is our enemy
    enemy_pieces = [enemy_pawn, enemy_pawn + 2]

    # Get the side choordinates of the tile and make them tuples so the scan later works properly.
    side_coords = [tuple(i) for i in get_sides(tile.xy)]
    # Make a dictionary to find what direction a tile is in if you give it the tile.
    side_tile_dict = {
        gameboard.get_tile("xy", side_coords[i]): i for i in range(4)
    }

    # Make a dictionary for the valid jumps and the pieces they jump
    valid = {}
    # Make a list for the end tiles after valid jumps
    side_dir_tiles = []

    # For each side tile in the jumpable tiles for this type of piece,
    for side_tile in gameboard.get_tiles(
        "xy", pawn_modify(side_coords, piece_id)
    ):
        # If the tile doesn't exist/error, go on to the next tile
        if side_tile is None or side_tile == "":
            continue
        # Get the direction from the dictionary we made earlier
        direction = side_tile_dict[side_tile]
        # If the tile's piece is one of the enemy pieces,
        if side_tile.piece in enemy_pieces:
            # Get the coordiates of the tile on the side of the main tile's side in the same direction as the main tile's side
            side_dir_side_coord = tuple(get_sides(side_tile.xy)[direction])
            # Get the tile from the game board by the main side's side coordinates
            side_dir_side = gameboard.get_tile("xy", side_dir_side_coord)
            # If the side exists and it's open,
            if (not side_dir_side is None) and side_dir_side.is_open():
                # Add it the valid jumps dictionary and add the tile to the list of end tiles.
                valid[side_dir_side.id] = [side_tile.id]
                side_dir_tiles.append(side_dir_side)

    # If there are vaid end point tiles,
    if len(side_dir_tiles):
        # For each end point tile in the list of end point tiles,
        for end_tile in side_dir_tiles:
            # Get the dictionary from the jumps you could make from that end tile
            w, h = gameboard.board_size
            if _rec + 1 > round(sqrt(sqrt(w**2 + h**2))):
                break
            # If the piece has made it to the opposite side,
            if (piece_id == 0 and end_tile.id[1] == "8") or (
                piece_id == 1 and end_tile.id[1] == "1"
            ):
                # King that piece
                piece_id += 2
                _rec = -1
            _, add_valid = get_jumps(
                gameboard, piece_id, end_tile, _rec=_rec + 1
            )
            # For each key in the new dictionary of valid tile's keys,
            for newKey in add_valid.keys():
                # If the key is not already existant in the list of valid destinations,
                if not newKey in valid.keys():
                    # Add that destination to the dictionary and every tile you have to jump to get there.
                    valid[newKey] = valid[end_tile.id] + add_valid[newKey]

    return list(valid.keys()), valid


def get_moves(
    gameboard: GameBoard, piece_id: int, tile: Tile, mustopen: bool = True
) -> tuple[str, ...]:
    "Gets valid moves a piece can make"
    # Get the side xy choords of the tile's xy pos, then modify results for pawns
    choords = [tuple(i) for i in pawn_modify(get_sides(tile.xy), piece_id)]
    moves = []
    tiles = gameboard.get_tiles("xy", choords)

    if len(choords) >= 1:
        if mustopen:
            for i in range(len(tiles) - 1, -1, -1):
                if (
                    not tiles[i] is None
                    and not tiles[i] == ""
                    and tiles[i].is_open()
                ):
                    continue
                del tiles[i]
        moves = [tile.id for tile in tiles]
    # Add in valid moves from jumping
    jumps = []
    if not piece_id is None:
        jumps, _ = get_jumps(gameboard, piece_id, tile)
    for jump in jumps:
        if not jump in moves:
            moves.append(jump)

    return tuple(moves)


def check_for_win(gameboard: GameBoard) -> int | None:
    "Checks a gameboard for wins, returns the player number if there is one, otherwise return None"
    # Get all the tiles pieces can be on, in this case black tiles
    tiles = gameboard.tiles.values()
    # For each of the two players,
    for player in range(2):
        # Get that player's possible pieces
        player_pieces = {player, player + 2}
        # For each tile in the playable tiles,
        for tile in tiles:
            # If the tile's piece is one of the player's pieces,
            if tile.piece in player_pieces:
                if get_moves(gameboard, tile.piece, tile):
                    # Player has at least one move, no need to continue
                    break
        else:
            # Continued without break, so player either has no moves
            # or no possible moves, so their opponent wins
            return (player + 1) % 2
    return None


class Tile:
    "Object for storing data about tiles"

    def __init__(
        self,
        board: GameBoard,
        tile_id: str,
        location: Vector2,
        color: int,
        xy: tuple[int, int],
    ) -> None:
        # Store data about the game board, what tile id we are, where we live, what color we are, xy positions, basic stuff.
        self.board = board
        self.id = tile_id
        self.location = Vector2(*location)
        self.color = color
        self.xy = xy
        # We shouldn't have any pieces on us
        self.piece = None
        # Get the width and height of self
        wh = [self.board.tile_size] * 2
        # Get our location x and y, width, and height for collison later
        self.xywh = (self.location[0], self.location[1], wh[0], wh[1])
        # Set up how long untill we can be clicked again
        self.click_delay = 0.1
        # We are not clicked
        self.click_time = 0
        # We are not selected
        self.selected = False
        # We are not glowing
        self.glowing = False
        # We don't know what the cursor's id is
        self.cursor_id = None
        # We don't know if we have any valid moves or jumps
        self.moves = None
        self.jumps = None

    def __repr__(self) -> str:
        return f"<Tile {self.id} {self.location} {self.color} {self.xy}>"

    def get_data(self) -> dict[str, int | str | bool | list[Any] | tuple[Any]]:
        "Returns a dictionary of important data that is safe to send to an AI"
        # Set up the dictionary we're going to send
        send = {}
        # Send if this tile is open
        send["open"] = bool(self.piece is None)
        # Send this tile's piece
        send["piece"] = str(self.piece)
        # If we're an open tile,
        if self.is_open() or self.moves is None:
            # We have no jumps or moves to send
            send["moves"] = []
            send["jumps"] = [[], {}]
        else:
            # Otherwise, send the jumps and moves our piece can make
            send["moves"] = list(self.moves)
            send["jumps"] = list(self.jumps)
        # Send our xy position
        send["xy"] = tuple(self.xy)
        # Send our color value
        send["color"] = int(self.color)
        # send['id'] = str(self.id)
        # No telling id required, board's dictionary has our id as the key.
        # Send the dictionary
        return send

    def get_cursor(self) -> Cursor | None:
        "Gets the cursor from the world and returns it"
        # If the cursor's id has not been found,
        if self.cursor_id is None:
            # Tell the world to find an entity with the name of 'cursor'
            cursor = self.board.world.get_type("cursor")
            # If the world found anything and there is at least one cursor entity,
            if len(cursor):
                # Set what we should return to the first (and in regular cases the only) cursor entity
                cursor = cursor[0]
                if cursor is not None:
                    self.cursor_id = cursor.id
                    return cursor
            # Return None if the world didn't find any matches
            return None
        # If the cursor's id has been found, get the cursor from the world
        cursor = self.board.world.get(self.cursor_id)
        # If the cursor does not exist anymore/was moved to a different id,
        if cursor is None:
            # We no longer know the true id of the cursor
            self.cursor_id = None
            # Re-find the cursor
            return self.get_cursor()
        return cursor

    def get_pressed(self) -> bool:
        "Return True if the cursor is over tile and right click down"
        # Get the cursor
        cursor = self.get_cursor()
        # If the cursor exists,
        if not cursor is None:
            # See if the right mouse button is down
            if cursor.get_pressed():
                # If it is, see if the cursor is over our image
                point_x, point_y = self.board.convert_loc(cursor.location)
                x, y, w, h = self.xywh

                in_x = point_x >= x and point_x < x + w
                in_y = point_y >= y and point_y < y + h
                # If it is, this will return True
                return in_x and in_y
        # Otherwise, return False
        return False

    def is_open(self) -> bool:
        "Return True if tile is empty"
        return self.piece is None

    def set_glowing_tiles(self, tf: bool) -> None:
        "Sets the glowing state of tiles our piece can move to"
        if self.moves:
            for tile in (self.board.tiles[tid] for tid in self.moves):
                tile.glowing = bool(tf)

    def update_moves(self) -> None:
        "Update self.moves and self.jumps if either are equal to None"
        n = lambda x: x is None
        if n(self.moves) or n(self.jumps):
            if not self.is_open():
                self.moves = get_moves(self.board, self.piece, self)
                self.jumps = get_jumps(self.board, self.piece, self)
            else:
                self.moves = []
                self.jumps = []

    def process(self, time_passed: float) -> None:
        "Do stuff like tell the cursor to carry pieces and drop them and click time and crazyness"
        # Find out if we've been pressed
        pressed = self.get_pressed()
        # Get the cursor
        cursor = self.get_cursor()
        # Update moves and jumps lists
        self.update_moves()
        # Process if we've been selected
        # If we are selected and haven't been clicked recently,
        if (
            pressed
            and not self.click_time
            and (
                self.is_open()
                or self.piece in ({1, 3}, {0, 2}, ())[self.board.playing]
            )
        ):
            # Toggle selected
            self.selected = not self.selected
            # If the cursor exists,
            if not cursor is None:
                # If we are now selected
                if self.selected:
                    # If we have a piece on us
                    if not self.is_open():
                        # If the cursor is not carrying a piece,
                        if not cursor.is_carry():
                            # Tell the cursor to carry our piece
                            cursor.drag(self, self.board.piece_map[self.piece])
                            # Get the tiles our piece can move to and make them glow
                            self.set_glowing_tiles(True)
                        else:
                            # If cursor is carrying a piece and have a piece
                            # Otherwise, we shouldn't be selected
                            self.selected = False
                    else:  # If we don't have a piece on us,
                        # If we are a black tile, tell the cursor to drop the piece it's carrying onto us if it's carrying a piece
                        if not self.color and cursor.is_carry():
                            # If this move is a valid move,
                            if self.id in cursor.carry_tile.moves:
                                # Set the valid tiles glowing effect to false
                                cursor.carry_tile.set_glowing_tiles(False)
                                # Move the piece
                                cursor.carry_tile.move_piece(self.id)
                                # In either case, tell the cursor to drop it's image
                                cursor.drop()
                        self.selected = False
                else:  # If we are now not selected,
                    # If the cursor is carrying our piece and we've been un-selected, tell the cursor to give our piece back.
                    if cursor.is_carry() and cursor.carry_tile.id == self.id:
                        cursor.drop()
                        self.set_glowing_tiles(False)
        else:
            # If we have been clicked recently, decement the time variable that tells us we were clicked recently
            self.click_time = max(self.click_time - time_passed, 0)
        if pressed:
            # If we have been clicked just now, reset the time variable that tells us we've been clicked recently
            self.click_time = self.click_delay

    def is_selected(self) -> bool:
        "Return True if we are selected"
        return self.selected

    def is_glowing(self) -> bool:
        "Return True if we are glowing"
        return self.glowing

    def king_piece(self, piece_id: int) -> int:
        "Return piece_id after piece has made it to this tile."
        # If the piece has made it to the opposite side,
        if (piece_id == 0 and self.id[1] == "8") or (
            piece_id == 1 and self.id[1] == "1"
        ):
            # King that piece
            piece_id += 2
        return piece_id

    def play(self, piece_id: int) -> None:
        "If tile is empty, set piece to piece id"
        # If we have no pieces on us,
        if self.is_open():
            # Clear any stray, random data still stored within us
            self.clear_moves()
            # Put the piece on us
            self.piece = self.king_piece(piece_id)

    def clear(self) -> None:
        "Clear tile of any pieces"
        # Delete any pieces that are on us.
        self.piece = None
        # Clear piece information
        self.clear_moves()

    def clear_moves(self) -> None:
        "Clear the jumps and moves information"
        self.moves = None
        self.jumps = None

    def reevaluate_moves(self) -> None:
        "Called by the game board when moves should be re-evaluated"
        self.clear_moves()
        self.update_moves()

    def move_piece(self, tolocid: str) -> None:
        "Return true if successfully moved piece from self to target tile"
        # Get the target tile from the game board
        target = self.board.tiles[tolocid]
        # If the target tile has no piece on it and it's a valid move,
        if target.is_open() and tolocid in self.moves:
            # Get the moves that are jumps and the dictionary that has jumped piece tile ids in it
            jump_moves, jumped = self.jumps
            # If the destination is a jump,
            if tolocid in jump_moves:
                # For each tile with a piece that got jumped in it,
                for tileid in jumped[tolocid]:
                    # Get the tile from the gameboard and clear it.
                    tile = self.board.tiles[tileid]
                    tile.clear()
                    self.piece = tile.king_piece(self.piece)
                    # self.board.tiles[tileid].play(self.piece)
                    # self.piece = self.board.tiles[tileid].piece
                    # self.board.tiles[tileid].clear()
            # Play our piece onto target tile
            target.play(self.piece)
            # We just played our piece to the target tile, we shouldn't have it anymore
            self.clear()
            # Niether of us are selected, we just made a play
            self.selected = False
            target.selected = False
            # Also set the target's glowing value to false if it was glowing
            target.glowing = False
            # Tell the board that the current player's turn is over
            self.board.turn_over()


class GameBoard(GameEntity):
    "Entity that stores data about the game board and renders it"

    def __init__(
        self, world: World, board_size: int, tile_size: int, **kwargs: Any
    ) -> None:
        # Make a blank surface of the proper size by multiplying the board size by the tile size
        image = pygame.Surface(to_int(amol(board_size, m=tile_size)))
        # Fill the blank surface with green so we know if anything is broken/not updating
        image.fill(GREEN)
        super().__init__(world, "board", image, **kwargs)

        # Define Tile Color Map and Piece Map
        self.tile_color_map = [BLACK, RED]
        red = (160, 0, 0)
        black = [
            127
        ] * 3  # Define Black Pawn color to be more of a dark grey so you can see it
        # Define each piece by giving what color it should be and an image to recolor
        self.piece_map = [
            [red, "Pawn"],
            [black, "Pawn"],
            [red, "King"],
            [black, "King"],
        ]

        # Store the Board Size and Tile Size
        self.board_size = to_int(board_size)
        self.tile_size = int(tile_size)

        # Convert Tile Color Map and Piece Map into Dictionarys
        self.tile_color_map = {
            i: self.tile_color_map[i] for i in range(len(self.tile_color_map))
        }
        self.piece_map = {
            i: self.piece_map[i] for i in range(len(self.piece_map))
        }

        # Generate Tile Surfaces for each color of tile stored in the Tile Color Map Dictionary
        self.tile_surfs = {
            color_id: self.gen_tile_surf(
                self.tile_color_map[color_id], [self.tile_size] * 2
            )
            for color_id in self.tile_color_map.keys()
        }

        # Generate a Pice Surface for each piece using a base image and a color
        self.piece_map = {
            i: replace_with_color(
                pygame.transform.scale(
                    IMAGES[self.piece_map[i][1]], [tile_size] * 2
                ),
                self.piece_map[i][0],
            )
            for i in range(len(self.piece_map))
        }

        # Generate tile data
        self.gen_tiles()

        # Set playing side
        self.playing = randint(0, 1)

        # No one has won.
        self.won = None

    def render(self, surface: Surface) -> None:
        "Generates the board surface and blits it to surface"
        # Generate the board surface and store it as self.image
        self.image = self.gen_board_surf()
        # Render self.image in the correct location on the screen
        super().render(surface)

    def process(self, time_passed: float) -> None:
        "Processes the game board and each of it's tiles and pieces"
        # Process the GameEntity part of self, which really doesn't do anything since the board doesn't move
        GameEntity.process(self, time_passed)

        # For each tile,
        for tile in iter(self.tiles.values()):
            # Process mouse clicks and stuff
            tile.process(time_passed)

    def get_data(self) -> dict[str, str | tuple[int, int] | dict[str, Any]]:
        "Returns imporant data that is safe to send to an AI"
        # Set up the dictionary we're going to send
        send = {}
        # Send the game board size
        send["board_size"] = tuple(self.board_size)
        # Send who's won the game
        send["won"] = str(self.won)
        # Send all tile data
        send["tiles"] = {
            tile.id: tile.get_data() for tile in self.tiles.values()
        }
        # Send the dictionary
        return send

    def gen_tile_surf(
        self,
        color: Color
        | int
        | str
        | tuple[int, int, int]
        | tuple[int, int, int, int]
        | Sequence[int],
        size: list[int],
    ) -> Surface:
        "Generate the image used for a tile"
        # Make a blank surface of the size we're given
        surf = pygame.Surface(to_int(size))
        # Fill the blank surface with the color given
        surf.fill(color)
        # Return a rectangular (or square if width and height of size are the same) image of the color given
        return surf

    def outline_surf(
        self, surface: Surface, color: tuple[int, int, int]
    ) -> Surface:
        "Add an outline of a given color to a surface"
        # Get the size of the surface
        w, h = surface.get_size()
        # Replace all color on the image with the color
        surf = replace_with_color(surface, color)
        # Get 90% of the width and height
        inside = round_all(amol([w, h], m=0.90))
        # Make the surface be 90% of it's size
        inside_surf = pygame.transform.scale(surface, inside)
        # Get the proper position the modified image should be at
        pos = amol(list(Vector2(w, h) - Vector2(*inside)), d=2)
        # Add the modified image to the correct location
        surf.blit(inside_surf, to_int(pos))
        # Return image with yellow outline
        return surf

    def gen_tiles(self) -> None:
        "Generate data about each tile"
        # Reset tile data
        self.tiles = {}
        location = Vector2(0, 0)
        # Get where pieces should be placed
        z_to_1 = round(self.board_size[1] / 3)  # White
        z_to_2 = (self.board_size[1] - (z_to_1 * 2)) + z_to_1  # Black
        # For each xy position in the area of where tiles should be,
        for y in range(self.board_size[1]):
            # Reset the x pos to 0
            location.x = 0
            for x in range(self.board_size[0]):
                # Get the proper name of the tile we're creating ('A1' to 'H8')
                name = chr(65 + x) + str(self.board_size[1] - y)
                # Get the color of that spot by adding x and y mod the number of different colors
                color = (x + y) % len(self.tile_surfs.keys())
                # Create the tile
                tile = Tile(self, name, location, color, (x, y))
                # If a piece should be placed on that tile and the tile is not Red,
                if (not color) and ((y <= z_to_1 - 1) or (y >= z_to_2)):
                    # Set the piece to White Pawn or Black Pawn depending on the current y pos
                    tile.piece = {True: 1, False: 0}[y <= z_to_1]
                # Add the tile to the tiles dictionary with a key of it's name ('A1' to 'H8')
                self.tiles[name] = tile
                # Increment the x counter by tile_size
                location.x += self.tile_size
            # Increment the y counter by tile_size
            location.y += self.tile_size

    def get_tile(self, by: str, value: object) -> Tile | None:
        "Get a spicific tile by an atribute it has, otherwise return None"
        by = str(by)
        # For each tile on the game board,
        for tile in self.tiles.values():
            # See if the tile has the attribute we're looking at, and if it does see if it matches value
            if hasattr(tile, by) and getattr(tile, by) == value:
                # If it's a match, return that tile
                return tile
        # Otherwise return None
        return None

    def get_tiles(self, by: str, values: Collection[object]) -> list[object]:
        "Gets all tiles whos attribute of by is in value, and if there are no matches return None"
        by = str(by)
        matches = []
        # For each tile on the game board,
        for tile in self.tiles.values():
            # See if it has the attribute we're looking for, and if it does have it, see if it's a match to the given value.
            if hasattr(tile, by) and getattr(tile, by) in values:
                # If it's a match, add it to matches
                matches.append(tile)
        if matches:
            # Return all tiles that matched our query
            return matches
        # Otherwise return None in a list
        return [None]

    def gen_board_surf(self) -> Surface:
        "Generate an image of a game board"
        location = Vector2(0, 0)
        # Get a surface the size of everything
        surf = pygame.Surface(amol(self.board_size, m=self.tile_size))
        # Fill it with green so we know if anything is broken
        surf.fill(GREEN)
        # For each tile xy choordinate,
        for y in range(self.board_size[1]):
            for x in range(self.board_size[0]):
                # Get the correct tile at that position
                tile = self.tiles[chr(65 + x) + str(self.board_size[1] - y)]
                # Get the color id of the tile, and get the tile surface that corrolates to that id
                tile_image = self.tile_surfs[tile.color]
                # If the tile has no piece on it and it's selected,
                if tile.piece is None and tile.is_selected():
                    # Make the tile have a yellow outline to indicate it's selected
                    tile_image = self.outline_surf(tile_image, YELLOW)
                if tile.is_glowing():
                    # Make the tile glow blue
                    tile_image = self.outline_surf(tile_image, BLUE)
                # Blit the tile image to the surface at the tile's location
                surf.blit(tile_image, tile.location)
                # If the tile does have a piece on it,
                if not tile.piece is None:
                    # Get the piece surface that corrolates to that piece id
                    piece = self.piece_map[tile.piece]
                    # If the tile is also selected,
                    if tile.is_selected():
                        # Add a yellow outline to the piece to indicate it's selected
                        piece = self.outline_surf(piece, YELLOW)
                    # Blit the piece to the surface at the tile's location
                    surf.blit(piece, tile.location)
        ##                # Blit the id of the tile at the tile's location
        ##                value = "".join(to_str(tile.xy))
        ##                # value = tile.id
        ##                blit_text(
        ##                    "VeraSerif.ttf",
        ##                    20,
        ##                    value,
        ##                    GREEN,
        ##                    tile.location,
        ##                    surf,
        ##                    False,
        ##                )
        return surf

    def convert_loc(self, location: Vector2) -> Vector2:
        "Converts a screen location to a location on the game board like tiles use"
        # Get where zero zero would be in tile location data,
        zero = self.location - Vector2(*amol(self.image.get_size(), d=2))
        # and return the given location minus zero zero to get tile location data
        return Vector2(*location) - zero

    def turn_over(self) -> None:
        "Called when a tile wishes to communicate that the current player's turn is over"
        # Toggle the active player
        self.playing = (self.playing + 1) % 2
        # Tell all tiles to re-evaluate their move information
        for tile in iter(self.tiles.values()):
            tile.reevaluate_moves()

        # If no one has won,
        if self.won is None:
            # Check for wins
            win = check_for_win(self)
            # If someone has won,
            if not win is None:
                # Don't let anybody move
                self.playing = 2
                # The winner is the person check_for_win found.
                self.won = win


def show_win(valdisplay: "ValDisplay") -> str:
    "Called when the value display requests text to render"
    # Get the board
    boards = valdisplay.world.get_type("board")
    if len(boards):
        board = boards[0]
    else:
        # If the board not exist, nothing to return
        return ""
    # If the game has been won,
    if not board.won is None:
        # show that
        return f"{PLAYERS[board.won]} Won!"
    return ""


class ValDisplay(GameEntity):
    "Entity that displays the value of a string returned by calling value_function(self)"

    def __init__(
        self,
        world: World,
        font_name: str,
        font_size: int,
        value_function,
        **kwargs: Any,
    ) -> None:
        GameEntity.__init__(self, world, "valdisplay", None, **kwargs)
        # Store the font __title__, font size, and value function
        self.font_name = str(font_name)
        self.font_size = int(font_size)
        self.value = value_function
        # By default text is not centered
        self.centered = True
        # By default text is black
        self.color = BLACK

        # Read keyword arguments and act on them appropriately.
        if "centered" in kwargs.keys():
            self.centered = bool(kwargs["centered"])
        if "color" in kwargs.keys():
            self.color = tuple(kwargs["color"])
        if "renderPriority" in kwargs.keys():
            self.render_priority = kwargs["renderPriority"]

    def render(self, surface: Surface) -> None:
        "Render text and blit it to surface"
        blit_text(
            self.font_name,
            self.font_size,
            str(self.value(self)),
            self.color,
            self.location,
            surface,
            middle=self.centered,
        )


class Button(BaseButton):
    "Button that only shows when a player has won the game"

    def __init__(
        self, world: World, anim, trigger, action, states: int = 0, **kwargs
    ):
        super().__init__(world, anim, trigger, action, states, **kwargs)
        self.do_reset = True
        self.anim_flip = False

    def process(self, time_passed: float) -> None:
        "Does regular button processing AND makes it so button only shows when the game has been won"
        # Do regular button processing
        BaseButton.process(self, time_passed)
        # Get the game board
        boards = self.world.get_type("board")
        if len(boards):
            board = boards[0]
            # Show if the game has been won
            self.show = not board.won is None
        if not self.do_reset and not self.anim_flip:
            self.anim = [i for i in reversed(self.anim)]
            self.anim_flip = True


def back_pressed(button: Button) -> None:
    "This function is called when the back buttons is pressed"
    global RUNNING
    boards = button.world.get_type("board")
    # Get the game board from the world
    if len(boards):
        board = boards[0]
        # If the game is won and this button is pressed,
        if board.won is not None and button.do_reset:
            # Reset the game board
            board.gen_tiles()  # Reset all tiles to defaults
            board.won = None  # No one has won
            board.playing = randint(0, 1)  # Player who can play now is random
        if not button.do_reset:
            RUNNING = False


def gen_button(text: str, size: int) -> Surface:
    "Generates a button surface by rendering text with size onto the base button image"
    base_image = IMAGES["button"]
    button_image = scale_surf(base_image, 4)
    xy = amol(button_image.get_size(), d=2)
    blit_text("VeraSerif.ttf", size, text, GREEN, xy, button_image)
    return button_image


def ai_play(target_tile_id: str, to_tile_id: str, board: GameEntity) -> bool:
    "Does pretty much everything that tiles and the cursor do to move a piece combined without visuals"
    # If the target tile id or destination tile id is not valid, return False
    if (target_tile_id not in board.tiles) or (to_tile_id not in board.tiles):
        return False
    # Get the target tile from the game board
    target_tile = board.tiles[target_tile_id]
    # Get the destination tile from the game board
    to_tile = board.tiles[to_tile_id]
    # If the target's piece is one of the black team's pieces,
    if target_tile.piece in (1, 3):
        # If the destination tile is a playable tile,
        if not to_tile.color and to_tile.is_open():
            if target_tile.moves is None:
                target_tile.reevaluate_moves()
            # If the destination tile id is one of the target tile's valid moves,
            if to_tile_id in target_tile.moves:
                # Move the target piece to the destination
                target_tile.move_piece(to_tile_id)
                # Return True
                return True
    return False


def load_ai(name: str) -> None:
    "Imports ai and calls AI.init()"
    # If the ai __title__ is valid,
    if name in find_ais():
        # Copy the ai's file to a temporary file
        global AI, aiData
        AI = __import__(name)
        # If the AI has an init command,
        if hasattr(AI, "init"):
            # Run it and get any special options the AI wants to run.
            aiData = AI.init()
        else:
            aiData = None


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


def play_ai() -> bool:
    "If there are AI modules, ask the user if they would like to play one and load it if so"
    ais = find_ais()
    if ais:
        print("\nAI Files found in this folder!")
        print("Would you like to play against an AI?")
        inp = input("(y / n) : ").lower()
        if inp in ("y"):
            print("\nList of AIs:")
            for index, name in enumerate(ais, 1):
                print(f"{index} : {name}")
            print("\nWhich AI would you like to play against?")
            inp = input(f"(Number between 1 and {len(ais)}) : ")
            if inp.isalnum():
                num = abs(int(inp) - 1) % len(ais)
                load_ai(ais[num])
                return True
            print("Answer is not a number. Starting two player game.")
            return False
    print("Starting two player game.")
    return False


def run() -> None:
    "Main loop of everything"
    print(f"{__title__} {__version__}")
    computer = play_ai()
    # Set up globals
    global IMAGES, PLAYERS, aiData, RUNNING
    # Initialize Pygame
    pygame.init()

    # Set up the screen
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 16)
    pygame.display.set_caption(__title__ + " " + __version__)

    # Set up the FPS clock
    clock = pygame.time.Clock()

    # Get the program path, and use it to find the picture path
    PROGPATH = os.path.split(os.sys.argv[0])[0]
    picpath = os.path.join(PROGPATH, PIC_PATH)

    # Get all picture filenames
    pics = os.listdir(picpath)

    # Create a dictionary containing the image surfaces
    IMAGES = {}
    for pic_name in pics:
        name = pic_name.split(".png")[0]
        image = pygame.image.load(picpath + pic_name).convert_alpha()
        IMAGES[name] = scale_surf(image, 0.25)

    # Get any additional images
    background = pygame.Surface(SCREEN_SIZE)
    background.fill(WHITE)

    # Define animations
    backAnim = [gen_button("Play Again", 35), gen_button("Quit Game", 35)]

    # Set up the world
    world = World(background)

    # Set up players
    if computer:
        PLAYERS = ["Player", "Computer"]
        if aiData and hasattr(aiData, "keys"):
            keys = aiData.keys()
            if "player_names" in keys:
                if len(aiData["player_names"]) == 2:
                    PLAYERS = to_str(list(aiData["player_names"]))
    else:
        PLAYERS = ["Red Player", "Black Player"]

    # Get the screen width and height for a lot of things
    w, h = SCREEN_SIZE

    # Add entities
    world.add_entity(Cursor(world))
    world.add_entity(
        GameBoard(world, [8] * 2, 45, location=amol(SCREEN_SIZE, d=2))
    )
    world.add_entity(
        ValDisplay(
            world,
            "VeraSerif.ttf",
            60,
            show_win,
            location=amol(SCREEN_SIZE, d=2),
            color=GREEN,
            renderPriority=5,
        )
    )
    world.add_entity(
        Button(
            world,
            backAnim,
            "cursor",
            back_pressed,
            states=1,
            location=Vector2(*amol(SCREEN_SIZE, d=2)) + Vector2(0, 80),
        )
    )

    if computer and hasattr(aiData, "keys"):
        keys = aiData.keys()
        if "starting_turn" in keys:
            world.get_type("board")[0].playing = int(aiData["starting_turn"])
        if "must_quit" in keys:
            world.get_type("button")[0].do_reset = not bool(
                aiData["must_quit"]
            )

    ai_has_been_told_game_is_won = False

    # System is running
    RUNNING = True

    # While the game is active
    while RUNNING:
        # Event handler
        for event in pygame.event.get():
            if event.type == QUIT:
                RUNNING = False

        # Update the FPS clock and get how much time elapsed since the last frame
        time_passed = clock.tick(FPS)

        # Process entities
        world.process(time_passed)

        # Render the world to the screen
        world.render(screen)

        # If we are playing against a computer,
        if computer:
            # Get the game board from the world
            boards = world.get_type("board")
            # If there are game board(s) the world found,
            if boards:
                # Get the first one
                board = boards[0]
                # If it's the AI's turn,
                if board.playing == 0:
                    # Reset game is won tracker since presumabley a new game has started
                    if ai_has_been_told_game_is_won:
                        ai_has_been_told_game_is_won = False
                    try:
                        # Send board data to the AI
                        AI.update(board.get_data())
                        # Get the target piece id and destination piece id from the AI
                        rec_data = AI.turn()
                        if rec_data != "QUIT":
                            if rec_data is not None:
                                target, dest = rec_data
                                # Play play the target piece id to the destination tile id
                                # on the game board
                                success = ai_play(
                                    str(target), str(dest), board
                                )
                                if hasattr(AI, "turn_success"):
                                    AI.turn_success(bool(success))
                            # else:
                            #     print('AI Played None. Still AI\'s Turn.')
                        else:
                            # Don't use this as an excuse if your AI can't win
                            print(
                                "AI wishes to hault execution. Exiting game."
                            )
                            RUNNING = False
                    except Exception as ex:
                        traceback.print_exception(ex)
                        RUNNING = False
                elif board.playing == 2 and not ai_has_been_told_game_is_won:
                    # If the game has been won, tell the AI about it
                    AI.update(board.get_data())
                    ai_has_been_told_game_is_won = True
        # Update the display
        pygame.display.update()
    pygame.quit()
    # If we have an AI going and it has the stop function,
    if computer and hasattr(AI, "stop"):
        # Tell the AI to stop
        AI.stop()


if __name__ == "__main__":
    # If we're not imported as a module, run.
    run()
