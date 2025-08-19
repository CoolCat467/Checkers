"""Machine Client - Checkers game client that can be controlled mechanically."""

from __future__ import annotations

__title__ = "Machine Client"
__author__ = "CoolCat467"
__version__ = "0.0.0"

import sys
from abc import ABCMeta, abstractmethod
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import trio
from libcomponent.component import (
    Component,
    ComponentManager,
    Event,
    ExternalRaiseManager,
)

from checkers.client import GameClient, read_advertisements
from checkers.state import Action, Pos, State

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

if sys.version_info < (3, 11):
    from exceptiongroup import BaseExceptionGroup

# Player:
# 0 = False = Person  = MIN = 0, 2
# 1 = True  = AI (Us) = MAX = 1, 3


class BaseRemoteState(Component, metaclass=ABCMeta):
    """Remote State.

    Keeps track of game state and call handle_perform_turn when it's
    this clients turn.
    """

    __slots__ = ("has_initial", "moves", "pieces", "playing_as", "state")

    def __init__(self, name: str = "remote_state") -> None:
        """Initialize remote state."""
        super().__init__(name)

        self.state = State((8, 8), {})
        self.has_initial = False
        self.pieces: dict[Pos, int] = {}

        self.playing_as = 1
        self.moves = 0

    def bind_handlers(self) -> None:
        """Register game event handlers."""
        self.register_handlers(
            {
                "game_action_complete": self.handle_action_complete,
                "game_winner": self.handle_game_over,
                "game_initial_config": self.handle_initial_config,
                "game_playing_as": self.handle_playing_as,
                "gameboard_create_piece": self.handle_create_piece,
            },
        )

    async def perform_action(self, action: Action) -> None:
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
    async def handle_perform_turn(self) -> None:
        """Handle perform turn. Should call await self.perform_action(action)."""

    async def base_perform_turn(self) -> None:
        """Perform turn."""
        self.moves += 1
        winner = self.state.check_for_win()
        if winner is not None:
            print("Terminal state, not performing turn")
            value = ("Lost", "Won")[winner == self.playing_as]
            print(f"{value} after {self.moves}")
            return
        await self.handle_perform_turn()

    async def handle_action_complete(
        self,
        event: Event[tuple[Pos, Pos, int]],
    ) -> None:
        """Perform action on internal state and perform our turn if possible."""
        from_pos, to_pos, turn = event.data
        action = self.state.action_from_points(from_pos, to_pos)
        self.state = self.state.perform_action(action)
        ##        print(f'{turn = }')
        if turn == self.playing_as:
            await self.base_perform_turn()

    async def handle_create_piece(self, event: Event[tuple[Pos, int]]) -> None:
        """Update internal pieces if we haven't had the initial setup event."""
        assert self.has_initial
        pos, type_ = event.data
        self.pieces[pos] = type_

    async def handle_playing_as(self, event: Event[int]) -> None:
        """Handle playing as event."""
        self.playing_as = event.data

        assert self.has_initial
        if self.state.turn == self.playing_as:
            await self.base_perform_turn()

    async def handle_initial_config(
        self,
        event: Event[tuple[Pos, int]],
    ) -> None:
        """Set up initial state and perform our turn if possible."""
        board_size, turn = event.data
        self.state = State(board_size, self.pieces, bool(turn))
        self.has_initial = True

    async def handle_game_over(self, event: Event[int]) -> None:
        """Raise network_stop event so we disconnect from server."""
        self.has_initial = False
        await self.raise_event(Event("network_stop", None))


class RemoteState(BaseRemoteState):
    """Remote State.

    Keeps track of game state and call perform_action when it's this clients
    turn.
    """

    __slots__ = ()

    @abstractmethod
    async def perform_turn(self) -> Action:
        """Perform turn, return action to perform."""

    async def handle_perform_turn(self) -> None:
        """Perform turn."""
        await self.perform_action(await self.perform_turn())


class MachineClient(ComponentManager):
    """Manager that runs until client_disconnected event fires."""

    __slots__ = ("running",)

    def __init__(self, remote_state_class: type[RemoteState]) -> None:
        """Initialize machine client."""
        super().__init__("machine_client")

        self.running = True

        self.add_component(remote_state_class())

    @asynccontextmanager
    async def client_with_block(self) -> AsyncGenerator[GameClient, None]:
        """Add client temporarily with `with` block, ensuring closure."""
        async with GameClient("game_client") as client:
            with self.temporary_component(client):
                yield client

    def bind_handlers(self) -> None:
        """Register client event handlers."""
        self.register_handlers(
            {
                "client_disconnected": self.handle_client_disconnected,
                "client_connection_closed": self.handle_client_disconnected,
            },
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
    connected: set[tuple[str, int]],
) -> None:
    """Run machine client and raise tick events."""
    async with trio.open_nursery() as main_nursery:
        event_manager = ExternalRaiseManager(
            "checkers",
            main_nursery,
            "client",
        )
        client = MachineClient(remote_state_class)
        with event_manager.temporary_component(client):
            async with client.client_with_block():
                await event_manager.raise_event(
                    Event("client_connect", (host, port)),
                )
                print(f"Connected to server {host}:{port}")
                try:
                    while client.running:  # noqa: ASYNC110
                        # Wait so backlog things happen
                        await trio.sleep(1)
                except KeyboardInterrupt:
                    print("Shutting down client from keyboard interrupt.")
                    await event_manager.raise_event(
                        Event("network_stop", None),
                    )
        print(f"Disconnected from server {host}:{port}")
        client.unbind_components()
    connected.remove((host, port))


def run_client_sync(
    host: str,
    port: int,
    remote_state_class: type[RemoteState],
) -> None:
    """Run client and connect to server at host:port."""
    trio.run(run_client, host, port, remote_state_class, set())


async def run_clients_in_local_servers(
    remote_state_class: type[RemoteState],
) -> None:
    """Run clients in local servers."""
    connected: set[tuple[str, int]] = set()
    print("Watching for advertisements...\n(CTRL + C to quit)")
    try:
        async with trio.open_nursery(strict_exception_groups=True) as nursery:
            while True:
                advertisements = set(await read_advertisements())
                servers = {server for _motd, server in advertisements}
                servers -= connected
                for server in servers:
                    connected.add(server)
                    nursery.start_soon(
                        run_client,
                        *server,
                        remote_state_class,
                        connected,
                    )
                await trio.sleep(1)
    except BaseExceptionGroup as exc:
        for ex in exc.exceptions:
            if isinstance(ex, KeyboardInterrupt):
                print("Shutting down from keyboard interrupt.")
                break
        else:
            raise


def run_clients_in_local_servers_sync(
    remote_state_class: type[RemoteState],
) -> None:
    """Run clients in local servers."""
    trio.run(run_clients_in_local_servers, remote_state_class)
