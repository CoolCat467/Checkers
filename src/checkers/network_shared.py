"""Shared network code."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, NamedTuple, TypeAlias

import trio

from .base_io import StructFormat

if TYPE_CHECKING:
    from .buffer import Buffer

ADVERTISEMENT_IP: Final = "224.0.2.60"
ADVERTISEMENT_PORT: Final = 4445

DEFAULT_PORT: Final = 31613

Pos: TypeAlias = tuple[int, int]


class TickEventData(NamedTuple):

    """Tick Event Data."""

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


# Stolen from WOOF (Web Offer One File), Copyright (C) 2004-2009 Simon Budig,
# available at http://www.home.unix-ag.org/simon/woof
# with modifications

# Utility function to guess the IP (as a string) where the server can be
# reached from the outside. Quite nasty problem actually.


async def find_ip() -> str:
    """Guess the IP where the server can be found from the network."""
    # we get a UDP-socket for the TEST-networks reserved by IANA.
    # It is highly unlikely, that there is special routing used
    # for these networks, hence the socket later should give us
    # the IP address of the default route.
    # We're doing multiple tests, to guard against the computer being
    # part of a test installation.

    candidates: list[str] = []
    for test_ip in ("192.0.2.0", "198.51.100.0", "203.0.113.0"):
        sock = trio.socket.socket(trio.socket.AF_INET, trio.socket.SOCK_DGRAM)
        await sock.connect((test_ip, 80))
        ip_addr: str = sock.getsockname()[0]
        sock.close()
        if ip_addr in candidates:
            return ip_addr
        candidates.append(ip_addr)

    return candidates[0]
