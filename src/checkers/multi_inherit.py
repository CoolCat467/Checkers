"""Objects that inherit from multipls base classes because mypyc is dumb."""

# Programmed by CoolCat467

from __future__ import annotations

# Objects that inherit from multipls base classes because mypyc is dumb
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

__title__ = "Multi-inherit Objects"
__author__ = "CoolCat467"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"


from typing import TYPE_CHECKING

from checkers import element_list, objects
from checkers.component import Event

if TYPE_CHECKING:
    import pygame

    from checkers import sprite


class ReturnElement(element_list.Element, objects.Button):
    """Connection list return to title element sprite."""

    __slots__ = ()

    def __init__(self, name: str, font: pygame.font.Font) -> None:
        """Initialize return element."""
        super().__init__(name, font)

        self.update_location_on_resize = False
        self.border_width = 4
        self.text = "Return to Title"
        self.visible = True

    async def handle_click(
        self,
        _: Event[sprite.PygameMouseButtonEventData],
    ) -> None:
        """Handle Click Event."""
        await self.raise_event(
            Event("return_to_title", None, 2),
        )


class ConnectionElement(element_list.Element, objects.Button):
    """Connection list element sprite."""

    __slots__ = ()

    def __init__(
        self,
        name: tuple[str, int],
        font: pygame.font.Font,
        motd: str,
    ) -> None:
        """Initialize connection element."""
        super().__init__(name, font)

        self.text = f"[{name[0]}:{name[1]}]\n{motd}"
        self.visible = True

    async def handle_click(
        self,
        _: Event[sprite.PygameMouseButtonEventData],
    ) -> None:
        """Handle Click Event."""
        details = self.name
        await self.raise_event(
            Event("join_server", details, 2),
        )
