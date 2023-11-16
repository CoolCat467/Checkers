"""Shared network code."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, NamedTuple, TypeAlias

from .base_io import StructFormat

if TYPE_CHECKING:
    from .buffer import Buffer

ADVERTISEMENT_IP: Final = "224.0.2.60"
ADVERTISEMENT_PORT: Final = 4445

Pos: TypeAlias = tuple[int, int]


class TickEventData(NamedTuple):
    """Tick Event Data"""

    time_passed: float
    fps: float


def read_position(buffer: Buffer) -> Pos:
    """Read a position tuple from buffer."""
    pos_x = buffer.read_value(StructFormat.UBYTE)
    pos_y = buffer.read_value(StructFormat.UBYTE)

    return pos_x, pos_y


def write_position(buffer: Buffer, pos: Pos) -> None:
    """Write a position tuple to buffer."""
    pos_x, pos_y = pos
    buffer.write_value(StructFormat.UBYTE, pos_x)
    buffer.write_value(StructFormat.UBYTE, pos_y)
