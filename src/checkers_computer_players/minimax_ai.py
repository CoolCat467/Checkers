#!/usr/bin/env python3
# AI that plays checkers.

"""Minimax Checkers AI."""

# Programmed by CoolCat467

from __future__ import annotations

# Minimax Checkers AI
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

__title__ = "Minimax AI"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import traceback
from typing import TYPE_CHECKING, TypeVar

from checkers_computer_players.checkers_minimax import CheckersMinimax
from checkers_computer_players.machine_client import (
    RemoteState,
    run_clients_in_local_servers_sync,
)

if TYPE_CHECKING:
    from checkers.state import Action

T = TypeVar("T")

# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3


class MinimaxWithID(Minimax[State, Action]):
    """Minimax with ID."""

    __slots__ = ()

    # Simple Transposition Table:
    # key → (stored_depth, value, action, flag)
    # flag: 'EXACT', 'LOWERBOUND', 'UPPERBOUND'
    TRANSPOSITION_TABLE: ClassVar[
        dict[int, tuple[int, MinimaxResult[Any], str]]
    ] = {}

    @classmethod
    def _transposition_table_lookup(
        cls,
        state_hash: int,
        depth: int,
        alpha: float,
        beta: float,
    ) -> MinimaxResult[Action] | None:
        """Lookup in transposition_table.  Return (value, action) or None."""
        entry = cls.TRANSPOSITION_TABLE.get(state_hash)
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

    @classmethod
    def _transposition_table_store(
        cls,
        state_hash: int,
        depth: int,
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
        cls.TRANSPOSITION_TABLE[state_hash] = (depth, result, flag)

    @classmethod
    def hash_state(cls, state: State) -> int:
        """Your state-to-hash function.  Must be consistent."""
        # For small games you might do: return hash(state)
        # For larger, use Zobrist or custom.
        return hash(state)

    @classmethod
    def alphabeta_transposition_table(
        cls,
        state: State,
        depth: int = 5,
        a: int | float = -infinity,
        b: int | float = infinity,
    ) -> MinimaxResult[Action]:
        """AlphaBeta with transposition table."""
        if cls.terminal(state):
            return MinimaxResult(cls.value(state), None)
        if depth <= 0:
            # Choose a random action
            # No need for cryptographic secure random
            return MinimaxResult(
                cls.value(state),
                random.choice(tuple(cls.actions(state))),  # noqa: S311
            )
        next_down = depth - 1

        state_h = cls.hash_state(state)
        # 1) Try transposition_table lookup
        transposition_table_hit = cls._transposition_table_lookup(
            state_h,
            depth,
            a,
            b,
        )
        if transposition_table_hit is not None:
            return transposition_table_hit
        next_down = None if depth is None else depth - 1

        current_player = cls.player(state)
        value: int | float

        best_action: Action | None = None

        if current_player == Player.MAX:
            value = -infinity
            for action in cls.actions(state):
                child = cls.alphabeta_transposition_table(
                    cls.result(state, action),
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
            for action in cls.actions(state):
                child = cls.alphabeta_transposition_table(
                    cls.result(state, action),
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
        cls._transposition_table_store(state_h, depth, result, a, b)
        return result

    @classmethod
    def iterative_deepening(
        cls,
        state: State,
        start_depth: int = 5,
        max_depth: int = 7,
        time_limit_ns: int | float | None = None,
    ) -> MinimaxResult[Action]:
        """Run alpha-beta with increasing depth up to max_depth.

        If time_limit_ns is None, do all depths. Otherwise stop early.
        """
        best_result: MinimaxResult[Action] = MinimaxResult(0, None)
        start_t = time.perf_counter_ns()

        for depth in range(start_depth, max_depth + 1):
            # clear or keep transposition_table between depths? often you keep it
            # cls.TRANSPOSITION_TABLE.clear()

            result = cls.alphabeta_transposition_table(
                state,
                depth,
            )
            best_result = result

            # Optional: if you find a forced win/loss you can stop
            if abs(result.value) == cls.HIGHEST:
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
class CheckersMinimax(MinimaxWithID):
    """Minimax Algorithm for Checkers."""

    __slots__ = ()

    @classmethod
    def hash_state(cls, state: State) -> int:
        """Return state hash value."""
        # For small games you might do: return hash(state)
        # For larger, use Zobrist or custom.
        return hash((state.size, tuple(state.pieces.items()), state.turn))

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
        return state.perform_action(action)

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

    __slots__ = ("minimax",)

    def __init__(self) -> None:
        """Initialize minimax player."""
        super().__init__()

        self.minimax = CheckersMinimax()

    async def perform_turn(self) -> Action:
        """Perform turn."""
        print("perform_turn")
        ##value, action = CheckersMinimax.adaptive_depth_minimax(
        ##    self.state, 4, 5
        ##)
        ##value, action = CheckersMinimax.minimax(self.state, 4)
        ##value, action = CheckersMinimax.alphabeta(self.state, 4)
        value, action = self.minimax.iterative_deepening(
            self.state,
            4,
            20,
            int(5 * 1e9),
        )
        if action is None:
            raise ValueError("action is None")
        print(f"{value = }")
        return action


def run() -> None:
    """Run MinimaxPlayer clients in local server."""
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    try:
        run_clients_in_local_servers_sync(MinimaxPlayer)
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    run()
