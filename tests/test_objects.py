from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pygame.surface import Surface

from checkers.objects import Button, OutlinedText, Text

if TYPE_CHECKING:
    from pygame.font import Font


class MockSurface(Surface):
    """Mocking a pygame surface for testing."""

    __slots__ = ("text_data",)

    def __init__(self, text_data: str = "") -> None:
        super().__init__((0, 0))
        self.text_data = text_data


class MockFont:
    """Mocking a pygame font for testing."""

    __slots__ = ()

    def render(
        self,
        text: str,
        antialias: bool,
        color: tuple[int, int, int],
    ) -> MockSurface:
        """Fake render method."""
        return MockSurface(text)


@pytest.fixture
def font() -> MockFont:
    return MockFont()


def test_text_initialization(font: Font) -> None:
    text = Text("TestText", font)
    assert text.text == "None"
    assert text.color == (255, 255, 255)
    assert text.font == font


def test_text_rendering(font: Font) -> None:
    text = Text("TestText", font)
    assert text.image is None


def test_text_rendering_blank(font: Font) -> None:
    text = Text("TestText", font)
    text.text = ""
    text.text = ""
    assert text.image.text_data == ""


def test_outlined_text_initialization(font: Font) -> None:
    outlined_text = OutlinedText("TestOutlinedText", font)
    assert outlined_text.outline == (0, 0, 0)
    assert outlined_text.inside == (255, 255, 255)


def test_outlined_text_rendering(font: Font) -> None:
    outlined_text = OutlinedText("TestOutlinedText", font)
    outlined_text.text = "Outlined Text"
    assert outlined_text.text == "Outlined Text"


def test_outlined_text_rendering_zero_border(font: Font) -> None:
    outlined_text = OutlinedText("TestOutlinedText", font)
    outlined_text.border_width = 0
    outlined_text.text = "Outlined Text"
    assert isinstance(outlined_text.image, Surface)


def test_button_initialization(font: Font) -> None:
    button = Button("TestButton", font)
    assert button.text == "None"
    assert button.color == (0, 0, 0, 255)  # type: ignore[comparison-overlap]
    assert button.border_width == 3
