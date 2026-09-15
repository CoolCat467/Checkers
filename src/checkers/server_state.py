"""Server State."""

# Programmed by CoolCat467

from __future__ import annotations

# Server State
# Copyright (C) 2023-2025  CoolCat467
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

__title__ = "Server State"
__author__ = "CoolCat467"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"


from collections import deque
from typing import TYPE_CHECKING

from checkers.state import State

if TYPE_CHECKING:
    from collections.abc import Iterable

    from mypy_extensions import u8

    from checkers.network_shared import Pos


class CheckersState(State):
    """Subclass of State that keeps track of actions in `action_queue`."""

    __slots__ = ("action_queue",)

    def __init__(
        self,
        size: Pos,
        pieces: dict[Pos, u8],
        turn: bool = True,
    ) -> None:
        """Initialize Checkers State."""
        super().__init__(size, pieces, turn)
        self.action_queue: deque[tuple[str, Iterable[Pos | u8]]] = deque()

    def piece_kinged(self, piece_pos: Pos, new_type: u8) -> None:
        """Add king event to action queue."""
        super().piece_kinged(piece_pos, new_type)
        self.action_queue.append(("king", (piece_pos, new_type)))

    def piece_moved(self, start_pos: Pos, end_pos: Pos) -> None:
        """Add move event to action queue."""
        super().piece_moved(start_pos, end_pos)
        self.action_queue.append(
            (
                "move",
                (
                    start_pos,
                    end_pos,
                ),
            ),
        )

    def piece_jumped(self, jumped_piece_pos: Pos) -> None:
        """Add jump event to action queue."""
        super().piece_jumped(jumped_piece_pos)
        self.action_queue.append(("jump", (jumped_piece_pos,)))

    def get_action_queue(self) -> deque[tuple[str, Iterable[Pos | u8]]]:
        """Return action queue."""
        return self.action_queue


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
