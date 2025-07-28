"""Clock - Clock ticks."""

# Programmed by CoolCat467

from __future__ import annotations

# Clock - Clock ticks
# Copyright (C) 2025  CoolCat467
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

__title__ = "Clock Ticking"
__author__ = "CoolCat467"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"


import time
from typing import Final

import pygame
import pygame.locals
import trio

SECOND_NANOS: Final = 1_000_000_000


async def main() -> None:
    """Run program async."""
    here = await trio.Path(__file__).absolute()
    tick = pygame.mixer.Sound(here.parent / "tick.mp3")
    counter = 1

    print("Control+C to close.\n")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                break

        offset = time.time_ns() % SECOND_NANOS
        delay_nanos = SECOND_NANOS - offset
        delay = delay_nanos / SECOND_NANOS

        try:
            await trio.sleep(delay)
        except KeyboardInterrupt:
            print("Closing from keyboard interrupt")
            break
        tick.play()

        # Alternating between full and half volume
        counter += 1
        counter %= 2
        tick.set_volume((counter + 1) / 2)


def run() -> None:
    """Run program."""
    pygame.init()
    try:
        trio.run(main, restrict_keyboard_interrupt_to_checkpoints=True)
    finally:
        pygame.quit()


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    run()
