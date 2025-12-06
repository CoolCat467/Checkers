#!/usr/bin/env python3
# Checkers Game Server

"""Checkers Game Server."""

# Programmed by CoolCat467

from __future__ import annotations

# Copyright (C) 2023-2024  CoolCat467
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

__title__ = "Server"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "0.0.0"

import traceback
from collections import deque
from functools import partial
from typing import TYPE_CHECKING, NoReturn, cast

import trio
from libcomponent import network
from libcomponent.base_io import StructFormat
from libcomponent.buffer import Buffer
from libcomponent.component import (
    ComponentManager,
    Event,
    ExternalRaiseManager,
)
from libcomponent.network_utils import (
    ServerClientNetworkEventComponent,
    find_ip,
)

from checkers.network_shared import (
    ADVERTISEMENT_IP,
    ADVERTISEMENT_PORT,
    DEFAULT_PORT,
    ClientBoundEvents,
    Pos,
    ServerBoundEvents,
    read_position,
    write_position,
)
from checkers.state import Action, State, generate_pieces

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable


class ServerClient(ServerClientNetworkEventComponent):
    """Server Client Network Event Component.

    When clients connect to server, this class handles the incoming
    connections to the server in the way of reading and raising events
    that are transferred over the network.
    """

    __slots__ = ("client_id", "rsa_key", "verify_token")

    def __init__(self, client_id: int) -> None:
        """Initialize Server Client."""
        self.client_id = client_id
        super().__init__(f"client_{client_id}")

        self.timeout = 3

        cbe = ClientBoundEvents
        self.register_network_write_events(
            {
                "server[write]->callback_ping": cbe.callback_ping,
                "server[write]->create_piece": cbe.create_piece,
                "server[write]->select_piece": cbe.select_piece,
                "server[write]->create_tile": cbe.create_tile,
                "server[write]->delete_tile": cbe.delete_tile,
                "server[write]->delete_piece_animation": cbe.delete_piece_animation,
                "server[write]->update_piece_animation": cbe.update_piece_animation,
                "server[write]->move_piece_animation": cbe.move_piece_animation,
                "server[write]->animation_state": cbe.animation_state,
                "server[write]->game_over": cbe.game_over,
                "server[write]->action_complete": cbe.action_complete,
                "server[write]->initial_config": cbe.initial_config,
                "server[write]->playing_as": cbe.playing_as,
                "server[write]->encryption_request": cbe.encryption_request,
            },
        )
        sbe = ServerBoundEvents
        self.register_read_network_events(
            {
                sbe.select_piece: f"client[{self.client_id}]->select_piece",
                sbe.select_tile: f"client[{self.client_id}]->select_tile",
                sbe.encryption_response: f"client[{self.client_id}]->encryption_response",
            },
        )

    def bind_handlers(self) -> None:
        """Bind event handlers."""
        super().bind_handlers()
        self.register_handlers(
            {
                f"client[{self.client_id}]->select_piece": self.read_raw_select_piece,
                f"client[{self.client_id}]->select_tile": self.read_raw_select_tile,
                f"client[{self.client_id}]->encryption_response": self.handle_encryption_response,
                "create_piece->network": self.handle_create_piece,
                "select_piece->network": self.handle_piece_select,
                "create_tile->network": self.handle_create_tile,
                "delete_tile->network": self.handle_delete_tile,
                "delete_piece_animation->network": self.handle_delete_piece_animation,
                "update_piece_animation->network": self.handle_update_piece_animation,
                "move_piece_animation->network": self.handle_move_piece_animation,
                "animation_state->network": self.handle_animation_state,
                "game_over->network": self.handle_game_over,
                "action_complete->network": self.handle_action_complete,
                "initial_config->network": self.handle_initial_config,
                f"playing_as->network[{self.client_id}]": self.handle_playing_as,
                f"callback_ping->network[{self.client_id}]": self.handle_callback_ping,
            },
        )

    async def read_raw_select_piece(self, event: Event[bytearray]) -> None:
        """Read raw select piece event and reraise as network->select_piece."""
        buffer = Buffer(event.data)

        pos_x, pos_y = read_position(buffer)

        await self.raise_event(
            Event("network->select_piece", (self.client_id, (pos_x, pos_y))),
        )

    async def read_raw_select_tile(self, event: Event[bytearray]) -> None:
        """Read raw select tile event and reraise as network->select_tile."""
        buffer = Buffer(event.data)

        pos_x, pos_y = read_position(buffer)

        await self.raise_event(
            Event("network->select_tile", (self.client_id, (pos_x, pos_y))),
        )

    async def handle_create_piece(self, event: Event[tuple[Pos, int]]) -> None:
        """Read create piece event and reraise as server[write]->create_piece."""
        piece_pos, piece_type = event.data

        buffer = Buffer()

        write_position(buffer, piece_pos)
        buffer.write_value(StructFormat.UBYTE, piece_type)

        await self.write_event(Event("server[write]->create_piece", buffer))

    async def handle_piece_select(
        self,
        event: Event[tuple[Pos, bool]],
    ) -> None:
        """Read piece select event and reraise as server[write]->select_piece."""
        piece_pos, outline_value = event.data

        buffer = Buffer()

        write_position(buffer, piece_pos)
        buffer.write_value(StructFormat.BOOL, outline_value)

        await self.write_event(Event("server[write]->select_piece", buffer))

    async def handle_create_tile(self, event: Event[Pos]) -> None:
        """Read create tile event and reraise as server[write]->create_tile."""
        tile_pos = event.data

        buffer = Buffer()

        write_position(buffer, tile_pos)

        await self.write_event(Event("server[write]->create_tile", buffer))

    async def handle_delete_tile(self, event: Event[Pos]) -> None:
        """Read delete tile event and reraise as server[write]->delete_tile."""
        tile_pos = event.data

        buffer = Buffer()

        write_position(buffer, tile_pos)

        await self.write_event(Event("server[write]->delete_tile", buffer))

    async def handle_delete_piece_animation(self, event: Event[Pos]) -> None:
        """Read delete piece animation event and reraise as server[write]->delete_piece_animation."""
        piece_pos = event.data

        buffer = Buffer()

        write_position(buffer, piece_pos)

        await self.write_event(
            Event("server[write]->delete_piece_animation", buffer),
        )

    async def handle_update_piece_animation(
        self,
        event: Event[tuple[Pos, int]],
    ) -> None:
        """Read update piece animation event and reraise as server[write]->update_piece_animation."""
        piece_pos, piece_type = event.data

        buffer = Buffer()

        write_position(buffer, piece_pos)
        buffer.write_value(StructFormat.UBYTE, piece_type)

        await self.write_event(
            Event("server[write]->update_piece_animation", buffer),
        )

    async def handle_move_piece_animation(
        self,
        event: Event[tuple[Pos, Pos]],
    ) -> None:
        """Read move piece animation event and reraise as server[write]->move_piece_animation."""
        piece_current_pos, piece_new_pos = event.data

        buffer = Buffer()

        write_position(buffer, piece_current_pos)
        write_position(buffer, piece_new_pos)

        await self.write_event(
            Event("server[write]->move_piece_animation", buffer),
        )

    async def handle_animation_state(self, event: Event[bool]) -> None:
        """Read animation state change event and reraise as server[write]->animation_state."""
        state = event.data

        buffer = Buffer()

        buffer.write_value(StructFormat.BOOL, state)

        await self.write_event(Event("server[write]->animation_state", buffer))

    async def handle_game_over(self, event: Event[int]) -> None:
        """Read game over event and reraise as server[write]->game_over."""
        winner = event.data

        buffer = Buffer()

        buffer.write_value(StructFormat.UBYTE, winner)

        await self.write_event(Event("server[write]->game_over", buffer))

    async def handle_action_complete(
        self,
        event: Event[tuple[Pos, Pos, int]],
    ) -> None:
        """Read action complete event and reraise as server[write]->action_complete."""
        from_pos, to_pos, player_turn = event.data

        buffer = Buffer()

        write_position(buffer, from_pos)
        write_position(buffer, to_pos)
        buffer.write_value(StructFormat.UBYTE, player_turn)

        await self.write_event(Event("server[write]->action_complete", buffer))

    async def handle_initial_config(
        self,
        event: Event[tuple[Pos, int]],
    ) -> None:
        """Read initial config event and reraise as server[write]->initial_config."""
        board_size, player_turn = event.data

        buffer = Buffer()

        write_position(buffer, board_size)
        buffer.write_value(StructFormat.UBYTE, player_turn)

        await self.write_event(Event("server[write]->initial_config", buffer))

    async def handle_playing_as(
        self,
        event: Event[int],
    ) -> None:
        """Read playing as event and reraise as server[write]->playing_as."""
        playing_as = event.data

        buffer = Buffer()
        buffer.write_value(StructFormat.UBYTE, playing_as)
        await self.write_event(Event("server[write]->playing_as", buffer))

    async def handle_callback_ping(
        self,
        _: Event[None],
    ) -> None:
        """Reraise as server[write]->callback_ping."""
        await self.write_callback_ping()

    async def start_encryption_request(self) -> None:
        """Start encryption request and raise as `server[write]->encryption_request`."""
        await super().start_encryption_request()

        event = await self.read_event()
        if event.name != f"client[{self.client_id}]->encryption_response":
            raise RuntimeError(
                f"Expected encryption response, got but {event.name!r}",
            )
        await self.handle_encryption_response(event)


class CheckersState(State):
    """Subclass of State that keeps track of actions in `action_queue`."""

    __slots__ = ("action_queue",)

    def __init__(
        self,
        size: Pos,
        pieces: dict[Pos, int],
        turn: bool = True,
    ) -> None:
        """Initialize Checkers State."""
        super().__init__(size, pieces, turn)
        self.action_queue: deque[tuple[str, Iterable[Pos | int]]] = deque()

    def piece_kinged(self, piece_pos: Pos, new_type: int) -> None:
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

    def get_action_queue(self) -> deque[tuple[str, Iterable[Pos | int]]]:
        """Return action queue."""
        return self.action_queue


class GameServer(network.Server):
    """Checkers server.

    Handles accepting incoming connections from clients and handles
    main game logic via State subclass above.
    """

    __slots__ = (
        "actions_queue",
        "advertisement_scope",
        "client_count",
        "client_players",
        "internal_singleplayer_mode",
        "player_selections",
        "players_can_interact",
        "running",
        "state",
    )

    board_size = (8, 8)
    max_clients = 4

    def __init__(self, internal_singleplayer_mode: bool = False) -> None:
        """Initialize server."""
        super().__init__("GameServer")

        self.client_count: int
        self.state: CheckersState = CheckersState(self.board_size, {})

        self.client_players: dict[int, int] = {}
        self.player_selections: dict[int, Pos] = {}
        self.players_can_interact: bool = False

        self.internal_singleplayer_mode = internal_singleplayer_mode
        self.advertisement_scope: trio.CancelScope | None = None
        self.running = False

    def bind_handlers(self) -> None:
        """Register start_server and stop_server."""
        self.register_handlers(
            {
                "server_start": self.start_server,
                "network_stop": self.stop_server,
                "server_send_game_start": self.handle_server_start_new_game,
                "network->select_piece": self.handle_network_select_piece,
                "network->select_tile": self.handle_network_select_tile,
            },
        )

    async def stop_server(self, event: Event[None] | None = None) -> None:
        """Stop serving and disconnect all NetworkEventComponents."""
        self.stop_serving()
        self.stop_advertising()

        close_methods: deque[Callable[[], Awaitable[object]]] = deque()
        for component in self.get_all_components():
            if isinstance(component, network.NetworkEventComponent):
                close_methods.append(component.close)
            print(f"stop_server {component.name = }")
            self.remove_component(component.name)
        async with trio.open_nursery() as nursery:
            while close_methods:
                nursery.start_soon(close_methods.popleft())
        self.running = False

    async def post_advertisement(
        self,
        udp_socket: trio.socket.SocketType,
        send_to_ip: str,
        hosting_port: int,
    ) -> None:
        """Post server advertisement packet."""
        motd = "Checkers Game"
        advertisement = (
            f"[AD]{hosting_port}[/AD][CHECKERS]{motd}[/CHECKERS]"
        ).encode()
        # print("post_advertisement")
        await udp_socket.sendto(
            advertisement,
            (send_to_ip, ADVERTISEMENT_PORT),
        )

    def stop_advertising(self) -> None:
        """Cancel self.advertisement_scope."""
        if self.advertisement_scope is None:
            return
        self.advertisement_scope.cancel()

    async def post_advertisements(self, hosting_port: int) -> None:
        """Post lan UDP packets so server can be found."""
        self.stop_advertising()
        self.advertisement_scope = trio.CancelScope()

        # Look up multicast group address in name server and find out IP version
        addrinfo = (await trio.socket.getaddrinfo(ADVERTISEMENT_IP, None))[0]
        send_to_ip = str(addrinfo[4][0])

        with trio.socket.socket(
            family=trio.socket.AF_INET,  # IPv4
            type=trio.socket.SOCK_DGRAM,  # UDP
            proto=trio.socket.IPPROTO_UDP,  # UDP
        ) as udp_socket:
            # Set Time-to-live (optional)
            # ttl_bin = struct.pack('@i', MYTTL)
            # if addrinfo[0] == trio.socket.AF_INET: # IPv4
            # udp_socket.setsockopt(
            # trio.socket.IPPROTO_IP, trio.socket.IP_MULTICAST_TTL, ttl_bin)
            # else:
            # udp_socket.setsockopt(
            # trio.socket.IPPROTO_IPV6, trio.socket.IPV6_MULTICAST_HOPS, ttl_bin)
            with self.advertisement_scope:
                print("Starting advertisement posting.")
                while True:  # not self.can_start():
                    try:
                        await self.post_advertisement(
                            udp_socket,
                            send_to_ip,
                            hosting_port,
                        )
                    except OSError as exc:
                        traceback.print_exception(exc)
                        print(
                            f"{self.__class__.__name__}: Failed to post server advertisement",
                        )
                        break
                    await trio.sleep(1.5)
            print("Stopped advertisement posting.")

    @staticmethod
    def setup_teams_internal(client_ids: list[int]) -> dict[int, int]:
        """Return teams for internal server mode given sorted client ids."""
        players: dict[int, int] = {}
        for idx, client_id in enumerate(client_ids):
            if idx == 0:
                players[client_id] = 2
            else:
                players[client_id] = 0xFF  # Spectator
        return players

    @staticmethod
    def setup_teams(client_ids: list[int]) -> dict[int, int]:
        """Return teams given sorted client ids."""
        players: dict[int, int] = {}
        for idx, client_id in enumerate(client_ids):
            if idx < 2:
                players[client_id] = idx % 2
            else:
                players[client_id] = 0xFF  # Spectator
        return players

    def new_game_init(self) -> None:
        """Start new game."""
        self.client_players.clear()
        self.player_selections.clear()

        pieces = generate_pieces(*self.board_size)
        self.state = CheckersState(self.board_size, pieces)

        # Why keep track of another object just to know client ID numbers
        # if we already have that with the components? No need!
        client_ids: set[int] = set()
        for component in self.get_all_components():
            if isinstance(component, ServerClient):
                client_ids.add(component.client_id)

        sorted_client_ids = sorted(client_ids)
        if self.internal_singleplayer_mode:
            self.client_players = self.setup_teams_internal(sorted_client_ids)
        else:
            self.client_players = self.setup_teams(sorted_client_ids)

        self.players_can_interact = True

    # "Implicit return in function which does not return"
    async def start_server(  # type: ignore[misc]
        self,
        event: Event[tuple[str | None, int]],
    ) -> NoReturn:
        """Serve clients."""
        print(f"{self.__class__.__name__}: Closing old server clients")
        await self.stop_server()
        print(f"{self.__class__.__name__}: Starting Server")
        self.client_count = 0

        host, port = event.data

        self.running = True
        async with trio.open_nursery() as nursery:
            # Do not post advertisements when using internal singleplayer mode
            if not self.internal_singleplayer_mode:
                nursery.start_soon(self.post_advertisements, port)
            # Serve runs forever until canceled
            nursery.start_soon(partial(self.serve, port, host, backlog=0))

    async def transmit_playing_as(self) -> None:
        """Transmit playing as."""
        async with trio.open_nursery() as nursery:
            for client_id, team in self.client_players.items():
                nursery.start_soon(
                    self.raise_event,
                    Event(f"playing_as->network[{client_id}]", team),
                )

    async def handle_server_start_new_game(self, event: Event[None]) -> None:
        """Handle game start."""
        # Delete all pieces from last state (shouldn't be needed but still.)
        async with trio.open_nursery() as nursery:
            for piece_pos, _piece_type in self.state.get_pieces():
                nursery.start_soon(
                    self.raise_event,
                    Event("delete_piece->network", piece_pos),
                )

        # Choose which team plays first
        # Using non-cryptographically secure random because it doesn't matter
        self.new_game_init()

        # Raise initial config event with board size and initial turn.
        await self.raise_event(
            Event(
                "initial_config->network",
                (self.board_size, self.state.turn),
            ),
        )

        # Send create_piece events for all pieces
        async with trio.open_nursery() as nursery:
            for piece_pos, piece_type in self.state.get_pieces():
                nursery.start_soon(
                    self.raise_event,
                    Event("create_piece->network", (piece_pos, piece_type)),
                )

        await self.transmit_playing_as()

    async def client_network_loop(self, client: ServerClient) -> None:
        """Network loop for given ServerClient.

        Could raise the following exceptions:
          trio.BrokenResourceError: if something has gone wrong, and the stream
            is broken.
          trio.ClosedResourceError: if stream was previously closed

        Probably couldn't raise because of write lock but still:
          trio.BusyResourceError: More than one task is trying to write
            to socket at once.
        """
        while not self.can_start() and not client.not_connected:
            try:
                await client.write_callback_ping()
            except (
                trio.BrokenResourceError,
                trio.ClosedResourceError,
                network.NetworkStreamNotConnectedError,
            ):
                print(f"{client.name} Disconnected in lobby.")
                return
        while not client.not_connected:
            event: Event[bytearray] | None = None
            try:
                with trio.fail_after(6):
                    await client.write_callback_ping()
                with trio.move_on_after(2):
                    event = await client.read_event()
            except trio.TooSlowError:
                print(f"{client.name} Writing callback ping took too long")
                break
            except network.NetworkTimeoutError:
                print(f"{client.name} Timeout")
                break
            except network.NetworkEOFError:
                print(f"{client.name} EOF")
                break
            except (
                trio.BrokenResourceError,
                trio.ClosedResourceError,
                RuntimeError,
            ):
                break
            except Exception as exc:
                traceback.print_exception(exc)
                break
            if event is not None:
                # print(f"{client.name} client_network_loop tick")
                # print(f"{client.name} {event = }")
                await client.raise_event(event)

    def can_start(self) -> bool:
        """Return if game can start."""
        if self.internal_singleplayer_mode:
            return self.client_count >= 1
        return self.client_count >= 2

    def game_active(self) -> bool:
        """Return if game is active."""
        return self.state.check_for_win() is None

    async def send_spectator_join_packets(
        self,
        client: ServerClient,
    ) -> None:
        """Send spectator start data."""
        print("send_spectator_join_packets")

        private_events_pocket = ComponentManager(
            f"private_events_pocket for {client.client_id}",
        )
        with self.temporary_component(private_events_pocket):
            with private_events_pocket.temporary_component(client):
                # Raise initial config event with board size and initial turn.
                await client.raise_event(
                    Event(
                        "initial_config->network",
                        (self.state.size, self.state.turn),
                    ),
                )

                # Send create_piece events for all pieces
                async with trio.open_nursery() as nursery:
                    for piece_pos, piece_type in self.state.get_pieces():
                        nursery.start_soon(
                            client.raise_event,
                            Event(
                                "create_piece->network",
                                (piece_pos, piece_type),
                            ),
                        )

                # Send who player is playing as
                await client.raise_event(
                    Event(f"playing_as->network[{client.client_id}]", 255),
                )

    async def handler(self, stream: trio.SocketStream) -> None:
        """Accept clients. Called by network.Server.serve."""
        if self.client_count == 0 and self.game_active():
            # Old game was running but everyone left, restart
            self.state.pieces.clear()
            # self.state = CheckersState(self.board_size, {})
        new_client_id = self.client_count
        print(
            f"{self.__class__.__name__}: client connected [client_id {new_client_id}]",
        )
        self.client_count += 1

        can_start = self.can_start()
        game_active = self.game_active()
        # if can_start:
        # self.stop_serving()

        if self.client_count > self.max_clients:
            print(
                f"{self.__class__.__name__}: client disconnected, too many clients",
            )
            await stream.aclose()
            self.client_count -= 1
            return

        async with ServerClient.from_stream(
            new_client_id,
            stream=stream,
        ) as client:
            # Encrypt traffic
            await client.start_encryption_request()
            assert client.encryption_enabled

            if can_start and game_active:
                await self.send_spectator_join_packets(client)
            with self.temporary_component(client):
                if can_start and not game_active:
                    await self.raise_event(
                        Event("server_send_game_start", None),
                    )
                try:
                    await self.client_network_loop(client)
                finally:
                    print(
                        f"{self.__class__.__name__}: client disconnected [client_id {new_client_id}]",
                    )
                    self.client_count -= 1
        # ServerClient's `with` block handles closing stream.

    async def handle_network_select_piece(
        self,
        event: Event[tuple[int, Pos]],
    ) -> None:
        """Handle piece event from client."""
        client_id, tile_pos = event.data

        player = self.client_players.get(client_id, 0xFF)
        if player == 2:
            player = int(self.state.turn)

        if player != self.state.turn:
            print(
                f"{player = } cannot select piece {tile_pos = } because it is not that player's turn",
            )
            return

        if not self.players_can_interact:
            print(
                f"{player = } cannot select piece {tile_pos = } because players_can_interact is False",
            )
            return
        if not self.state.can_player_select_piece(player, tile_pos):
            print(f"{player = } cannot select piece {tile_pos = }")
            await self.player_select_piece(player, None)
            return
        if tile_pos == self.player_selections.get(player):
            # print(f"{player = } toggle select -> No select")
            await self.player_select_piece(player, None)
            return

        await self.player_select_piece(player, tile_pos)

    async def player_select_piece(
        self,
        player: int,
        piece_pos: Pos | None,
    ) -> None:
        """Update glowing tiles from new selected piece."""
        ignore: set[Pos] = set()

        if piece_pos is not None:
            # Calculate actions if required
            new_action_set = self.state.calculate_actions(piece_pos)
            ignore = new_action_set.ends

        ignored: set[Pos] = set()

        # Remove outlined tiles from previous selection if existed
        if prev_selection := self.player_selections.get(player):
            action_set = self.state.calculate_actions(prev_selection)
            ignored = action_set.ends & ignore
            remove = action_set.ends - ignore
            async with trio.open_nursery() as nursery:
                for tile_position in remove:
                    nursery.start_soon(
                        self.raise_event,
                        Event("delete_tile->network", tile_position),
                    )
                if piece_pos != prev_selection:
                    nursery.start_soon(
                        self.raise_event,
                        Event(
                            "select_piece->network",
                            (prev_selection, False),
                        ),
                    )

        if piece_pos is None:
            if prev_selection:
                del self.player_selections[player]
            return

        self.player_selections[player] = piece_pos

        # For each end point
        async with trio.open_nursery() as nursery:
            for tile_position in new_action_set.ends - ignored:
                nursery.start_soon(
                    self.raise_event,
                    Event("create_tile->network", tile_position),
                )
            # Sent select piece as well
            nursery.start_soon(
                self.raise_event,
                Event(
                    "select_piece->network",
                    (self.player_selections[player], True),
                ),
            )

    async def handle_move_animation(self, from_pos: Pos, to_pos: Pos) -> None:
        """Handle move animation."""
        await self.raise_event(
            Event("move_piece_animation->network", (from_pos, to_pos)),
        )

    async def handle_jump_animation(self, jumped_pos: Pos) -> None:
        """Handle jump animation."""
        await self.raise_event(
            Event("delete_piece_animation->network", jumped_pos),
        )

    async def handle_king_animation(
        self,
        kinged_pos: Pos,
        piece_type: int,
    ) -> None:
        """Handle jump animation."""
        await self.raise_event(
            Event("update_piece_animation->network", (kinged_pos, piece_type)),
        )

    async def handle_action_animations(
        self,
        actions: deque[tuple[str, Iterable[Pos | int]]],
    ) -> None:
        """Handle action animations."""
        while actions:
            name, params = actions.popleft()
            if name == "move":
                await self.handle_move_animation(
                    *cast("Iterable[Pos]", params),
                )
            elif name == "jump":
                await self.handle_jump_animation(
                    *cast("Iterable[Pos]", params),
                )
            elif name == "king":
                await self.handle_king_animation(
                    *cast("tuple[Pos, int]", params),
                )
            else:
                raise NotImplementedError(f"Animation for action {name}")

    async def handle_network_select_tile(
        self,
        event: Event[tuple[int, Pos]],
    ) -> None:
        """Handle select tile event from network."""
        client_id, tile_pos = event.data

        player = self.client_players.get(client_id, 0xFF)
        if player == 2:
            player = int(self.state.turn)

        if not self.players_can_interact:
            print(
                f"{player = } cannot select tile {tile_pos = } because players_can_interact is False",
            )
            return

        if player != self.state.turn:
            print(
                f"{player = } cannot select tile {tile_pos = } because it is not their turn.",
            )
            return

        piece_pos = self.player_selections.get(player)
        if piece_pos is None:
            print(
                f"{player = } cannot select tile {tile_pos = } because has no selection",
            )
            return

        if tile_pos not in self.state.calculate_actions(piece_pos).ends:
            print(
                f"{player = } cannot select tile {piece_pos!r} because not valid move",
            )
            return

        self.players_can_interact = False  # No one moves during animation
        # Send animation state start event
        await self.raise_event(Event("animation_state->network", True))

        # Remove tile sprites and glowing effect
        await self.player_select_piece(player, None)

        action = Action(piece_pos, tile_pos)
        # print(f"{action = }")

        # Get new state after performing valid action
        new_state = self.state.perform_action(action)
        # Get action queue from old state
        action_queue = self.state.get_action_queue()
        self.state = new_state

        # Send action animations
        await self.handle_action_animations(action_queue)

        # Send action complete event
        await self.raise_event(
            Event(
                "action_complete->network",
                (piece_pos, tile_pos, self.state.turn),
            ),
        )

        win_value = self.state.check_for_win()
        if win_value is not None:
            # If we have a winner, send game over event.
            await self.raise_event(Event("game_over->network", win_value))
            return

        # If not game over, allow interactions so next player can take turn
        self.players_can_interact = True
        await self.raise_event(Event("animation_state->network", False))

    def __del__(self) -> None:
        """Debug print."""
        print(f"del {self.__class__.__name__}")
        super().__del__()


async def run_server(
    server_class: type[GameServer],
    host: str,
    port: int,
) -> None:
    """Run machine client and raise tick events."""
    async with trio.open_nursery() as main_nursery:
        event_manager = ExternalRaiseManager(
            "checkers",
            main_nursery,
        )
        server = server_class()
        event_manager.add_component(server)

        await event_manager.raise_event(Event("server_start", (host, port)))
        while not server.running:
            print("Server starting...")
            await trio.sleep(1)

        print("\nServer running.")

        try:
            while server.running:  # noqa: ASYNC110  # sleep in while loop
                # Process background tasks in the main nursery
                await trio.sleep(0.01)
        except KeyboardInterrupt:
            print("\nClosing from keyboard interrupt.")
        await server.stop_server()
        server.unbind_components()


async def cli_run_async() -> None:
    """Run game server."""
    host = await find_ip()
    port = DEFAULT_PORT
    await run_server(GameServer, host, port)


def cli_run() -> None:
    """Run game server."""
    trio.run(cli_run_async)


if __name__ == "__main__":
    cli_run()
