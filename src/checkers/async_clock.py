#!/usr/bin/env python3
# Async Clock - Asynchronous version of pygame.time.Clock

"Asynchronous FPS clock"

# Programmed by CoolCat467

__title__ = "Async Clock"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import pygame.time
import trio


class Clock:
    "pygame.time.Clock but with asynchronous tick"
    __slots__ = (
        "fps_tick",
        "timepassed",
        "rawpassed",
        "last_tick",
        "fps",
        "fps_count",
    )

    def __init__(self) -> None:
        self.fps_tick = 0
        self.timepassed = 0
        self.rawpassed = 0
        self.last_tick = pygame.time.get_ticks()
        self.fps = 0.0
        self.fps_count = 0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.fps:2f})>"

    def get_fps(self) -> float:
        "compute the clock framerate"
        return self.fps

    def get_rawtime(self) -> int:
        "actual time used in the previous tick"
        return self.rawpassed

    def get_time(self) -> int:
        "time used in the previous tick"
        return self.timepassed

    async def tick(self, framerate: int = 0) -> int:
        "update the clock"
        if framerate > 0:
            endtime = 1000 // framerate
        else:
            endtime = 0
        self.rawpassed = pygame.time.get_ticks() - self.last_tick
        delay = endtime - self.rawpassed
        if delay > 0:
            await trio.sleep(delay / 1000)

        nowtime = pygame.time.get_ticks()
        self.timepassed = nowtime - self.last_tick
        self.fps_count += 1
        self.last_tick = nowtime

        if not self.fps_tick:
            self.fps_count = 0
            self.fps_tick = nowtime
        if self.fps_count >= 10:
            self.fps = self.fps_count / ((nowtime - self.fps_tick) / 1000)
            self.fps_count = 0
            self.fps_tick = nowtime
        return self.timepassed


if __name__ == "__main__":  # pragma: nocover
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
