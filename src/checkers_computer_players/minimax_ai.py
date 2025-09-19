#!/usr/bin/env python3
# AI that plays checkers.

"""Minimax Checkers AI."""

# Programmed by CoolCat467

from __future__ import annotations

# Minimax Checkers AI
# Copyright (C) 2024-2025  CoolCat467
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

__title__ = "Minimax AI"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import traceback
from typing import TYPE_CHECKING, TypeVar

from checkers_computer_players.checkers_minimax import CheckersMinimax
from checkers_computer_players.machine_client import (
    RemoteState,
    run_clients_in_local_servers_sync,
)

if TYPE_CHECKING:
    from checkers.state import Action

T = TypeVar("T")

# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3


class MinimaxPlayer(RemoteState):
    """Minimax Player."""

    __slots__ = ("minimax",)

    def __init__(self) -> None:
        """Initialize minimax player."""
        super().__init__()

        self.minimax = CheckersMinimax()

    async def perform_turn(self) -> Action:
        """Perform turn."""
        print("perform_turn")
        ##value, action = CheckersMinimax.adaptive_depth_minimax(
        ##    self.state, 4, 5
        ##)
        ##value, action = CheckersMinimax.minimax(self.state, 4)
        ##value, action = CheckersMinimax.alphabeta(self.state, 4)
        value, action = self.minimax.iterative_deepening(
            self.state,
            4,
            20,
            int(5 * 1e9),
        )
        if action is None:
            raise ValueError("action is None")
        print(f"{value = }")
        return action


def run() -> None:
    """Run MinimaxPlayer clients in local server."""
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    try:
        run_clients_in_local_servers_sync(MinimaxPlayer)
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    run()
