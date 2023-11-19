"""Minimax - Boilerplate code for Minimax AIs."""

# Programmed by CoolCat467

__title__ = "Minimax"
__author__ = "CoolCat467"
__version__ = "0.0.0"

from abc import ABC, abstractmethod
from collections.abc import Iterable
from enum import IntEnum, auto
from math import inf as infinity
from typing import Generic, NamedTuple, TypeVar


class Player(IntEnum):
    """Enum for player status"""

    __slots__ = ()
    MIN = auto()
    MAX = auto()


State = TypeVar("State")
Action = TypeVar("Action")


class MinimaxResult(NamedTuple, Generic[Action]):
    """Minimax Result"""

    value: int | float
    action: Action | None


class Minimax(ABC, Generic[State, Action]):
    """Base class for Minimax AIs"""

    __slots__ = ()

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

        Must return either Player.MIN or Player.MAX
        """

    @classmethod
    @abstractmethod
    def actions(cls, state: State) -> Iterable[Action]:
        """Return a collection of all possible actions in a given game state"""

    @classmethod
    @abstractmethod
    def result(cls, state: State, action: Action) -> State:
        """Return new game state after performing action on given state"""

    @classmethod
    def minimax(
        cls,
        state: State,
        depth: int | None = 5,
    ) -> MinimaxResult[Action]:
        if cls.terminal(state):
            return MinimaxResult(cls.value(state), None)
        if depth is not None and depth <= 0:
            return MinimaxResult(
                cls.value(state), next(iter(cls.actions(state))),
            )
        next_down = None if depth is None else depth - 1

        current_player = cls.player(state)
        value: int | float
        if current_player == Player.MAX:
            value = -infinity
            best = max
        else:
            value = infinity
            best = min

        best_action: Action | None = None
        for action in cls.actions(state):
            result = cls.minimax(cls.result(state, action), next_down)
            new_value = best(value, result.value)
            if new_value != value:
                best_action = action
            value = new_value
        return MinimaxResult(value, best_action)


class AsyncMinimax(ABC, Generic[State, Action]):
    """Base class for Minimax AIs"""

    __slots__ = ()

    @classmethod
    @abstractmethod
    async def value(cls, state: State) -> int | float:
        """Return the value of a given game state"""

    @classmethod
    @abstractmethod
    async def terminal(cls, state: State) -> bool:
        """Return if given game state is terminal"""

    @classmethod
    @abstractmethod
    async def player(cls, state: State) -> Player:
        """Return player status given the state of the game

        Must return either Player.MIN or Player.MAX
        """

    @classmethod
    @abstractmethod
    async def actions(cls, state: State) -> Iterable[Action]:
        """Return a collection of all possible actions in a given game state"""

    @classmethod
    @abstractmethod
    async def result(cls, state: State, action: Action) -> State:
        """Return new game state after performing action on given state"""

    @classmethod
    async def minimax(
        cls,
        state: State,
        depth: int | None = 5,
    ) -> MinimaxResult[Action]:
        if await cls.terminal(state):
            return MinimaxResult(await cls.value(state), None)
        if depth is not None and depth <= 0:
            return MinimaxResult(
                await cls.value(state), next(iter(await cls.actions(state))),
            )
        next_down = None if depth is None else depth - 1

        current_player = await cls.player(state)
        value: int | float
        if current_player == Player.MAX:
            value = -infinity
            best = max
        else:
            value = infinity
            best = min

        best_action: Action | None = None
        for action in await cls.actions(state):
            result = await cls.minimax(
                await cls.result(state, action), next_down,
            )
            new_value = best(value, result.value)
            if new_value != value:
                best_action = action
            value = new_value
        return MinimaxResult(value, best_action)


if __name__ == "__main__":
    print(f"{__title__}\nProgrammed by {__author__}.\n")
