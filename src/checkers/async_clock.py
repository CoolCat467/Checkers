"""Asynchronous Clock - Asynchronous version of pygame.time.Clock."""

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

__title__ = "Async Clock"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "0.0.0"


from time import perf_counter_ns
from typing import NewType

import trio

nanoseconds = NewType("nanoseconds", int)


def get_ticks() -> nanoseconds:
    """Get Ticks."""
    return nanoseconds(perf_counter_ns())


class Clock:
    """pygame.time.Clock but with asynchronous tick."""

    __slots__ = (
        "fps",
        "fps_count",
        "fps_tick",
        "last_tick",
        "rawpassed",
        "timepassed",
    )

    def __init__(self) -> None:
        """Initialize variables."""
        self.fps_tick = nanoseconds(0)
        self.timepassed = nanoseconds(0)
        self.rawpassed = nanoseconds(0)
        self.last_tick: nanoseconds = get_ticks()
        self.fps = 0.0
        self.fps_count = 0

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"<{self.__class__.__name__}({self.fps:2f})>"

    def get_fps(self) -> float:
        """Return the clock framerate in Frames Per Second."""
        return self.fps

    def get_rawtime(self) -> nanoseconds:
        """Return the actual time used in the previous tick in nanoseconds (original was milliseconds)."""
        return self.rawpassed

    def get_time(self) -> nanoseconds:
        """Return time used in the previous tick (in nanoseconds, original was milliseconds)."""
        return self.timepassed

    async def tick(self, framerate: int = 0) -> int:
        """Tick the clock. Return time passed in nanoseconds, same as get_time (original was milliseconds)."""
        endtime = 1000000000 // framerate if framerate > 0 else 0
        self.rawpassed = nanoseconds(get_ticks() - self.last_tick)
        delay = endtime - self.rawpassed
        if delay > 0:
            await trio.sleep(delay / 1e9)  # nanoseconds -> seconds
        else:
            await trio.lowlevel.checkpoint()

        nowtime: nanoseconds = get_ticks()
        self.timepassed = nanoseconds(nowtime - self.last_tick)
        self.fps_count += 1
        self.last_tick = nowtime

        if not self.fps_tick:
            self.fps_count = 0
            self.fps_tick = nowtime
        if self.fps_count >= 10:
            self.fps = self.fps_count / (
                (nowtime - self.fps_tick) / 1e9
            )  # nanoseconds -> seconds
            self.fps_count = 0
            self.fps_tick = nowtime
        return self.timepassed


if __name__ == "__main__":  # pragma: nocover
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
