"""Element List - List of element sprites."""

# Programmed by CoolCat467

from __future__ import annotations

# Element List - List of element sprites.
# Copyright (C) 2024  CoolCat467
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

__title__ = "Element List"
__author__ = "CoolCat467"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"


from typing import TYPE_CHECKING

from checkers import sprite
from checkers.vector import Vector2

if TYPE_CHECKING:
    from collections.abc import Generator


class Element(sprite.Sprite):
    """Element sprite."""

    __slots__ = ()

    def self_destruct(self) -> None:
        """Remove this element."""
        self.kill()
        if self.manager_exists:
            self.manager.remove_component(self.name)

    def __del__(self) -> None:
        """Clean up this element for garbage collecting."""
        self.self_destruct()
        super().__del__()


class ElementList(sprite.Sprite):
    """Element List sprite."""

    __slots__ = ("_order",)

    def __init__(self, name: object) -> None:
        """Initialize connection list."""
        super().__init__(name)

        self._order: list[object] = []

    def add_element(self, element: Element) -> None:
        """Add element to this list."""
        group = self.groups()[-1]
        group.add(element)  # type: ignore[arg-type]
        self.add_component(element)
        self._order.append(element.name)

    def delete_element(self, element_name: object) -> None:
        """Delete an element (only from component)."""
        element = self.get_component(element_name)
        index = self._order.index(element_name)
        if element.visible:
            assert element.image is not None
            height = element.image.get_height()
            self.offset_elements_after(index, (0, -height))
        self._order.pop(index)
        assert isinstance(element, Element)
        element.self_destruct()

    def yield_elements(self) -> Generator[Element, None, None]:
        """Yield bound Element components in order."""
        for component_name in iter(self._order):
            # Kind of strange to mutate in yield, maybe shouldn't do that?
            if not self.component_exists(component_name):
                self._order.remove(component_name)
                continue
            component = self.get_component(component_name)
            assert isinstance(component, Element)
            yield component

    def get_last_rendered_element(self) -> Element | None:
        """Return last bound Element sprite or None."""
        for component_name in reversed(self._order):
            if not self.component_exists(component_name):
                self._order.remove(component_name)
                continue
            component = self.get_component(component_name)
            assert isinstance(component, Element)
            if component.visible:
                assert component.image is not None
                return component
        return None

    def get_new_connection_position(self) -> Vector2:
        """Return location for new connection."""
        last_element = self.get_last_rendered_element()
        if last_element is None:
            return Vector2.from_iter(self.rect.topleft)
        location = Vector2.from_iter(last_element.rect.topleft)
        assert last_element.image is not None
        location += (0, last_element.image.get_height())
        return location

    def offset_elements(self, diff: tuple[int, int]) -> None:
        """Offset all element locations by given difference."""
        for element in self.yield_elements():
            element.location += diff

    def offset_elements_after(self, index: int, diff: tuple[int, int]) -> None:
        """Offset elements after index by given difference."""
        for idx, element in enumerate(self.yield_elements()):
            if idx <= index:
                continue
            element.location += diff

    def _set_location(self, value: tuple[int, int]) -> None:
        """Set rect center from tuple of integers."""
        current = self.location
        super()._set_location(value)
        diff = Vector2.from_iter(value) - current
        self.offset_elements(diff)


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
