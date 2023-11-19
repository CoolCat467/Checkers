"""Machine Client - Checkers game client that can be controlled mechanically"""

from __future__ import annotations

__title__ = "Machine Client"
__author__ = "CoolCat467"
__version__ = "0.0.0"

from abc import ABCMeta, abstractmethod

import trio
from checkers.client import GameClient
from checkers.component import (
    Component,
    ComponentManager,
    Event,
    ExternalRaiseManager,
)
from checkers.state import Action, Pos, State

PORT = 31613


# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3


class RemoteState(Component, metaclass=ABCMeta):

    """Remote State

    Keeps track of game state and call preform_action when it's this clients
    turn.
    """

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
            },
        )

    async def preform_action(self, action: Action) -> None:
        """Raise events to perform game action."""
        await self.raise_event(
            Event(
                "gameboard_piece_clicked",
                (
                    action.from_pos,
                    self.state.pieces[action.from_pos],
                ),
            ),
        )
        await self.raise_event(Event("gameboard_tile_clicked", action.to_pos))

    @abstractmethod
    async def preform_turn(self) -> Action:
        """Perform turn, return action to perform"""

    async def base_preform_turn(self) -> None:
        """Perform turn"""
        if self.state.check_for_win() is not None:
            print("Terminal state, not performing turn")
            return
        action = await self.preform_turn()
        await self.preform_action(action)

    async def handle_action_complete(
        self,
        event: Event[tuple[Pos, Pos, int]],
    ) -> None:
        """Perform action on internal state and perform our turn if possible."""
        from_pos, to_pos, turn = event.data
        action = self.state.action_from_points(from_pos, to_pos)
        self.state = self.state.preform_action(action)
        ##        print(f'{turn = }')
        if turn == self.playing_as:
            await self.base_preform_turn()

    async def handle_create_piece(self, event: Event[tuple[Pos, int]]) -> None:
        """Update internal pieces if we haven't had the initial setup event."""
        if self.has_initial:
            return
        pos, type_ = event.data
        self.pieces[pos] = type_

    async def handle_initial_config(
        self,
        event: Event[tuple[Pos, int]],
    ) -> None:
        """Set up initial state and perform our turn if possible."""
        board_size, turn = event.data
        self.state = State(board_size, bool(turn), self.pieces)
        self.has_initial = True
        if turn == self.playing_as:
            await self.base_preform_turn()

    async def handle_game_over(self, event: Event[int]) -> None:
        """Raise network_stop event so we disconnect from server."""
        self.has_initial = False
        await self.raise_event(Event("network_stop", None))


class MachineClient(ComponentManager):

    """Manager that runs until client_disconnected event fires."""

    __slots__ = ("running",)

    def __init__(self, remote_state_class: type[RemoteState]) -> None:
        super().__init__("machine_client")

        self.running = True

        self.add_components((remote_state_class(), GameClient("game_client")))

    def bind_handlers(self) -> None:
        self.register_handlers(
            {"client_disconnected": self.handle_client_disconnected},
        )

    ##    async def raise_event(self, event: Event) -> None:
    ##        """Raise event but also log it if not tick."""
    ##        if event.name not in {"tick"}:
    ##            print(f'{event = }')
    ##        return await super().raise_event(event)

    async def handle_client_disconnected(self, event: Event[None]) -> None:
        """Set self.running to false on network disconnect."""
        self.running = False


async def run_client(
    host: str,
    port: int,
    remote_state_class: type[RemoteState],
) -> None:
    """Run machine client and raise tick events."""
    async with trio.open_nursery() as main_nursery:
        event_manager = ExternalRaiseManager(
            "checkers",
            main_nursery,
            "client",
        )
        client = MachineClient(remote_state_class)
        event_manager.add_component(client)
        await event_manager.raise_event(Event("client_connect", (host, port)))
        print("Connected to server")
        while client.running:
            # Wait so backlog things happen
            await trio.sleep(1)
        client.unbind_components()


def run_client_sync(
    host: int,
    port: int,
    remote_state_class: type[RemoteState],
) -> None:
    """Synchronous entry point."""
    trio.run(run_client, host, port, remote_state_class)
