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
    from collections.abc import Generator, Iterable


class Player(IntEnum):
    """Enum for player status."""

    __slots__ = ()
    MIN = auto()
    MAX = auto()


State = TypeVar("State")
Action = TypeVar("Action")


class MinimaxResult(NamedTuple, Generic[Action]):
    """Minimax Result."""

    value: int | float
    action: Action | None


class ActionNode(NamedTuple, Generic[Action]):
    """Action Tree Node."""

    action: Action
    children: list[ActionNode[Action]]

    def add_child(self, child_node: ActionNode[Action]) -> None:
        """Add child note to this action node."""
        self.children.append(child_node)

    def should_use_actions(self) -> bool:
        """Return if should use this tree's actions."""
        return bool(self.children)

    def get_actions(self) -> Generator[Action, None, None]:
        """Yield child actions."""
        for child_node in self.children:
            yield child_node.action

    def get_child_tree(self, action: Action) -> ActionNode[Action]:
        """Return child tree that uses given action."""
        for child_node in self.children:
            if child_node.action == action:
                return child_node
        raise ValueError(f"Action {action} not found in children.")


class Minimax(ABC, Generic[State, Action]):
    """Base class for Minimax AIs."""

    __slots__ = ()

    @classmethod
    @abstractmethod
    def value(cls, state: State) -> int | float:
        """Return the value of a given game state."""

    @classmethod
    @abstractmethod
    def terminal(cls, state: State) -> bool:
        """Return if given game state is terminal."""

    @classmethod
    @abstractmethod
    def player(cls, state: State) -> Player:
        """Return player status given the state of the game.

        Must return either Player.MIN or Player.MAX
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
    def minimax(
        cls,
        state: State,
        depth: int | None = 5,
        parent: ActionNode[Action] | None = None,
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
        else:
            value = infinity
            best = min

        best_action: Action | None = None
        actions: Iterable[Action]
        add_child = True
        if parent is not None and parent.should_use_actions():
            actions = parent.get_actions()
            add_child = False
        else:
            actions = cls.actions(state)
        for action in actions:
            action_node = ActionNode(action, [])
            if parent is not None and add_child:
                parent.add_child(action_node)
            result = cls.minimax(
                cls.result(state, action),
                next_down,
                action_node,
            )
            new_value = best(value, result.value)
            if new_value != value:
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
        else:
            value = infinity
            best = min
            compare = operator.lt  # less than (<)
            set_idx = 1

        best_action: Action | None = None
        for action in cls.actions(state):
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
        return MinimaxResult(value, best_action)


class AsyncMinimax(ABC, Generic[State, Action]):
    """Base class for Minimax AIs."""

    __slots__ = ()

    @classmethod
    @abstractmethod
    async def value(cls, state: State) -> int | float:
        """Return the value of a given game state."""

    @classmethod
    @abstractmethod
    async def terminal(cls, state: State) -> bool:
        """Return if given game state is terminal."""

    @classmethod
    @abstractmethod
    async def player(cls, state: State) -> Player:
        """Return player status given the state of the game.

        Must return either Player.MIN or Player.MAX
        """

    @classmethod
    @abstractmethod
    async def actions(cls, state: State) -> Iterable[Action]:
        """Return a collection of all possible actions in a given game state."""

    @classmethod
    @abstractmethod
    async def result(cls, state: State, action: Action) -> State:
        """Return new game state after performing action on given state."""

    @classmethod
    async def minimax(
        cls,
        state: State,
        depth: int | None = 5,
    ) -> MinimaxResult[Action]:
        """Return minimax result best action for a given state for the current player."""
        if await cls.terminal(state):
            return MinimaxResult(await cls.value(state), None)
        if depth is not None and depth <= 0:
            return MinimaxResult(
                await cls.value(state),
                next(iter(await cls.actions(state))),
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
                await cls.result(state, action),
                next_down,
            )
            new_value = best(value, result.value)
            if new_value != value:
                best_action = action
            value = new_value
        return MinimaxResult(value, best_action)


if __name__ == "__main__":
    print(f"{__title__}\nProgrammed by {__author__}.\n")
