"""Objects - Common objects that are useful."""

# Programmed by CoolCat467

from __future__ import annotations

# Copyright (C) 2023  CoolCat467
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

__title__ = "Objects"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "0.0.0"


from typing import TYPE_CHECKING

from pygame.color import Color
from pygame.draw import rect
from pygame.locals import SRCALPHA
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

    def __init__(self, name: object, font: Font) -> None:
        """Initialize with font. Defaults to white text."""
        super().__init__(name)

        self.__text = "None"
        self.color: Color | tuple[int, int, int] = Color(0xFF, 0xFF, 0xFF)
        self.font = font

    def render_multiline(self, text: str, y_sep: int = 0) -> list[Surface]:
        """Return list of rendered line surfaces."""
        if not text:
            return [self.font.render("", True, self.color)]
        lines = text.splitlines()
        return [self.font.render(line, True, self.color) for line in lines]

    def render_multiline_surf(
        self,
        text: str,
        y_sep: int = 0,
    ) -> Surface:
        """Return rendered multiline text surface."""
        surfaces = self.render_multiline(text, y_sep)
        if len(surfaces) == 1:
            return surfaces[0]

        total_y_sep = y_sep * len(surfaces) - 1
        height = (
            sum(surface.get_size()[1] for surface in surfaces) + total_y_sep
        )
        width = max(surface.get_width() for surface in surfaces)

        image = Surface((width, height), flags=SRCALPHA)
        image.fill((0, 0, 0, 0))

        y = 0
        for surface in surfaces:
            image.blit(surface, (0, y))
            y += y_sep + surface.get_size()[1]
        return image

    def render(self) -> Surface:
        """Render text surface."""
        return self.render_multiline_surf(self.__text)

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

    def __init__(self, name: object, font: Font) -> None:
        """Initialize with name and font."""
        super().__init__(name, font)

        self.outline = (0, 0, 0)
        self.inside = (0xFF, 0xFF, 0xFF)
        self.color = Color(0, 0, 0)

    def render(self) -> Surface:
        """Render text and draw outline behind it."""
        text = "\n".join(f" {line} " for line in self.text.splitlines())
        text_surf = self.render_multiline_surf(text)

        text_rect = text_surf.get_rect()

        extra = self.border_width * 2
        w, h = text_rect.size

        image = Surface((w + extra, h + extra), flags=SRCALPHA)
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

    def __init__(self, name: object, font: Font) -> None:
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
