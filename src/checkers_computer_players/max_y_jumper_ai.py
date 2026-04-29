#!/usr/bin/env python3
# AI that plays checkers.

"""Get to other side + best jump AI Checkers AI."""

from __future__ import annotations

# Programmed by CoolCat467

__title__ = "Get to other side + best jump AI"
__author__ = "CoolCat467"
__version__ = "1.0.0"
__ver_major__ = 1
__ver_minor__ = 0
__ver_patch__ = 0


import random
from typing import TypeVar

from checkers.state import Action, Pos, State
from checkers_computer_players.machine_client import (
    RemoteState,
    run_clients_in_local_servers_sync,
)

T = TypeVar("T")


def turn(state: State) -> Action:
    """Return the piece it wants to move and the tile id the target piece should be moved to."""
    # We have no idea what jumps we can make nor tiles we can select
    jump_tiles = {}
    select_tiles = {}

    # For each tile id in tileids
    for piece_pos, piece_type in state.get_pieces():
        # If the tile's piece is one of ours,
        if piece_type in {state.turn, state.turn + 2}:
            jumps = state.get_jumps(piece_pos)
            # If this our piece can make jumps,
            if jumps:
                # Get the number of jumps each end point would make
                v = [len(v) for v in list(jumps.values())]
                # Get the end point with the most jumps
                k = list(jumps.keys())[v.index(max(v))]
                # Store the target tile id and the end point with the most jumps in dictionary
                # with the number of jumps that moves makes
                jump_tiles[max(v)] = [piece_pos, k]
            # Get the moves our piece can make
            moves = state.get_moves(piece_pos)
            # If our piece can move,
            if moves:
                # Add it's moves to the dictionary of movable pieces at key of target tile id
                select_tiles[piece_pos] = moves
    # If there are no jumps we can make,
    if not jump_tiles:
        # Get a list of selectable target tiles
        selectable = list(select_tiles.keys())
        y_pos: dict[int, list[tuple[Pos, Pos]]] = {}
        for target in selectable:
            possible_moves = select_tiles[target]
            ##                print(target)
            ##                print(possible_moves)
            for move in possible_moves:
                _x, y = move
                if y not in y_pos:
                    y_pos[y] = []
                y_pos[y].append((target, move))
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
                    y_pos[y].append((target, move))
                min_y = min(y_pos)
                return Action(
                    *random.choice(  # noqa: S311  # Not important to be cryptographically safe
                        y_pos[min_y],
                    ),
                )
        ##            target = random.choice(selectable)
        ##            # Get the possible moves that piece can make
        ##            possibleMoves = select_tiles[target]
        ##            # Choose a random valid destination that piece can make as our destination tile id
        ##            destination= random.choice(possibleMoves)#[len(possibleMoves)-1]
        return Action(
            *random.choice(  # noqa: S311  # Not important to be cryptographically safe
                best_y,
            ),
        )
    # If we can make jumps,
    # Get the jump with the most jumps possible
    select = max(jump_tiles.keys())
    # Set our target to that jump's starting tile id
    target = jump_tiles[select][0]
    # Set our destination to that jump's end tile id
    destination = jump_tiles[select][1]
    # Tell the game about our decision
    return Action(target, destination)


class MaxYJumperPlayer(RemoteState):
    """Max Y Jumper Player."""

    __slots__ = ()

    async def perform_turn(self) -> Action:
        """Perform turn."""
        print("perform_turn")
        return turn(self.state)


def run() -> None:
    """Run MaxYJumperPlayer clients in local servers."""
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    run_clients_in_local_servers_sync(MaxYJumperPlayer)


if __name__ == "__main__":
    run()
