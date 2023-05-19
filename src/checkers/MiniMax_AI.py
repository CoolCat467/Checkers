#!/usr/bin/env python3
# AI that plays checkers.

# IMPORTANT NOTE:
# For the game to recognize this as an
# AI, it's filename should have the words
# 'AI' in it.

__title__ = "Minimax AI"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import math
from collections import Counter, namedtuple
from collections.abc import Generator, Iterable
from typing import Any, Self, TypeVar

from minimax import Minimax, MinimaxResult, Player

T = TypeVar("T")


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


def pawn_modify(moves: list[T], piece_type: int) -> list[T]:
    "Modifies a list based on piece id to take out invalid moves for pawns"
    assert (
        len(moves) == 4
    ), "List size MUST be four for this to return valid results!"
    if (
        piece_type == 0
    ):  # If it's a white pawn, it can only move to top left and top right
        moves = moves[:2]
    if (
        piece_type == 1
    ):  # If it's a black pawn, it can only move to bottom left anf bottom right
        moves = moves[2:]
    return moves


# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3

Action = namedtuple("Action", ("from_pos", "to_pos"))


class State:
    """Represents state of checkers game"""

    __slots__ = ("size", "turn", "pieces")

    def __init__(
        self,
        size: tuple[int, int],
        turn: bool,
        pieces: dict[tuple[int, int], int],
    ) -> None:
        self.size = size
        self.turn = turn
        self.pieces = pieces

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.size}, {self.turn}, {self.pieces})"

    def __str__(self) -> str:
        map_ = {None: " ", 0: "-", 1: "+", 2: "O", 3: "X"}
        w, h = self.size
        lines = []
        for y in range(h):
            line = []
            for x in range(w):
                if (x + y) % 2:
                    line.append("_")
                    continue
                line.append(map_[self.pieces.get((x, y))])
            lines.append("".join(line))
        ##            lines.append(" | ".join(line))
        ##            lines.append("--+-"*(w-1)+"-")
        return "\n".join(lines)

    @classmethod
    def from_game_board(cls, board_data: dict[str, Any]) -> Self:
        size = board_data.get("boardsize", (8, 8))
        turn = True
        pieces = cls.get_pieces_from_tiles(board_data.get("tiles", {}))
        return cls(size, turn, pieces)

    @staticmethod
    def get_pieces_from_tiles(
        tiles: dict[str, dict[str, Any]]
    ) -> dict[tuple[int, int], int]:
        """Convert board data from game to internal representation"""
        pieces: dict[tuple[int, int], int] = {}
        for tile_name, tile_data in tiles.items():
            piece_type = tile_data["piece"]
            if piece_type in {None, "None"}:
                continue
            x, y = tile_data["xy"]
            pieces[(x, y)] = int(piece_type)
        return pieces

    def preform_action(self, action: Action) -> Self:
        """Return new state after preforming action on self"""
        class_ = self.__class__
        from_pos_name, to_pos_name = action
        from_pos = self.get_tile_pos(from_pos_name)
        to_pos = self.get_tile_pos(to_pos_name)

        pieces_copy = dict(self.pieces.items())

        # Remove piece from it's start position
        piece_type = pieces_copy.pop(from_pos)

        # See if it kings and king it if so
        if self.does_piece_king(piece_type, to_pos):
            piece_type += 2

        # See if it's a jump
        if to_pos not in self.get_moves(from_pos):
            # Jumps are more complex to calculate and we need
            # to know what pieces got jumped over
            cur_x, cur_y = from_pos
            for jumped_pos in self.get_jumps(from_pos)[to_pos]:
                # Remove jumped position from pieces in play
                if jumped_pos in pieces_copy:
                    pieces_copy.pop(jumped_pos)
                # See if piece kinged
                jumped_x, jumped_y = jumped_pos
                # Rightshift 1 is more efficiant way to multiply by 2
                cur_x += (jumped_x - cur_x) << 1
                cur_y += (jumped_y - cur_y) << 1
                # Now that we know the current position, see if kinged
                if self.does_piece_king(piece_type, (cur_x, cur_y)):
                    piece_type += 2

        # Move piece to it's end position
        pieces_copy[to_pos] = piece_type

        # Swap turn
        return class_(self.size, not self.turn, pieces_copy)

    def get_tile_name(self, x: int, y: int) -> str:
        """Get name of a given tile"""
        return chr(65 + x) + str(self.size[1] - y)

    def get_tile_pos(self, name: str) -> tuple[int, int]:
        """Get tile position from it's name"""
        x = ord(name[0]) - 65
        y = self.size[1] - int(name[1:])
        return (x, y)

    def action_from_points(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> Action:
        """Return action from given start and end coordinates"""
        return Action(self.get_tile_name(*start), self.get_tile_name(*end))

    def get_turn(self) -> bool:
        """Return whose turn it is. True = AI (us)"""
        return self.turn

    def valid_location(self, position: tuple[int, int]) -> bool:
        """Return if position is valid"""
        x, y = position
        w, h = self.size
        return 0 <= x and 0 <= y and x < w and y < h

    def does_piece_king(
        self, piece_type: int, position: tuple[int, int]
    ) -> bool:
        """Return if piece needs to be kinged given it's type and position"""
        _, y = position
        _, h = self.size
        return (piece_type == 1 and y == 0) or (piece_type == 0 and y == h - 1)

    def get_jumps(
        self,
        position: tuple[int, int],
        piece_type: int | None = None,
        _recursion: int = 0,
    ) -> dict[tuple[int, int], list[tuple[int, int]]]:
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
        valid: dict[tuple[int, int], list[tuple[int, int]]] = {}

        # For each side tile in the jumpable tiles for this type of piece,
        for direction, side in pawn_modify(list(enumerate(sides)), piece_type):
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
            w, h = self.size
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
                    valid[end_pos] = valid[end_tile] + jumped_pieces

        return valid

    def get_moves(
        self, position: tuple[int, int]
    ) -> tuple[tuple[int, int], ...]:
        "Gets valid moves piece at position can make, not including jumps"
        piece_type = self.pieces[position]
        # Get the side xy choords of the tile's xy pos,
        # then modify results for pawns
        moves = pawn_modify(get_sides(position), piece_type)
        moves = [
            m
            for m in filter(self.valid_location, moves)
            if m not in self.pieces
        ]
        return tuple(moves)

    def get_actions(self, position: tuple[int, int]) -> list[Action]:
        """Return list of all moves and jumps the piece at position can make"""
        ends = set(self.get_jumps(position))
        ends.update(self.get_moves(position))
        return [self.action_from_points(position, end) for end in ends]

    def get_all_actions(self, player: int) -> Generator[Action, None, None]:
        """Yield all actions for given player"""
        player_pieces = {player, player + 2}
        for position, piece_type in self.pieces.items():
            if piece_type not in player_pieces:
                continue
            yield from iter(self.get_actions(position))

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
                    if self.get_actions(position):
                        # Player has at least one move, no need to continue
                        break
            else:
                # Continued without break, so player either has no moves
                # or no possible moves, so their opponent wins
                return (player + 1) % 2
        return None


CURRENT_STATE: State


def update(board_data: dict[str, Any]) -> None:
    "This function is called by the game to inform the ai of any changes that have occored on the game board"
    global CURRENT_STATE
    CURRENT_STATE = State.from_game_board(board_data)


class CheckersMinimax(Minimax[State, Action]):
    """Minimax Algorithm for Checkers"""

    __slots__ = ()

    @staticmethod
    def value(state: State) -> int | float:
        # Return winner if possible
        win = state.check_for_win()
        # If no winner, we have to predict the value
        if win is None:
            # We'll estimate the value by the pieces in play
            counts = Counter(state.pieces.values())
            # Score is pawns plus 3 times kings
            min_ = counts[0] + 3 * counts[2]
            max_ = counts[1] + 3 * counts[3]
            # More max will make score higher,
            # more min will make score lower
            # Plus one in divisor makes so never / 0
            return (max_ - min_) / (max_ + min_ + 1)
        return win * 2 - 1

    @staticmethod
    def terminal(state: State) -> bool:
        return state.check_for_win() is not None

    @staticmethod
    def player(state: State) -> Player:
        return Player.MAX if state.get_turn() else Player.MIN

    @staticmethod
    def actions(state: State) -> Iterable[Action]:
        return state.get_all_actions(int(state.get_turn()))

    @staticmethod
    def result(state: State, action: Action) -> State:
        return state.preform_action(action)

    @classmethod
    def adaptive_depth_minimax(
        cls, state: State, minimum: int, maximum: int
    ) -> MinimaxResult:
        current = len(state.pieces.values())
        w, h = state.size
        max_count = w * h // 6 << 1
        depth = (1 - (current / max_count)) * math.floor(
            math.sqrt(w**2 + h**2)
        )
        final_depth = math.floor(min(maximum, max(minimum, depth)))
        print(f"{final_depth = }")
        return cls.minimax(state, final_depth)


def turn() -> tuple[str, str] | None:
    "This function is called when the game requests the AI to return the piece it wants to move's id and the tile id the target piece should be moved to."
    print("\nAI brain data:")
    value, action = CheckersMinimax.adaptive_depth_minimax(CURRENT_STATE, 4, 5)
    print(f"Current State: {repr(CURRENT_STATE)}")
    assert isinstance(action, tuple)
    from_, to_ = action
    assert isinstance(from_, str)
    assert isinstance(to_, str)
    print(f"Next Move: {action}\nValue of move: {value}")
    return from_, to_


def turn_success(tf: bool) -> None:
    "This function is called immidiately after the ai's play is made, telling it if it was successfull or not"
    if not tf:
        print("AI: Something went wrong playing move...")


def stop() -> None:
    "This function is called immediately after the game's window is closed"
    pass


def init() -> dict[str, object]:
    "This function is called immidiately after the game imports the AI"
    return {
        "player_names": ("Player", "Minimax"),
    }


print(f"AI: AI Module {__title__} Created by {__author__}")
