#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Component - Components instead of chaotic class hierarchy mess

"Component system module"

# Programmed by CoolCat467

__title__ = "Component"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import functools
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, Generic, Self, TypeVar, cast
from weakref import proxy, ref

import trio

T = TypeVar("T")


class Event(Generic[T]):
    "Event with name and data"
    __slots__ = ("name", "data", "level")

    def __init__(self, name: str, data: T, levels: int = 0) -> None:
        self.name = name
        self.data = data
        self.level = levels

    def __repr__(self) -> str:
        "Return representation of self"
        items = {
            x: getattr(self, x)
            for x in self.__slots__
            if not x.startswith("_")
        }
        return f"<{self.__class__.__name__} {items}>"

    def pop_level(self) -> bool:
        "Travel up one level and return if should continue or not"
        self.level = max(0, self.level - 1)
        return self.level > 0


Manager = TypeVar("Manager", bound="ComponentManager")


class Component(Generic[Manager]):
    "Component base class"
    __slots__ = ("name", "__manager")

    def __init__(self, name: str) -> None:
        self.name = name
        self.__manager: ref[Manager] | None = None

    def __repr__(self) -> str:
        "Return representation of self"
        return f"{self.__class__.__name__}({self.name!r})"

    @property
    def manager(self) -> Manager:
        "ComponentManager if bound to one, otherwise raise AttributeError"
        if self.__manager is not None:
            manager = self.__manager()
            if manager is not None:
                return manager
        raise AttributeError(f"No component manager bound for {self.name}")

    def _unbind(self) -> None:
        "If you use this you are evil. This is only for ComponentManagers!"
        self.__manager = None

    @property
    def manager_exists(self) -> bool:
        "Return if manager is bound or not"
        return self.__manager is not None and self.__manager() is not None

    def register_handler(
        self,
        event_name: str,
        handler_coro: Callable[[Event[Any]], Awaitable[Any]],
    ) -> None:
        "Register handler with bound component manager"
        self.manager.register_handler(event_name, handler_coro)  # , self.name)

    def register_handlers(
        self,
        handlers: dict[str, Callable[[Event[Any]], Awaitable[Any]]],
    ) -> None:
        "Register multiple handler Coroutines"
        for name, coro in handlers.items():
            self.register_handler(name, coro)

    def bind_handlers(self) -> None:
        "Add handlers in subclass"

    def bind(self, manager: Manager) -> None:
        "Bind self to manager"
        if self.manager_exists:
            raise RuntimeError(
                f"{self.name} component is already bound to {self.manager}"
            )
        self.__manager = ref(manager)
        self.bind_handlers()

    async def raise_event(self, event: Event[Any]) -> None:
        "Raise event for bound manager"
        await self.manager.raise_event(event)

    def component_exists(self, component_name: str) -> bool:
        "Return if component exists in manager"
        return self.manager.component_exists(component_name)

    def components_exist(self, component_names: Iterable[str]) -> bool:
        "Return if all component names given exist in manager"
        return self.manager.components_exist(component_names)

    def get_component(self, component_name: str) -> "Component[Manager]":
        "Get Component from manager"
        return self.manager.get_component(component_name)

    def get_components(
        self, component_names: Iterable[str]
    ) -> list["Component[Manager]"]:
        "Get Components from manager"
        return self.manager.get_components(component_names)


class ComponentManager(Component["ComponentManager"]):
    "Component manager class"
    __slots__ = ("__event_handlers", "__components", "__weakref__")

    def __init__(self, name: str, own_name: str | None = None) -> None:
        "If own_name is set, add self to list of components as specified name"
        super().__init__(name)
        self.__event_handlers: dict[
            str, list[Callable[[Event[Any]], Awaitable[Any]]]
        ] = {}
        self.__components: dict[str, Component[Self]] = {}

        if own_name is not None:
            self.__add_self_as_component(own_name)

    def __repr__(self) -> str:
        return f"<ComponentManager Components: {self.__components}>"

    def __add_self_as_component(self, name: str) -> None:
        "Add this manager as component to self without binding."
        if self.component_exists(name):
            raise ValueError(f'Component named "{name}" already exists!')
        self.__components[name] = proxy(self)
        self.bind_handlers()

    def register_handler(
        self,
        event_name: str,
        handler_coro: Callable[[Event[Any]], Awaitable[None]],
    ) -> None:
        "Register handler_func as handler for event_name"
        if event_name not in self.__event_handlers:
            self.__event_handlers[event_name] = []
        self.__event_handlers[event_name].append(handler_coro)

    async def raise_event(self, event: Event[Any]) -> None:
        "Raise event for all components that have handlers registered"
        # Forward leveled events up; They'll come back to us soon enough.
        if self.manager_exists and event.pop_level():
            await super().raise_event(event)
            return

        # Call all registered handlers for this event
        if event.name in self.__event_handlers:
            async with trio.open_nursery() as nursery:
                for handler in self.__event_handlers[event.name]:
                    nursery.start_soon(handler, event)

        # Forward events to contained managers
        async with trio.open_nursery() as nursery:
            for component in self.get_all_components():
                # Skip self component if exists
                if component is self:
                    continue
                if isinstance(component, ComponentManager):
                    nursery.start_soon(component.raise_event, event)

    def add_component(self, component: Component[Self]) -> None:
        "Add component to this manager"
        assert isinstance(component, Component), "Must be component"
        if self.component_exists(component.name):
            raise ValueError(
                f'Component named "{component.name}" already exists!'
            )
        component.bind(self)
        self.__components[component.name] = component

    def add_components(self, components: Iterable[Component[Self]]) -> None:
        "Add multiple components to this manager"
        for component in components:
            self.add_component(component)

    def component_exists(self, component_name: str) -> bool:
        "Return if component exists in this manager"
        return component_name in self.__components

    def components_exist(self, component_names: Iterable[str]) -> bool:
        "Return if all component names given exist in this manager"
        return all(self.component_exists(name) for name in component_names)

    def get_component(self, component_name: str) -> Component[Self]:
        "Return Component or raise ValueError"
        if not self.component_exists(component_name):
            raise ValueError(f'"{component_name}" component does not exist')
        return self.__components[component_name]

    def get_components(
        self, component_names: Iterable[str]
    ) -> list[Component[Self]]:
        "Return iterable of components asked for or raise ValueError"
        return [self.get_component(name) for name in component_names]

    def list_components(self) -> tuple[str, ...]:
        "Return list of components bound to this manager"
        return tuple(self.__components)

    def get_all_components(self) -> tuple[Component[Self], ...]:
        "Return all bound components"
        return tuple(self.__components.values())

    def unbind_components(self) -> None:
        "Unbind all components, allows things to get garbage collected."
        self.__event_handlers.clear()
        for component in iter(self.__components.values()):
            component._unbind()
        self.__components.clear()

    def __del__(self) -> None:
        self.unbind_components()


F = TypeVar("F", bound=Callable[..., Any])


def comps_must_exist(component_names: tuple[str, ...]) -> Callable[[F], F]:
    "Decorator for Components & ComponentManagers to ensure components exist"

    def must_exist_decorator(func: F) -> F:
        "Wrap function and ensure component names exist."

        @functools.wraps(func)
        def must_exist_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if not isinstance(self, (Component, ComponentManager)):
                raise TypeError(
                    "comps_must_exist must wrap a "
                    "Component or ComponentManager function, "
                    f'not "{type(self)}"!'
                )
            if not self.components_exist(component_names):
                raise RuntimeError(
                    f"Not all components from {component_names} exist!"
                )
            return func(self, *args, **kwargs)

        return cast(F, must_exist_wrapper)

    return must_exist_decorator


async def run_async() -> None:
    "Run test asynchronously"
    cat = ComponentManager("cat")
    sound_effect = Component[ComponentManager]("sound_effect")
    cat.add_component(sound_effect)
    print(cat)


def run() -> None:
    "Run test"
    trio.run(run_async)


if __name__ == "__main__":
    print(f"{__title__}\nProgrammed by {__author__}.")
    run()
