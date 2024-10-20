#!/usr/bin/env python3
# AI that plays checkers.

"""Minimax Checkers AI."""

from __future__ import annotations

# Programmed by CoolCat467

__title__ = "Minimax AI"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import math
from collections import Counter
from typing import TYPE_CHECKING, TypeVar

from machine_client import RemoteState, run_clients_in_local_servers_sync
from minimax import Minimax, MinimaxResult, Player

from checkers.state import Action, State

if TYPE_CHECKING:
    from collections.abc import Iterable

T = TypeVar("T")

# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3


class CheckersMinimax(Minimax[State, Action]):
    """Minimax Algorithm for Checkers."""

    __slots__ = ()

    @staticmethod
    def value(state: State) -> int | float:
        """Return value of given game state."""
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
        """Return if game state is terminal."""
        return state.check_for_win() is not None

    @staticmethod
    def player(state: State) -> Player:
        """Return Player enum from current state's turn."""
        return Player.MAX if state.get_turn() else Player.MIN

    @staticmethod
    def actions(state: State) -> Iterable[Action]:
        """Return all actions that are able to be performed for the current player in the given state."""
        return state.get_all_actions(int(state.get_turn()))

    @staticmethod
    def result(state: State, action: Action) -> State:
        """Return new state after performing given action on given current state."""
        return state.preform_action(action)

    @classmethod
    def adaptive_depth_minimax(
        cls,
        state: State,
        minimum: int,
        maximum: int,
    ) -> MinimaxResult[Action]:
        """Return minimax result from adaptive max depth."""
        ##        types = state.pieces.values()
        ##        current = len(types)
        ##        w, h = state.size
        ##        max_count = w * h // 6 << 1
        ##        old_depth = (1 - (current / max_count)) * math.floor(
        ##            math.sqrt(w**2 + h**2)
        ##        )

        depth = cls.value(state) * maximum + minimum
        final_depth = min(maximum, max(minimum, math.floor(depth)))
        print(f"{depth = } {final_depth = }")
        return cls.minimax(state, final_depth)


class MinimaxPlayer(RemoteState):
    """Minimax Player."""

    __slots__ = ()

    async def preform_turn(self) -> Action:
        """Perform turn."""
        print("preform_turn")
        ##value, action = CheckersMinimax.adaptive_depth_minimax(
        ##    self.state, 4, 5
        ##)
        ##value, action = CheckersMinimax.minimax(self.state, 4)
        value, action = CheckersMinimax.alphabeta(self.state, 4)
        if action is None:
            raise ValueError("action is None")
        print(f"{value = }")
        return action


def run() -> None:
    """Run MinimaxPlayer clients in local server."""
    run_clients_in_local_servers_sync(MinimaxPlayer)


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    run()
