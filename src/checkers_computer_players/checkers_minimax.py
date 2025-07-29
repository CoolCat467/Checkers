"""Checkers Minimax."""

# Programmed by CoolCat467

from __future__ import annotations

# Checkers Minimax
# Copyright (C) 2024-2025  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "Checkers Minimax"
__author__ = "CoolCat467"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"


import math
import random
import time
from collections import Counter
from math import inf as infinity
from typing import TYPE_CHECKING, Any, TypeVar

from checkers.state import Action, State
from checkers_computer_players.minimax import (
    Minimax,
    MinimaxResult,
    Player,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from mypy_extensions import u8

T = TypeVar("T")

# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3


class MinimaxWithTT(Minimax[State, Action]):
    """Minimax with transposition table."""

    __slots__ = ("transposition_table",)

    # Simple Transposition Table:
    # key → (stored_depth, result, flag)
    # flag: 'EXACT', 'LOWERBOUND', 'UPPERBOUND'
    def __init__(self) -> None:
        """Initialize this object."""
        super().__init__()

        self.transposition_table: dict[
            int,
            tuple[u8, MinimaxResult[Any], str],
        ] = {}

    def _transposition_table_lookup(
        self,
        state_hash: int,
        depth: u8,
        alpha: float,
        beta: float,
    ) -> MinimaxResult[Action] | None:
        """Lookup in transposition_table.  Return (value, action) or None."""
        entry = self.transposition_table.get(state_hash)
        if entry is None:
            return None

        stored_depth, result, flag = entry
        # only use if stored depth is deep enough
        if stored_depth >= depth and (
            (flag == "EXACT")
            or (flag == "LOWERBOUND" and result.value > alpha)
            or (flag == "UPPERBOUND" and result.value < beta)
        ):
            return result
        return None

    def _transposition_table_store(
        self,
        state_hash: int,
        depth: u8,
        result: MinimaxResult[Action],
        alpha: float,
        beta: float,
    ) -> None:
        """Store in transposition_table with proper flag."""
        if result.value <= alpha:
            flag = "UPPERBOUND"
        elif result.value >= beta:
            flag = "LOWERBOUND"
        else:
            flag = "EXACT"
        self.transposition_table[state_hash] = (depth, result, flag)

    @classmethod
    def hash_state(cls, state: State) -> int:
        """Your state-to-hash function.  Must be consistent."""
        # For small games you might do: return hash(state)
        # For larger, use Zobrist or custom.
        return hash(state)

    def alphabeta_transposition_table(
        self,
        state: State,
        depth: u8 = 5,
        a: float = -infinity,
        b: float = infinity,
    ) -> MinimaxResult[Action]:
        """AlphaBeta with transposition table."""
        if self.terminal(state):
            return MinimaxResult(self.value(state), None)
        if depth <= 0:
            # Choose a random action
            # No need for cryptographic secure random
            return MinimaxResult(
                self.value(state),
                random.choice(tuple(self.actions(state))),  # noqa: S311
            )
        next_down = depth - 1

        state_h = self.hash_state(state)
        # 1) Try transposition_table lookup
        transposition_table_hit = self._transposition_table_lookup(
            state_h,
            depth,
            a,
            b,
        )
        if transposition_table_hit is not None:
            return transposition_table_hit
        next_down = None if depth is None else depth - 1

        current_player = self.player(state)
        value: float

        best_action: Action | None = None

        if current_player == Player.MAX:
            value = -infinity
            for action in self.actions(state):
                child = self.alphabeta_transposition_table(
                    self.result(state, action),
                    next_down,
                    a,
                    b,
                )
                if child.value > value:
                    value = child.value
                    best_action = action
                a = max(a, value)
                if a >= b:
                    break

        elif current_player == Player.MIN:
            value = infinity
            for action in self.actions(state):
                child = self.alphabeta_transposition_table(
                    self.result(state, action),
                    next_down,
                    a,
                    b,
                )
                if child.value < value:
                    value = child.value
                    best_action = action
                b = min(b, value)
                if b <= a:
                    break
        else:
            raise NotImplementedError(f"{current_player = }")

        # 2) Store in transposition_table
        result = MinimaxResult(value, best_action)
        self._transposition_table_store(state_h, depth, result, a, b)
        return result

    def iterative_deepening(
        self,
        state: State,
        start_depth: u8 = 5,
        max_depth: u8 = 7,
        time_limit_ns: int | float | None = None,
    ) -> MinimaxResult[Action]:
        """Run alpha-beta with increasing depth up to max_depth.

        If time_limit_ns is None, do all depths. Otherwise stop early.
        """
        best_result: MinimaxResult[Action] = MinimaxResult(0.0, None)
        start_t = time.perf_counter_ns()

        for depth in range(start_depth, max_depth + 1):
            # clear or keep transposition_table between depths? often you keep it
            # self.transposition_table.clear()

            result = self.alphabeta_transposition_table(
                state,
                depth,
            )
            best_result = result

            # Optional: if you find a forced win/loss you can stop
            if abs(result.value) == self.HIGHEST:
                print(f"reached terminal state stop {depth=}")
                break

            # optional time check
            if (
                time_limit_ns
                and (time.perf_counter_ns() - start_t) > time_limit_ns
            ):
                print(
                    f"break from time expired {depth=} ({(time.perf_counter_ns() - start_t) / 1e9} seconds elaped)",
                )
                break
            print(
                f"{depth=} ({(time.perf_counter_ns() - start_t) / 1e9} seconds elaped)",
            )

        return best_result


# Minimax[State, Action]
class CheckersMinimax(MinimaxWithTT):
    """Minimax Algorithm for Checkers."""

    __slots__ = ()

    @classmethod
    def hash_state(cls, state: State) -> int:
        """Return state hash value."""
        # For small games you might do: return hash(state)
        # For larger, use Zobrist or custom.
        return hash((state.size, tuple(state.pieces.items()), state.turn))

    @classmethod
    def value(cls, state: State) -> float:
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
        return float(win) * 2.0 - 1.0

    @classmethod
    def terminal(cls, state: State) -> bool:
        """Return if game state is terminal."""
        return state.check_for_win() is not None

    @classmethod
    def player(cls, state: State) -> Player:
        """Return Player enum from current state's turn."""
        return Player.MAX if state.get_turn() else Player.MIN

    @classmethod
    def actions(cls, state: State) -> Iterable[Action]:
        """Return all actions that are able to be performed for the current player in the given state."""
        return state.get_all_actions(int(state.get_turn()))

    @classmethod
    def result(cls, state: State, action: Action) -> State:
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


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
