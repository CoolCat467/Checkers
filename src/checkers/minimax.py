#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Minimax - Boilerplate code for Minimax AIs

"Minimax AI Base"

# Programmed by CoolCat467

__title__ = "Minimax"
__author__ = "CoolCat467"
__version__ = "0.0.0"

from abc import ABC, abstractmethod
from collections import namedtuple
from collections.abc import Iterable
from enum import IntEnum, auto
from math import inf as infinity
from typing import Generic, TypeVar


class Player(IntEnum):
    """Enum for player status"""

    MIN = auto()
    MAX = auto()


MinimaxResult = namedtuple("MinimaxResult", ("value", "action"))

State = TypeVar("State")
Action = TypeVar("Action")


class Minimax(ABC, Generic[State, Action]):
    """Base class for Minimax AIs"""

    __slots__ = ()
    ##    min_wins_value: int | float = -1
    ##    max_wins_value: int | float = 1

    @classmethod
    @abstractmethod
    def value(cls, state: State) -> int | float:
        """Return the value of a given game state"""

    @classmethod
    @abstractmethod
    def terminal(cls, state: State) -> bool:
        """Return if given game state is terminal"""

    @classmethod
    @abstractmethod
    def player(cls, state: State) -> Player:
        """Return player status given the state of the game

        Must return either Player.MIN or Player.MAX"""

    @classmethod
    @abstractmethod
    def actions(cls, state: State) -> Iterable[Action]:
        """Return a collection of all possible actions in a given game state"""

    @classmethod
    @abstractmethod
    def result(cls, state: State, action: Action) -> State:
        """Return new game state after preforming action on given state"""

    @classmethod
    @abstractmethod
    def minimax(
        cls,
        state: State,
        depth: int | None = 5,
    ) -> MinimaxResult:
        if cls.terminal(state):
            return MinimaxResult(cls.value(state), None)
        if depth is not None and depth <= 0:
            return MinimaxResult(
                cls.value(state), next(iter(cls.actions(state)))
            )
        next_down = None if depth is None else depth - 1

        current_player = cls.player(state)
        value: int | float
        if current_player == Player.MAX:
            value = -infinity
            best = max
        ##            opponent_win = cls.min_wins_value
        else:
            value = infinity
            best = min
        ##            opponent_win = cls.max_wins_value

        best_action: Action | None = None
        for action in cls.actions(state):
            result = cls.minimax(cls.result(state, action), next_down)
            new_value = best(value, result.value)
            if new_value != value:
                best_action = action
            value = new_value
        return MinimaxResult(value, best_action)


def run() -> None:
    "Run test of module"


if __name__ == "__main__":
    print(f"{__title__}\nProgrammed by {__author__}.\n")
    run()
