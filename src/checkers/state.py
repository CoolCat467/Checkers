"""Checkers State"""

# Programmed by CoolCat467

__title__ = "Checkers State"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import math
from collections.abc import Generator
from typing import Any, NamedTuple, Self, TypeVar, cast

# Player:
# 0 = False = Red   = MIN = 0, 2
# 1 = True  = Black = MAX = 1, 3

# Note: Tile Ids are chess board tile titles, A1 to H8
# A8 ... H8
# .........
# A1 ... H1

T = TypeVar("T")

Pos = tuple[int, int]


class Action(NamedTuple):
    """Represents an action"""

    from_pos: Pos
    to_pos: Pos


class ActionSet(NamedTuple):
    """Represents a set of actions"""

    jumps: dict[Pos, list[Pos]]
    moves: tuple[Pos, ...]
    ends: set[Pos]


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


class State:
    """Represents state of checkers game"""

    __slots__ = ("size", "turn", "pieces", "pre_calculated_actions")

    def __init__(
        self,
        size: tuple[int, int],
        turn: bool,
        pieces: dict[Pos, int],
        /,
        pre_calculated_actions: dict[Pos, ActionSet] | None = None,
    ) -> None:
        self.size = size
        self.turn = turn
        self.pieces = pieces

        if pre_calculated_actions is None:
            pre_calculated_actions = {}
        self.pre_calculated_actions = pre_calculated_actions

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
                    # line.append("_")
                    line.append(" ")
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
    ) -> dict[Pos, int]:
        """Convert board data from game to internal representation"""
        pieces: dict[Pos, int] = {}
        for _tile_name, tile_data in tiles.items():
            piece_type = tile_data["piece"]
            if piece_type in {None, "None"}:
                continue
            x, y = tile_data["xy"]
            pieces[(x, y)] = int(piece_type)
        return pieces

    def calculate_actions(self, position: Pos) -> ActionSet:
        "Calculate all the actions the piece at given position can make"
        jumps = self.get_jumps(position)
        moves = self.get_moves(position)
        ends = set(jumps)
        ends.update(moves)
        return ActionSet(jumps, moves, ends)

    def get_actions_set(self, piece_position: Pos) -> ActionSet:
        """Calculate and return ActionSet if required"""
        if piece_position in self.pre_calculated_actions:
            new_action_set = self.pre_calculated_actions[piece_position]
        else:
            new_action_set = self.calculate_actions(piece_position)
            self.pre_calculated_actions[piece_position] = new_action_set
        return new_action_set

    def invalidate_location(self, position: Pos) -> None:
        if position in self.pre_calculated_actions:
            del self.pre_calculated_actions[position]

    def invalidate_all_locations(self) -> None:
        self.pre_calculated_actions.clear()

    ##            print(position)

    def piece_kinged(self, piece_pos: Pos, new_type: int) -> None:
        """Called when piece kinged."""
        ##        print(f'piece_kinged {piece = }')
        self.invalidate_location(piece_pos)

    def piece_moved(self, start_pos: Pos, end_pos: Pos) -> None:
        """Called when piece moved from start_pos to end_pos."""
        self.invalidate_location(start_pos)

    def piece_jumped(self, jumped_piece_pos: Pos) -> None:
        """Called when piece jumped."""
        ##        print(f'piece_jumped {position = }')
        self.invalidate_all_locations()

    def preform_action(self, action: Action) -> Self:
        """Return new state after preforming action on self"""
        from_pos, to_pos = action

        pieces_copy = dict(self.pieces.items())

        # Remove piece from it's start position
        piece_type = pieces_copy.pop(from_pos)

        # See if it's a jump
        if to_pos not in self.get_moves(from_pos):
            # Jumps are more complex to calculate and we need
            # to know what pieces got jumped over
            cur_x, cur_y = from_pos
            for jumped_pos in self.get_jumps(from_pos)[to_pos]:
                # Remove jumped position from pieces in play
                if jumped_pos in pieces_copy:
                    pieces_copy.pop(jumped_pos)
                self.piece_jumped(jumped_pos)
                # See if piece kinged
                jumped_x, jumped_y = jumped_pos
                # Rightshift 1 is more efficiant way to multiply by 2
                cur_x += (jumped_x - cur_x) << 1
                cur_y += (jumped_y - cur_y) << 1

                self.piece_moved(from_pos, (cur_x, cur_y))
                from_pos = (cur_x, cur_y)

                # Now that we know the current position, see if kinged
                if self.does_piece_king(piece_type, (cur_x, cur_y)):
                    piece_type += 2
                    self.piece_kinged(from_pos, piece_type)
        else:
            self.piece_moved(from_pos, to_pos)

        # See if it kings and king it if so
        if self.does_piece_king(piece_type, to_pos):
            piece_type += 2
            self.piece_kinged(from_pos, piece_type)

        # Move piece to it's end position
        pieces_copy[to_pos] = piece_type
        self.invalidate_location(from_pos)

        self.invalidate_all_locations()

        # Swap turn
        return self.__class__(
            self.size,
            not self.turn,
            pieces_copy,
            pre_calculated_actions=self.pre_calculated_actions,
        )

    def get_tile_name(self, x: int, y: int) -> str:
        """Get name of a given tile"""
        return chr(65 + x) + str(self.size[1] - y)

    def get_tile_pos(self, name: str) -> Pos:
        """Get tile position from it's name"""
        x = ord(name[0]) - 65
        y = self.size[1] - int(name[1:])
        return (x, y)

    def action_from_points(self, start: Pos, end: Pos) -> Action:
        """Return action from given start and end coordinates"""
        ##        return Action(self.get_tile_name(*start), self.get_tile_name(*end))
        return Action(start, end)

    def get_turn(self) -> bool:
        """Return whose turn it is. True = AI (us)"""
        return self.turn

    def valid_location(self, position: Pos) -> bool:
        """Return if position is valid"""
        x, y = position
        w, h = self.size
        return 0 <= x and 0 <= y and x < w and y < h

    def does_piece_king(self, piece_type: int, position: Pos) -> bool:
        """Return if piece needs to be kinged given it's type and position"""
        _, y = position
        _, h = self.size
        return (piece_type == 0 and y == 0) or (piece_type == 1 and y == h - 1)

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

    def get_actions(self, position: Pos) -> list[Action]:
        """Return list of all moves and jumps the piece at position can make"""
        ends = set(self.get_jumps(position))
        ends.update(self.get_moves(position))
        ##        ends = self.get_actions_set(position).ends
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

    def can_player_select_piece(self, player: int, tile_pos: Pos) -> bool:
        """Return True if player can select piece on given tile position."""
        piece_at_pos = self.pieces.get(tile_pos)
        if piece_at_pos is None:
            return False
        return (piece_at_pos % 2) == player

    def get_pieces(self) -> tuple[tuple[Pos, int], ...]:
        """Get all pieces"""
        return tuple((pos, type_) for pos, type_ in self.pieces.items())
