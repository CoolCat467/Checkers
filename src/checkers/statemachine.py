#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# State Machines

"State Machine module"

# Programmed by CoolCat467

__title__ = "State Machine"
__author__ = "CoolCat467"
__version__ = "0.1.8"
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 8

from collections.abc import Iterable
from typing import Generic, Self, TypeVar
from weakref import ref

__all__ = ["State", "AsyncState", "StateMachine", "AsyncStateMachine"]


Machine = TypeVar("Machine", bound="BaseStateMachine", covariant=True)


class BaseState(Generic[Machine]):
    "Base class for states."
    __slots__ = ("name", "machine_ref")

    def __init__(self, name: str) -> None:
        "Initialize state with a name."
        self.name = name
        self.machine_ref: ref[Machine]

    def __str__(self) -> str:
        "Return <{self.name} {class-name}>"
        return f"<{self.name} {self.__class__.__name__}>"

    def __repr__(self) -> str:
        "Return self as string."
        return str(self)

    @property
    def machine(self) -> Machine | None:
        """Get machine from internal weak reference"""
        return self.machine_ref()


SyncMachine = TypeVar("SyncMachine", bound="StateMachine", covariant=True)


class State(BaseState[SyncMachine]):
    "Base class for synchronous states."
    __slots__ = ()

    def entry_actions(self) -> None:
        "Preform entry actions for this State."
        return None

    def do_actions(self) -> None:
        "Preform actions for this State."
        return None

    def check_conditions(self) -> str | None:
        "Check state and return new state name or stay in current"
        return None

    def exit_actions(self) -> None:
        "Preform exit actions for this State."
        return None


AsyncMachine = TypeVar(
    "AsyncMachine", bound="AsyncStateMachine", covariant=True
)


class AsyncState(BaseState[AsyncMachine]):
    "Base class for asynchronous states."
    __slots__ = ()

    async def entry_actions(self) -> None:
        "Preform entry actions for this State."
        return None

    async def do_actions(self) -> None:
        "Preform actions for this State."
        return None

    async def check_conditions(self) -> str | None:
        "Check state and return new state name or stay in current"
        return None

    async def exit_actions(self) -> None:
        "Preform exit actions for this State."
        return None


class BaseStateMachine:
    "State Machine base class"
    __slots__ = ("states", "active_state", "__weakref__")

    def __repr__(self) -> str:
        "Return <{class-name} {self.states}>"
        text = f"<{self.__class__.__name__}"
        if hasattr(self, "states"):
            text += f" {self.states}"
        return text + ">"


class StateMachine(BaseStateMachine):
    "Synchronous State Machine base class"
    __slots__ = ()

    def __init__(self) -> None:
        self.states: dict[str, State[Self]] = {}  # Stores the states
        self.active_state: State[
            Self
        ] | None = None  # The currently active state

    def add_state(self, state: State[Self]) -> None:
        "Add a State instance to the internal dictionary."
        if not isinstance(state, State):
            raise TypeError(
                f'"{type(state).__name__}" is not an instance of State!'
            )
        state.machine_ref = ref(self)
        self.states[state.name] = state

    def add_states(self, states: Iterable[State[Self]]) -> None:
        "Add multiple State instances to internal dictionary."
        for state in states:
            self.add_state(state)

    def remove_state(self, state_name: str) -> None:
        "Remove state with given name from internal dictionary."
        if state_name not in self.states:
            raise ValueError(f"{state_name} is not a registered State.")
        del self.states[state_name]

    def set_state(self, new_state_name: str | None) -> None:
        "Change states and preform any exit / entry actions."
        if new_state_name not in self.states and new_state_name is not None:
            raise KeyError(
                f'"{new_state_name}" not found in internal states dictionary!'
            )

        if self.active_state is not None:
            self.active_state.exit_actions()

        if new_state_name is None:
            self.active_state = None
        else:
            self.active_state = self.states[new_state_name]
            self.active_state.entry_actions()

    def think(self) -> None:
        "Preform actions check conditions and potentially change states"
        # Only continue if there is an active state
        if self.active_state is None:
            return None
        # Preform the actions of the active state
        self.active_state.do_actions()
        # Check conditions and potentially change states.
        new_state_name = self.active_state.check_conditions()
        if new_state_name is not None:
            self.set_state(new_state_name)
        return None


class AsyncStateMachine(BaseStateMachine):
    "Asynchronous State Machine base class"
    __slots__ = ()

    def __init__(self) -> None:
        self.states: dict[str, AsyncState[Self]] = {}  # Stores the states
        self.active_state: AsyncState[Self] | None = None  # active state

    def add_state(self, state: AsyncState[Self]) -> None:
        "Add an AsyncState instance to the internal dictionary."
        if not isinstance(state, AsyncState):
            raise TypeError(
                f'"{type(state).__name__}" is not an instance of AsyncState!'
            )
        state.machine_ref = ref(self)
        self.states[state.name] = state

    def add_states(self, states: Iterable[AsyncState[Self]]) -> None:
        "Add multiple State instances to internal dictionary."
        for state in states:
            self.add_state(state)

    def remove_state(self, state_name: str) -> None:
        "Remove state with given name from internal dictionary."
        if state_name not in self.states:
            raise ValueError(f"{state_name} is not a registered AsyncState.")
        del self.states[state_name]

    async def set_state(self, new_state_name: str | None) -> None:
        "Change states and preform any exit / entry actions."
        if new_state_name not in self.states and new_state_name is not None:
            raise KeyError(
                f'"{new_state_name}" not found in internal states dictionary!'
            )

        if self.active_state is not None:
            await self.active_state.exit_actions()

        if new_state_name is None:
            self.active_state = None
        else:
            self.active_state = self.states[new_state_name]
            await self.active_state.entry_actions()

    async def think(self) -> None:
        "Preform actions check conditions and potentially change states"
        # Only continue if there is an active state
        if self.active_state is None:
            return None
        # Preform the actions of the active state
        await self.active_state.do_actions()
        # Check conditions and potentially change states.
        new_state_name = await self.active_state.check_conditions()
        if new_state_name is not None:
            await self.set_state(new_state_name)


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.")
