#!/usr/bin/env python3
# AI that plays checkers.

# IMPORTANT NOTE:
# For the game to recognize this as an
# AI, it's filename should have the words
# 'AI' in it.

__title__ = "Minimax AI"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import math
from collections import Counter
from collections.abc import Iterable
from typing import TypeVar

import trio
from checkers import GameClient
from component import Component, ComponentManager, Event, ExternalRaiseManager
from minimax import Minimax, MinimaxResult, Player
from state import Action, Pos, State

T = TypeVar("T")

PORT = 31613


# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3


class CheckersMinimax(Minimax[State, Action]):
    """Minimax Algorithm for Checkers"""

    __slots__ = ()

    @staticmethod
    def value(state: State) -> int | float:
        # Return winner if possible
        win = state.check_for_win()
        # If no winner, we have to predict the value
        if win is None:
            # We'll estimate the value by the pieces in play
            counts = Counter(state.pieces.values())
            # Score is pawns plus 3 times kings
            min_ = counts[0] + 3 * counts[2]
            max_ = counts[1] + 3 * counts[3]
            # More max will make score higher,
            # more min will make score lower
            # Plus one in divisor makes so never / 0
            return (max_ - min_) / (max_ + min_ + 1)
        return win * 2 - 1

    @staticmethod
    def terminal(state: State) -> bool:
        return state.check_for_win() is not None

    @staticmethod
    def player(state: State) -> Player:
        return Player.MAX if state.get_turn() else Player.MIN

    @staticmethod
    def actions(state: State) -> Iterable[Action]:
        return state.get_all_actions(int(state.get_turn()))

    @staticmethod
    def result(state: State, action: Action) -> State:
        return state.preform_action(action)

    @classmethod
    def adaptive_depth_minimax(
        cls, state: State, minimum: int, maximum: int
    ) -> MinimaxResult[Action]:
        ##        types = state.pieces.values()
        ##        current = len(types)
        ##        w, h = state.size
        ##        max_count = w * h // 6 << 1
        ##        old_depth = (1 - (current / max_count)) * math.floor(
        ##            math.sqrt(w**2 + h**2)
        ##        )

        depth = cls.value(state) * maximum + minimum
        final_depth = min(maximum, max(minimum, math.floor(depth)))
        print(f"{depth = } {final_depth = }")
        return cls.minimax(state, final_depth)


class RemoteState(Component):
    __slots__ = ("state", "pieces", "has_initial", "playing_as")

    def __init__(self) -> None:
        super().__init__("remote_state")

        self.state = State((8, 8), False, {})
        self.has_initial = False
        self.pieces: dict[Pos, int] = {}

        self.playing_as = 1

    def bind_handlers(self) -> None:
        self.register_handlers(
            {
                "game_action_complete": self.handle_action_complete,
                "game_winner": self.handle_game_over,
                "game_initial_config": self.handle_initial_config,
                "gameboard_create_piece": self.handle_create_piece,
            }
        )

    async def preform_turn(self) -> None:
        """Preform turn"""
        print("preform_turn")
        if CheckersMinimax.terminal(self.state):
            print("Terminal state, not preforming turn")
            return
        value, action = CheckersMinimax.adaptive_depth_minimax(
            self.state, 4, 5
        )
        print(f"{value = }")
        await self.raise_event(
            Event(
                "gameboard_piece_clicked",
                (
                    action.from_pos,
                    self.state.pieces[action.from_pos],
                ),
            )
        )
        await self.raise_event(Event("gameboard_tile_clicked", action.to_pos))

    async def handle_action_complete(
        self, event: Event[tuple[Pos, Pos, int]]
    ) -> None:
        """Preform action on internal state and preform our turn if possible."""
        from_pos, to_pos, turn = event.data
        action = self.state.action_from_points(from_pos, to_pos)
        self.state = self.state.preform_action(action)
        ##        print(f'{turn = }')
        if turn == self.playing_as:
            await self.preform_turn()

    async def handle_create_piece(self, event: Event[tuple[Pos, int]]) -> None:
        """Update interal pieces if we haven't had the initial setup event."""
        if self.has_initial:
            return
        pos, type_ = event.data
        self.pieces[pos] = type_

    async def handle_initial_config(
        self, event: Event[tuple[Pos, int]]
    ) -> None:
        """Set up initial state and preform our turn if possible."""
        board_size, turn = event.data
        self.state = State(board_size, turn, self.pieces)
        self.has_initial = True
        if turn == self.playing_as:
            await self.preform_turn()

    async def handle_game_over(self, event: Event[int]) -> None:
        """Raise network_stop event so we disconnect from server."""
        self.has_initial = False
        await self.raise_event(Event("network_stop", None))


class MachineClient(ComponentManager):
    __slots__ = ("running",)

    def __init__(self) -> None:
        super().__init__("machine_client")

        self.running = True

        self.add_components((RemoteState(), GameClient("game_client")))

    def bind_handlers(self) -> None:
        self.register_handlers({"network_stop": self.handle_network_stop})

    ##    async def raise_event(self, event: Event) -> None:
    ##        """Raise event but also log it if not tick."""
    ##        if event.name not in {"tick"}:
    ##            print(f'{event = }')
    ##        return await super().raise_event(event)

    async def handle_network_stop(self, event: Event[None]) -> None:
        """Set self.running to false on network disconnect."""
        self.running = False


async def run_client() -> None:
    """Run machine client and raise tick events."""
    async with trio.open_nursery() as main_nursery:
        event_manager = ExternalRaiseManager(
            "checkers", main_nursery, "client"
        )
        client = MachineClient()
        event_manager.add_component(client)
        await event_manager.raise_event(
            Event("client_connect", ("127.0.0.1", PORT))
        )
        print("Connected to server")
        while client.running:
            await event_manager.raise_event(Event("tick", None))

            # Not sure why we need this but nothing seems to work without it...
            await trio.sleep(0.01)


def run() -> None:
    """Synchronous entry point."""
    trio.run(run_client)


if __name__ == "__main__":
    run()
