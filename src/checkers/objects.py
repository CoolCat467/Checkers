#!/usr/bin/env python3
# Objects - Common objects that are useful

"Objects"

# Programmed by CoolCat467

__title__ = "Objects"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import sprite
from component import Event
from pygame.color import Color
from pygame.draw import rect
from pygame.font import Font
from pygame.surface import Surface


class Text(sprite.Sprite):
    "Text element"
    __slots__ = ("__text", "font")

    def __init__(self, name: str, font: Font) -> None:
        super().__init__(name)

        self.__text = "None"
        self.color = Color(0xFF, 0xFF, 0xFF)
        self.font = font

    def render(self) -> Surface:
        """Render text surface"""
        return self.font.render(self.__text, True, self.color)

    def update_image(self) -> None:
        "Update image"
        self.image = self.render()

    def __get_text(self) -> str:
        "Get text"
        return self.__text

    def __set_text(self, value: str) -> None:
        "Set text"
        if value == self.__text:
            return
        self.__text = value
        self.update_image()

    text = property(__get_text, __set_text, doc="Text to display")


class OutlinedText(Text):
    "Outlined Text element"
    __slots__ = ("outline", "inside")

    border_width = 3
    border_radius = 8

    def __init__(self, name: str, font: Font) -> None:
        super().__init__(name, font)

        self.outline = (0, 0, 0)
        self.inside = (0xFF, 0xFF, 0xFF)
        self.color = (0, 0, 0)

    def render(self) -> Surface:
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
    "Button element"
    __slots__ = ()

    def __init__(self, name: str, font: Font) -> None:
        super().__init__(name, font)

        self.add_component(sprite.DragClickEventComponent())

    async def handle_click(
        self, event: Event[dict[str, tuple[int, int] | int]]
    ) -> None:
        """Handle ckick events"""

    def bind_handlers(self) -> None:
        super().bind_handlers()
        self.register_handler("click", self.handle_click)
