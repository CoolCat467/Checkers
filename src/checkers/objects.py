#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Objects - Common objects that are useful

"Objects"

# Programmed by CoolCat467

__title__ = "Objects"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import sprite
from pygame.color import Color
from pygame.font import Font


class Text(sprite.Sprite):
    "Text element"
    __slots__ = ("__text", "font")

    def __init__(self, name: str, font: Font) -> None:
        super().__init__(name)

        self.__text = "None"
        self.color = Color(0xFF, 0xFF, 0xFF)
        self.font = font
        self.text = ""
        self.visible = True

    def update_image(self) -> None:
        "Update image"
        self.image = self.font.render(self.__text, True, self.color)

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
