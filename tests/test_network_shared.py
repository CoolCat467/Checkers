from __future__ import annotations

from libcomponent.buffer import Buffer

from checkers.network_shared import read_position, write_position


def test_read_position() -> None:
    buffer = Buffer(b"\r\x12")

    assert read_position(buffer) == (13, 18)


def test_write_position() -> None:
    buffer = Buffer()

    write_position(buffer, (13, 18))
    assert buffer == b"\r\x12"
