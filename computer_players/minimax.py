"""Minimax - Boilerplate code for Minimax AIs."""

from __future__ import annotations

# Programmed by CoolCat467

__title__ = "Minimax"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import operator
import random
from abc import ABC, abstractmethod
from enum import IntEnum, auto
from math import inf as infinity
from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable


class Player(IntEnum):
    """Enum for player status."""

    __slots__ = ()
    MIN = auto()
    MAX = auto()
    CHANCE = auto()


State = TypeVar("State")
Action = TypeVar("Action")


class MinimaxResult(NamedTuple, Generic[Action]):
    """Minimax Result."""

    value: int | float
    action: Action | None


class Minimax(ABC, Generic[State, Action]):
    """Base class for Minimax AIs."""

    __slots__ = ()

    LOWEST = -1
    HIGHEST = 1

    @classmethod
    @abstractmethod
    def value(cls, state: State) -> int | float:
        """Return the value of a given game state.

        Should be in range [cls.LOWEST, cls.HIGHEST].
        """

    @classmethod
    @abstractmethod
    def terminal(cls, state: State) -> bool:
        """Return if given game state is terminal."""

    @classmethod
    @abstractmethod
    def player(cls, state: State) -> Player:
        """Return player status given the state of the game.

        Must return either Player.MIN or Player.MAX, or Player.CHANCE
        if there is a random action.
        """

    @classmethod
    @abstractmethod
    def actions(cls, state: State) -> Iterable[Action]:
        """Return a collection of all possible actions in a given game state."""

    @classmethod
    @abstractmethod
    def result(cls, state: State, action: Action) -> State:
        """Return new game state after performing action on given state."""

    @classmethod
    def probability(cls, action: Action) -> float:
        """Return probability that given chance node action will happen.

        Should be in range [0.0, 1.0] for 0% and 100% chance respectively.
        """
        raise NotImplementedError()

    @classmethod
    def minimax(
        cls,
        state: State,
        depth: int | None = 5,
    ) -> MinimaxResult[Action]:
        """Return minimax result best action for a given state for the current player."""
        if cls.terminal(state):
            return MinimaxResult(cls.value(state), None)
        if depth is not None and depth <= 0:
            # Choose a random action
            # No need for cryptographic secure random
            return MinimaxResult(
                cls.value(state),
                random.choice(tuple(cls.actions(state))),  # noqa: S311
            )
        next_down = None if depth is None else depth - 1

        current_player = cls.player(state)
        value: int | float
        if current_player == Player.MAX:
            value = -infinity
            best = max
        elif current_player == Player.MIN:
            value = infinity
            best = min
        elif current_player == Player.CHANCE:
            value = 0
            best = sum
        else:
            raise ValueError(f"Unexpected player type {current_player!r}")

        best_action: Action | None = None
        for action in cls.actions(state):
            result = cls.minimax(cls.result(state, action), next_down)
            result_value = result.value
            if current_player == Player.CHANCE:
                # Probability[action]
                result_value *= cls.probability(action)
            new_value = best(value, result_value)
            if new_value != value and current_player != Player.CHANCE:
                best_action = action
            value = new_value
        return MinimaxResult(value, best_action)

    @classmethod
    def alphabeta(
        cls,
        state: State,
        depth: int | None = 5,
        a: int | float = -infinity,
        b: int | float = infinity,
    ) -> MinimaxResult[Action]:
        """Return minimax alphabeta pruning result best action for given current state."""
        # print(f'alphabeta {depth = } {a = } {b = }')

        if cls.terminal(state):
            return MinimaxResult(cls.value(state), None)
        if depth is not None and depth <= 0:
            # Choose a random action
            # No need for cryptographic secure random
            return MinimaxResult(
                cls.value(state),
                random.choice(tuple(cls.actions(state))),  # noqa: S311
            )
        next_down = None if depth is None else depth - 1

        current_player = cls.player(state)
        value: int | float
        if current_player == Player.MAX:
            value = -infinity
            best = max
            compare = operator.gt  # greater than (>)
            set_idx = 0
        elif current_player == Player.MIN:
            value = infinity
            best = min
            compare = operator.lt  # less than (<)
            set_idx = 1
        elif current_player == Player.CHANCE:
            value = 0
            best = sum
        else:
            raise ValueError(f"Unexpected player type {current_player!r}")

        actions = tuple(cls.actions(state))
        successors = len(actions)
        expect_a = successors * (a - cls.HIGHEST) + cls.HIGHEST
        expect_b = successors * (b - cls.LOWEST) + cls.LOWEST

        best_action: Action | None = None
        for action in actions:
            if current_player == Player.CHANCE:
                # Limit child a, b to a valid range
                ax = max(expect_a, cls.LOWEST)
                bx = min(expect_b, cls.HIGHEST)
                # Search the child with new cutoff values
                result = cls.alphabeta(
                    cls.result(state, action),
                    next_down,
                    ax,
                    bx,
                )
                score = result.value
                # Check for a, b cutoff conditions
                if score <= expect_a:
                    return MinimaxResult(a, None)
                if score >= expect_b:
                    return MinimaxResult(b, None)
                value += score
                # Adjust a, b for the next child
                expect_a += cls.HIGHEST - score
                expect_b += cls.LOWEST - score
                continue

            result = cls.alphabeta(cls.result(state, action), next_down, a, b)
            new_value = best(value, result.value)

            if new_value != value:
                best_action = action
            value = new_value

            if compare(new_value, (a, b)[set_idx ^ 1]):
                # print("cutoff")
                break  # cutoff

            alpha_beta_value = (a, b)[set_idx]
            new_alpha_beta_value = best(alpha_beta_value, value)

            if new_alpha_beta_value != alpha_beta_value:
                # Set new best
                alpha_beta_list = [a, b]
                alpha_beta_list[set_idx] = new_alpha_beta_value
                a, b = alpha_beta_list
        if current_player == Player.CHANCE:
            # No cutoff occurred, return score
            return MinimaxResult(value / successors, None)
        return MinimaxResult(value, best_action)


if __name__ == "__main__":
    print(f"{__title__}\nProgrammed by {__author__}.\n")
