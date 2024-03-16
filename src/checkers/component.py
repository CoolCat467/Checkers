"""Component system module -  Components instead of chaotic class hierarchy mess."""

# Programmed by CoolCat467

# Copyright (C) 2023  CoolCat467
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

__title__ = "Component"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "0.0.0"

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from weakref import ref

import trio

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Generator, Iterable

T = TypeVar("T")


class Event(Generic[T]):
    """Event with name, data, and re-raise levels."""

    __slots__ = ("name", "data", "level")

    def __init__(self, name: str, data: T, levels: int = 0) -> None:
        """Initialize event."""
        self.name = name
        self.data = data
        self.level = levels

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"{self.__class__.__name__}({self.name!r}, {self.data!r}, {self.level!r})"

    def pop_level(self) -> bool:
        """Travel up one level and return if should continue or not."""
        continue_level = self.level > 0
        self.level = max(0, self.level - 1)
        return continue_level


class Component:
    """Component base class."""

    __slots__ = ("name", "__manager")

    def __init__(self, name: str) -> None:
        """Initialise with name."""
        self.name = name
        self.__manager: ref[ComponentManager] | None = None

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"{self.__class__.__name__}({self.name!r})"

    @property
    def manager(self) -> ComponentManager:
        """ComponentManager if bound to one, otherwise raise AttributeError."""
        if self.__manager is not None:
            manager = self.__manager()
            if manager is not None:
                return manager
        raise AttributeError(f"No component manager bound for {self.name}")

    def _unbind(self) -> None:
        """If you use this you are evil. This is only for ComponentManagers!."""
        self.__manager = None

    @property
    def manager_exists(self) -> bool:
        """Return if manager is bound or not."""
        return self.__manager is not None and self.__manager() is not None

    def register_handler(
        self,
        event_name: str,
        handler_coro: Callable[[Event[Any]], Awaitable[Any]],
    ) -> None:
        """Register handler with bound component manager."""
        self.manager.register_component_handler(
            event_name,
            handler_coro,
            self.name,
        )

    def register_handlers(
        self,
        handlers: dict[str, Callable[[Event[Any]], Awaitable[Any]]],
    ) -> None:
        """Register multiple handler Coroutines."""
        for name, coro in handlers.items():
            self.register_handler(name, coro)

    def bind_handlers(self) -> None:
        """Add handlers in subclass."""

    def bind(self, manager: ComponentManager) -> None:
        """Bind self to manager."""
        if self.manager_exists:
            raise RuntimeError(
                f"{self.name} component is already bound to {self.manager}",
            )
        self.__manager = ref(manager)
        self.bind_handlers()

    def has_handler(self, event_name: str) -> bool:
        """Return if manager has event handlers registered for a given event."""
        return self.manager.has_handler(event_name)

    async def raise_event(self, event: Event[Any]) -> None:
        """Raise event for bound manager."""
        await self.manager.raise_event(event)

    def component_exists(self, component_name: str) -> bool:
        """Return if component exists in manager."""
        return self.manager.component_exists(component_name)

    def components_exist(self, component_names: Iterable[str]) -> bool:
        """Return if all component names given exist in manager."""
        return self.manager.components_exist(component_names)

    def get_component(self, component_name: str) -> Any:
        """Get Component from manager."""
        return self.manager.get_component(component_name)

    def get_components(
        self,
        component_names: Iterable[str],
    ) -> list[Component]:
        """Return Components from manager."""
        return self.manager.get_components(component_names)


class ComponentManager(Component):
    """Component manager class."""

    __slots__ = ("__event_handlers", "__components", "__weakref__")

    def __init__(self, name: str, own_name: str | None = None) -> None:
        """If own_name is set, add self to list of components as specified name."""
        super().__init__(name)
        self.__event_handlers: dict[
            str,
            set[tuple[Callable[[Event[Any]], Awaitable[Any]], str]],
        ] = {}
        self.__components: dict[str, Component] = {}

        if own_name is not None:
            self.__add_self_as_component(own_name)
        self.bind_handlers()

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"<{self.__class__.__name__} Components: {self.__components}>"

    def __add_self_as_component(self, name: str) -> None:
        """Add this manager as component to self without binding."""
        if self.component_exists(name):  # pragma: nocover
            raise ValueError(f'Component named "{name}" already exists!')
        self.__components[name] = self

    def register_handler(
        self,
        event_name: str,
        handler_coro: Callable[[Event[Any]], Awaitable[None]],
    ) -> None:
        """Register handler_func as handler for event_name (self component)."""
        self.register_component_handler(event_name, handler_coro, self.name)

    def register_component_handler(
        self,
        event_name: str,
        handler_coro: Callable[[Event[Any]], Awaitable[None]],
        component_name: str,
    ) -> None:
        """Register handler_func as handler for event_name."""
        if event_name not in self.__event_handlers:
            self.__event_handlers[event_name] = set()
        self.__event_handlers[event_name].add((handler_coro, component_name))

    def has_handler(self, event_name: str) -> bool:
        """Return if there are event handlers registered for a given event."""
        return bool(self.__event_handlers.get(event_name))

    async def raise_event_in_nursery(
        self,
        event: Event[Any],
        nursery: trio.Nursery,
    ) -> None:
        """Raise event in a particular trio nursery."""
        # Forward leveled events up; They'll come back to us soon enough.
        if self.manager_exists and event.pop_level():
            await super().raise_event(event)
            return

        ##if not event.name.startswith("Pygame") and event.name not in {"tick", "gameboard_create_piece", "server->create_piece", "create_piece->network"}:
        ##    print(f'''{self.__class__.__name__}({self.name!r}):\n{event = }''')

        # Call all registered handlers for this event
        if event.name in self.__event_handlers:
            for handler, _name in self.__event_handlers[event.name]:
                nursery.start_soon(handler, event)

        # Forward events to contained managers
        for component in self.get_all_components():
            # Skip self component if exists
            if component is self:
                continue
            if isinstance(component, ComponentManager):
                nursery.start_soon(component.raise_event, event)

    async def raise_event(self, event: Event[Any]) -> None:
        """Raise event for all components that have handlers registered."""
        async with trio.open_nursery() as nursery:
            await self.raise_event_in_nursery(event, nursery)

    def add_component(self, component: Component) -> None:
        """Add component to this manager."""
        assert isinstance(component, Component), "Must be component instance"
        if self.component_exists(component.name):
            raise ValueError(
                f'Component named "{component.name}" already exists!',
            )
        self.__components[component.name] = component
        component.bind(self)

    def add_components(self, components: Iterable[Component]) -> None:
        """Add multiple components to this manager."""
        for component in components:
            self.add_component(component)

    def remove_component(self, component_name: str) -> None:
        """Remove a component."""
        if not self.component_exists(component_name):
            raise ValueError(f"Component {component_name!r} does not exist!")
        # Remove component from registered components
        component = self.__components.pop(component_name)
        # Tell component they need to unbind
        component._unbind()

        # Unregister component's event handlers
        # List of events that will have no handlers once we are done
        empty = []
        for event_name, handlers in self.__event_handlers.items():
            for item in tuple(handlers):
                handler, handler_component = item
                if handler_component == component_name:
                    self.__event_handlers[event_name].remove(item)
                    if not self.__event_handlers[event_name]:
                        empty.append(event_name)
        # Remove event handler table keys that have no items anymore
        for name in empty:
            self.__event_handlers.pop(name)

    def component_exists(self, component_name: str) -> bool:
        """Return if component exists in this manager."""
        return component_name in self.__components

    @contextmanager
    def temporary_component(
        self,
        component: Component,
    ) -> Generator[None, None, None]:
        """Temporarily add given component but then remove after exit."""
        name = component.name
        self.add_component(component)
        try:
            yield
        finally:
            if self.component_exists(name):
                self.remove_component(name)

    def components_exist(self, component_names: Iterable[str]) -> bool:
        """Return if all component names given exist in this manager."""
        return all(self.component_exists(name) for name in component_names)

    def get_component(self, component_name: str) -> Any:
        """Return Component or raise ValueError."""
        if not self.component_exists(component_name):
            raise ValueError(f'"{component_name}" component does not exist')
        return self.__components[component_name]

    def get_components(self, component_names: Iterable[str]) -> list[Any]:
        """Return iterable of components asked for or raise ValueError."""
        return [self.get_component(name) for name in component_names]

    def list_components(self) -> tuple[str, ...]:
        """Return list of components bound to this manager."""
        return tuple(self.__components)

    def get_all_components(self) -> tuple[Component, ...]:
        """Return all bound components."""
        return tuple(self.__components.values())

    def unbind_components(self) -> None:
        """Unbind all components, allows things to get garbage collected."""
        self.__event_handlers.clear()
        for component in iter(self.__components.values()):
            if (
                isinstance(component, ComponentManager)
                and component is not self
            ):
                component.unbind_components()
            component._unbind()
        self.__components.clear()

    def __del__(self) -> None:
        """Unbind components."""
        self.unbind_components()


class ExternalRaiseManager(ComponentManager):
    """Component Manager, but raises events in an external nursery."""

    __slots__ = ("nursery",)

    def __init__(
        self,
        name: str,
        nursery: trio.Nursery,
        own_name: str | None = None,
    ) -> None:
        """Initialize with name, own component name, and nursery."""
        super().__init__(name, own_name)
        self.nursery = nursery

    async def raise_event(self, event: Event[Any]) -> None:
        """Raise event in nursery."""
        await self.raise_event_in_nursery(event, self.nursery)

    async def raise_event_internal(self, event: Event[Any]) -> None:
        """Raise event in internal nursery."""
        await super().raise_event(event)


if __name__ == "__main__":  # pragma: nocover
    print(f"{__title__}\nProgrammed by {__author__}.")
