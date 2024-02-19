"""Objects - Common objects that are useful."""

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

__title__ = "Objects"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "0.0.0"

from typing import TYPE_CHECKING

from pygame.color import Color
from pygame.draw import rect
from pygame.surface import Surface

from checkers import sprite

if TYPE_CHECKING:
    from pygame.font import Font

    from checkers.component import Event


class Text(sprite.Sprite):
    """Text element.

    Attributes
    ----------
        color: pygame.Color or something pygame.Font.render accepts. Text color.
        font: pygame.font.Font, font used for rendering text.
        text: str, text to display.

    """

    __slots__ = ("__text", "font")

    def __init__(self, name: str, font: Font) -> None:
        """Initialize with font. Defaults to white text."""
        super().__init__(name)

        self.__text = "None"
        self.color = Color(0xFF, 0xFF, 0xFF)
        self.font = font

    def render(self) -> Surface:
        """Render text surface."""
        return self.font.render(self.__text, True, self.color)

    def update_image(self) -> None:
        """Update image."""
        self.image = self.render()

    def __get_text(self) -> str:
        """Return current text."""
        return self.__text

    def __set_text(self, value: str) -> None:
        """Set current text."""
        if value == self.__text:
            return
        self.__text = value
        self.update_image()

    text = property(__get_text, __set_text, doc="Text to display")


class OutlinedText(Text):
    """Outlined Text element.

    Attributes
    ----------
        font: pygame.font.Font, font used for rendering text.
        text: str, text to display.
        color: pygame.color.Color, Text color.
        border_width: int, controls width of border. If <= 0, no border.
        border_radius: int, controls radius of border rounded rect.
        outline: tuple[int, int, int], border outline color.
        inside: tuple[int, int, int], outline interior color.

    """

    __slots__ = ("outline", "inside")

    border_width = 3
    border_radius = 8

    def __init__(self, name: str, font: Font) -> None:
        """Initialize with name and font."""
        super().__init__(name, font)

        self.outline = (0, 0, 0)
        self.inside = (0xFF, 0xFF, 0xFF)
        self.color = Color(0, 0, 0)

    def render(self) -> Surface:
        """Render text and draw outline behind it."""
        text_surf = self.font.render(f" {self.text} ", True, self.color)

        text_rect = text_surf.get_rect()

        extra = self.border_width * 2
        w, h = text_rect.size

        image = Surface((w + extra, h + extra)).convert_alpha()
        image.fill((0, 0, 0, 0))
        rect(
            image,
            self.inside,
            image.get_rect(),
            border_radius=self.border_radius,
        )
        if self.border_width > 0:
            rect(
                image,
                self.outline,
                image.get_rect(),
                width=self.border_width,
                border_radius=self.border_radius,
            )
        image.blit(text_surf, (self.border_width, self.border_width))
        return image


class Button(OutlinedText):
    """Button element.

    Attributes
    ----------
        font: pygame.font.Font, font used for rendering text.
        text: str, text to display.
        color: tuple[int, int, int], Text color.
        border_width: int, controls width of border. If <= 0, no border.
        border_radius: int, controls radius of border rounded rect.
        outline: tuple[int, int, int], border outline color.
        inside: tuple[int, int, int], outline interior color.

    Components:
        DragClickEventComponent

    Events Used:
        click

    """

    __slots__ = ()

    def __init__(self, name: str, font: Font) -> None:
        """Initialize with name and font."""
        super().__init__(name, font)

        self.add_component(sprite.DragClickEventComponent())

    async def handle_click(
        self,
        event: Event[sprite.PygameMouseButtonEventData],
    ) -> None:
        """Handle click events."""

    def bind_handlers(self) -> None:
        """Register click handler."""
        super().bind_handlers()
        self.register_handler("click", self.handle_click)
