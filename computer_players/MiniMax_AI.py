#!/usr/bin/env python3
# AI that plays checkers.

from __future__ import annotations

__title__ = "Minimax AI"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import math
from collections import Counter
from typing import TYPE_CHECKING, TypeVar

import trio
from checkers.client import read_advertisements
from checkers.state import Action, State
from machine_client import RemoteState, run_client
from minimax import Minimax, MinimaxResult, Player

if TYPE_CHECKING:
    from collections.abc import Iterable

T = TypeVar("T")

PORT = 31613

# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3


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
        cls, state: State, minimum: int, maximum: int,
    ) -> MinimaxResult[Action]:
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
    """Minimax Player"""

    __slots__ = ()

    async def preform_turn(self) -> Action:
        """Perform turn"""
        print("preform_turn")
        ##        value, action = CheckersMinimax.adaptive_depth_minimax(
        ##            self.state, 4, 5
        ##        )
        value, action = CheckersMinimax.minimax(self.state, 4)
        print(f"{value = }")
        return action


async def run_async() -> None:
    details: tuple[str, int] | None = None
    while details is None:
        print("Watching for advertisements...")
        for advertisement in await read_advertisements():
            motd, details = advertisement
            print(f"{motd = } {details = }")
            break

    ##    host = "127.0.0.1"
    ##    port = PORT
    host, port = details
    await run_client(host, port, MinimaxPlayer)


def run() -> None:
    """Synchronous entry point."""
    trio.run(run_async)


print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
run()
