"""Shared network code."""

# Programmed by CoolCat467

# Copyright (C) 2023-2024  CoolCat467
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

__title__ = "Network Shared"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"

from typing import TYPE_CHECKING, Final, NamedTuple, TypeAlias

import trio
from mypy_extensions import u8

from .base_io import StructFormat

if TYPE_CHECKING:
    from .buffer import Buffer

ADVERTISEMENT_IP: Final = "224.0.2.60"
ADVERTISEMENT_PORT: Final = 4445

DEFAULT_PORT: Final = 31613

Pos: TypeAlias = tuple[u8, u8]


class TickEventData(NamedTuple):
    """Tick Event Data."""

    time_passed: float
    fps: float


def read_position(buffer: Buffer) -> Pos:
    """Read a position tuple from buffer."""
    pos_x: u8 = buffer.read_value(StructFormat.UBYTE)
    pos_y: u8 = buffer.read_value(StructFormat.UBYTE)

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
