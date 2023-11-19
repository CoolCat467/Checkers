#!/usr/bin/env python3
# AI that plays checkers.

from __future__ import annotations

__title__ = "Get to other side + best jump AI"
__author__ = "CoolCat467"
__version__ = "1.0.0"
__ver_major__ = 1
__ver_minor__ = 0
__ver_patch__ = 0


import random
from typing import TYPE_CHECKING, TypeVar

from machine_client import RemoteState, run_client_sync

if TYPE_CHECKING:
    from checkers.state import Action, State

T = TypeVar("T")

PORT = 31613


def turn(state: State) -> Action:
    """This function is called when the game requests the AI to return the piece it wants to move's id and the tile id the target piece should be moved to."""
    # We have no idea what jumps we can make nor tiles we can select
    jump_tiles = {}
    select_tiles = {}

    # For each tile id in tileids
    for piece_pos, piece_type in state.get_pieces():
        # If the tile's piece is one of ours,
        if piece_type in {state.turn, state.turn + 2}:
            action_set = state.get_actions_set(piece_pos)
            # If this our piece can make jumps,
            if action_set.jumps:
                # Get the number of jumps each end point would make
                v = [len(v) for v in list(action_set.jumps.values())]
                # Get the end point with the most jumps
                k = list(action_set.jumps.keys())[v.index(max(v))]
                # Store the target tile id and the end point with the most jumps in dictionary
                # with the number of jumps that moves makes
                jump_tiles[max(v)] = [piece_pos, k]
            # Get the moves our piece can make
            moves = action_set.moves
            # If our piece can move,
            if moves:
                # Add it's moves to the dictionary of movable pieces at key of target tile id
                select_tiles[piece_pos] = moves
    # If there are no jumps we can make,
    if not jump_tiles:
        # Get a list of selectable target tiles
        selectable = list(select_tiles.keys())
        y_pos = {}
        for target in selectable:
            possible_moves = select_tiles[target]
            ##                print(target)
            ##                print(possible_moves)
            for move in possible_moves:
                _x, y = move
                if y not in y_pos:
                    y_pos[y] = []
                y_pos[y].append([target, move])
        max_y = max(y_pos)
        best_y = y_pos[max_y]
        for target, _dest in best_y:
            if int(state.pieces[target]) >= 2:
                # If kinged is best, make it start to come back
                y_pos = {}
                for move in select_tiles[target]:
                    _x, y = move
                    if y not in y_pos:
                        y_pos[y] = []
                    y_pos[y].append([target, move])
                min_y = min(y_pos)
                return state.action_from_points(
                    *random.choice(  # noqa: S311  # Not important to be cryptographically safe
                        y_pos[min_y],
                    ),
                )
        ##            target = random.choice(selectable)
        ##            # Get the possible moves that piece can make
        ##            possibleMoves = select_tiles[target]
        ##            # Choose a random valid destination that piece can make as our destination tile id
        ##            destination= random.choice(possibleMoves)#[len(possibleMoves)-1]
        return state.action_from_points(
            *random.choice(  # noqa: S311  # Not important to be cryptographically safe
                best_y,
            ),
        )
    else:
        # If we can make jumps,
        # Get the jump with the most jumps possible
        select = max(jump_tiles.keys())
        # Set our target to that jump's starting tile id
        target = jump_tiles[select][0]
        # Set our destination to that jump's end tile id
        destination = jump_tiles[select][1]
    # Tell the game about our decision
    return state.action_from_points(target, destination)


class MaxYJumperPlayer(RemoteState):
    """Max Y Jumper Player"""

    __slots__ = ()

    async def preform_turn(self) -> Action:
        """Perform turn"""
        print("preform_turn")
        action = turn(self.state)
        return action


def run() -> None:
    """Synchronous entry point."""
    run_client_sync(MaxYJumperPlayer)


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    run()
