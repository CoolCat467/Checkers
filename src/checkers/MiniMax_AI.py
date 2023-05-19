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

##    # Below is an example of empty board data that would be sent with an empty board to this ai
##    emptyboard_data = {'boardsize': (8, 8),
##                      'won': 'None',
##                      'tiles': {
##                          'A8': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (0, 0), 'color': 0},
##                          'B8': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 0), 'color': 1},
##                          'C8': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (2, 0), 'color': 0},
##                          'D8': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 0), 'color': 1},
##                          'E8': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (4, 0), 'color': 0},
##                          'F8': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 0), 'color': 1},
##                          'G8': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (6, 0), 'color': 0},
##                          'H8': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 0), 'color': 1},
##                          'A7': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 1), 'color': 1},
##                          'B7': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (1, 1), 'color': 0},
##                          'C7': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 1), 'color': 1},
##                          'D7': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (3, 1), 'color': 0},
##                          'E7': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 1), 'color': 1},
##                          'F7': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (5, 1), 'color': 0},
##                          'G7': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 1), 'color': 1},
##                          'H7': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (7, 1), 'color': 0},
##                          'A6': {'open': False, 'piece': '1', 'moves': ['B5'], 'jumps': [[], {}], 'xy': (0, 2), 'color': 0},
##                          'B6': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 2), 'color': 1},
##                          'C6': {'open': False, 'piece': '1', 'moves': ['B5', 'D5'], 'jumps': [[], {}], 'xy': (2, 2), 'color': 0},
##                          'D6': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 2), 'color': 1},
##                          'E6': {'open': False, 'piece': '1', 'moves': ['D5', 'F5'], 'jumps': [[], {}], 'xy': (4, 2), 'color': 0},
##                          'F6': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 2), 'color': 1},
##                          'G6': {'open': False, 'piece': '1', 'moves': ['F5', 'H5'], 'jumps': [[], {}], 'xy': (6, 2), 'color': 0},
##                          'H6': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 2), 'color': 1},
##                          'A5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 3), 'color': 1},
##                          'B5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 3), 'color': 0},
##                          'C5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 3), 'color': 1},
##                          'D5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 3), 'color': 0},
##                          'E5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 3), 'color': 1},
##                          'F5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 3), 'color': 0},
##                          'G5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 3), 'color': 1},
##                          'H5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 3), 'color': 0},
##                          'A4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 4), 'color': 0},
##                          'B4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 4), 'color': 1},
##                          'C4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 4), 'color': 0},
##                          'D4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 4), 'color': 1},
##                          'E4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 4), 'color': 0},
##                          'F4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 4), 'color': 1},
##                          'G4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 4), 'color': 0},
##                          'H4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 4), 'color': 1},
##                          'A3': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 5), 'color': 1},
##                          'B3': {'open': False, 'piece': '0', 'moves': ['A4', 'C4'], 'jumps': [[], {}], 'xy': (1, 5), 'color': 0},
##                          'C3': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 5), 'color': 1},
##                          'D3': {'open': False, 'piece': '0', 'moves': ['C4', 'E4'], 'jumps': [[], {}], 'xy': (3, 5), 'color': 0},
##                          'E3': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 5), 'color': 1},
##                          'F3': {'open': False, 'piece': '0', 'moves': ['E4', 'G4'], 'jumps': [[], {}], 'xy': (5, 5), 'color': 0},
##                          'G3': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 5), 'color': 1},
##                          'H3': {'open': False, 'piece': '0', 'moves': ['G4'], 'jumps': [[], {}], 'xy': (7, 5), 'color': 0},
##                          'A2': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (0, 6), 'color': 0},
##                          'B2': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 6), 'color': 1},
##                          'C2': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (2, 6), 'color': 0},
##                          'D2': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 6), 'color': 1},
##                          'E2': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (4, 6), 'color': 0},
##                          'F2': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 6), 'color': 1},
##                          'G2': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (6, 6), 'color': 0},
##                          'H2': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 6), 'color': 1},
##                          'A1': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 7), 'color': 1},
##                          'B1': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (1, 7), 'color': 0},
##                          'C1': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 7), 'color': 1},
##                          'D1': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (3, 7), 'color': 0},
##                          'E1': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 7), 'color': 1},
##                          'F1': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (5, 7), 'color': 0},
##                          'G1': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 7), 'color': 1},
##                          'H1': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (7, 7), 'color': 0}
##                          }
##                      }


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
        new = class_(self.size, not self.turn, pieces_copy)
        ##        if jump:
        ##            print(f"\n\nBefore Jump:\n{self}\nAfter Jump:\n{new}\n")
        return new

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
    __slots__ = ()

    def value(self, state: State) -> int | float:
        win = state.check_for_win()
        if win is None:
            counts = Counter(state.pieces.values())
            min_ = counts[0] + 3 * counts[2]
            max_ = counts[1] + 3 * counts[3]
            value = (max_ - min_) / (max_ + min_)
            ##            if value != 0:
            ##                print(state)
            ##                print(f'{value = }')
            return value
        return win * 2 - 1

    def terminal(self, state: State) -> bool:
        return state.check_for_win() is not None

    def player(self, state: State) -> Player:
        return Player.MAX if state.get_turn() else Player.MIN

    def actions(self, state: State) -> Iterable[Action]:
        return state.get_all_actions(int(state.get_turn()))

    def result(self, state: State, action: Action) -> State:
        return state.preform_action(action)

    def adaptive_depth_minimax(
        self, state: State, minimum: int
    ) -> MinimaxResult:
        current = len(state.pieces.values())
        w, h = state.size
        max_count = w * h // 6 << 1
        depth = (1 - (current / max_count)) * math.floor(
            math.sqrt(w**2 + h**2)
        )
        final_depth = math.floor(max(minimum, depth))
        print(f"{final_depth = }")
        return self.minimax(state, final_depth)


def turn() -> tuple[str, str] | None:
    "This function is called when the game requests the AI to return the piece it wants to move's id and the tile id the target piece should be moved to."
    minimax = CheckersMinimax()
    value, action = minimax.adaptive_depth_minimax(CURRENT_STATE, 4)
    print(repr(CURRENT_STATE))
    assert isinstance(action, tuple)
    from_, to_ = action
    assert isinstance(from_, str)
    assert isinstance(to_, str)
    print(f"{value = } {action = }")
    return from_, to_


def turn_success(tf: bool) -> None:
    "This function is called immidiately after the ai's play is made, telling it if it was successfull or not"
    if not tf:
        print("AI: Something went wrong playing move...")


def stop() -> None:
    "This function is called immidiately after the game's window is closed"
    pass


def init() -> dict[str, object]:
    "This function is called immidiately after the game imports the AI"
    return {
        "player_names": ("Player", "Minimax"),
    }


print("AI: AI Module Loaded")
print("AI: " + __title__ + " Created by " + __author__)
