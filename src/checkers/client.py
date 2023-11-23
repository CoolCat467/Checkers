"""Game Client."""

from __future__ import annotations

__title__ = "Game Client"
__author__ = "CoolCat467"

import struct
import traceback

import trio

from checkers.base_io import StructFormat
from checkers.buffer import Buffer
from checkers.component import Event
from checkers.network import NetworkEventComponent, TimeoutException
from checkers.network_shared import (
    ADVERTISEMENT_IP,
    ADVERTISEMENT_PORT,
    Pos,
    TickEventData,
    read_position,
    write_position,
)


async def read_advertisements(
    timeout: int = 3,
) -> list[tuple[str, tuple[str, int]]]:
    """Read server advertisements from network. Return tuples of (motd, (host, port))."""
    # Look up multicast group address in name server and find out IP version
    addrinfo = (await trio.socket.getaddrinfo(ADVERTISEMENT_IP, None))[0]

    with trio.socket.socket(
        family=trio.socket.AF_INET,  # IPv4
        type=trio.socket.SOCK_DGRAM,  # UDP
        proto=trio.socket.IPPROTO_UDP,
    ) as udp_socket:
        # SO_REUSEADDR: allows binding to port potentially already in use
        # Allow multiple copies of this program on one machine
        # (not strictly needed)
        udp_socket.setsockopt(
            trio.socket.SOL_SOCKET,
            trio.socket.SO_REUSEADDR,
            1,
        )

        await udp_socket.bind(("", ADVERTISEMENT_PORT))

        ##        # Tell the kernel that we are a multicast socket
        ##        udp_socket.setsockopt(trio.socket.IPPROTO_IP, trio.socket.IP_MULTICAST_TTL, 255)

        # socket.IPPROTO_IP works on Linux and Windows
        ##        # IP_MULTICAST_IF: force sending network traffic over specific network adapter
        # IP_ADD_MEMBERSHIP: join multicast group
        ##        udp_socket.setsockopt(
        ##            trio.socket.IPPROTO_IP, trio.socket.IP_MULTICAST_IF,
        ##            trio.socket.inet_aton(network_adapter)
        ##        )
        ##    udp_socket.setsockopt(
        ##        trio.socket.IPPROTO_IP,
        ##        trio.socket.IP_ADD_MEMBERSHIP,
        ##        struct.pack(
        ##            "4s4s",
        ##            trio.socket.inet_aton(group),
        ##            trio.socket.inet_aton(network_adapter),
        ##        ),
        ##    )
        group_bin = trio.socket.inet_pton(addrinfo[0], addrinfo[4][0])
        # Join group
        if addrinfo[0] == trio.socket.AF_INET:  # IPv4
            mreq = group_bin + struct.pack("=I", trio.socket.INADDR_ANY)
            udp_socket.setsockopt(
                trio.socket.IPPROTO_IP,
                trio.socket.IP_ADD_MEMBERSHIP,
                mreq,
            )
        else:
            mreq = group_bin + struct.pack("@I", 0)
            udp_socket.setsockopt(
                trio.socket.IPPROTO_IPV6,
                trio.socket.IPV6_JOIN_GROUP,
                mreq,
            )

        buffer = b""
        address = ""
        with trio.move_on_after(timeout):
            buffer, address = await udp_socket.recvfrom(512)
            host, port = address
        ##            print(f"{buffer = }")
        ##            print(f"{address = }")

        response: list[tuple[str, tuple[str, int]]] = []

        start = 0
        for _ in range(1024):
            ad_start = buffer.find(b"[AD]", start)
            if ad_start == -1:
                break
            ad_end = buffer.find(b"[/AD]", ad_start)
            if ad_end == -1:
                break
            start_block = buffer.find(b"[CHECKERS]", ad_end)
            if start_block == -1:
                break
            start_end = buffer.find(b"[/CHECKERS]", start_block)
            if start_end == -1:
                break

            start = start_end

            motd = buffer[start_block + 10 : start_end].decode("utf-8")
            raw_port = buffer[ad_start + 4 : ad_end].decode("utf-8")
            try:
                port = int(raw_port)
            except ValueError:
                continue
            response.append((motd, (host, port)))
        return response


class GameClient(NetworkEventComponent):
    """Game Client Network Event Component.

    This class handles connecting to the game server, transmitting events
    to the server, and reading and raising incoming events from the server.
    """

    __slots__ = ()  # "tick_lock",

    def __init__(self, name: str) -> None:
        super().__init__(name)

        # Five seconds until timeout is generous, but it gives server end wiggle
        # room.
        self.timeout = 5

        self.register_network_write_events(
            {
                "select_piece->server": 0,
                "select_tile->server": 1,
            },
        )
        self.register_read_network_events(
            {
                0: "no_actions->client",
                1: "server->create_piece",
                2: "server->select_piece",
                3: "server->create_tile",
                4: "server->delete_tile",
                5: "server->delete_piece_animation",
                6: "server->update_piece_animation",
                7: "server->move_piece_animation",
                8: "server->animation_state",
                9: "server->game_over",
                10: "server->action_complete",
                11: "server->initial_config",
                12: "server->playing_as",
            },
        )

    ##        self.tick_lock = trio.Lock()

    def bind_handlers(self) -> None:
        super().bind_handlers()
        self.register_handlers(
            {
                # "no_actions->client": self.print_no_actions,
                "gameboard_piece_clicked": self.write_piece_click,
                "gameboard_tile_clicked": self.write_tile_click,
                "server->create_piece": self.read_create_piece,
                "server->select_piece": self.read_select_piece,
                "server->create_tile": self.read_create_tile,
                "server->delete_tile": self.read_delete_tile,
                "server->delete_piece_animation": self.read_delete_piece_animation,
                "server->update_piece_animation": self.read_update_piece_animation,
                "server->move_piece_animation": self.read_move_piece_animation,
                "server->animation_state": self.read_animation_state,
                "server->game_over": self.read_game_over,
                "server->action_complete": self.read_action_complete,
                "server->initial_config": self.read_initial_config,
                "server->playing_as": self.read_playing_as,
                "network_stop": self.handle_network_stop,
                "client_connect": self.handle_client_connect,
                f"client[{self.name}]_read_event": self.handle_read_event,
            },
        )

    async def print_no_actions(self, event: Event[bytearray]) -> None:
        """Print received `no_actions` event from server.

        This event is used as a sort of keepalive heartbeat, because
        it stops the connection from timing out.
        """
        print(f"print_no_actions {event = }")

    async def raise_disconnect(self, message: str) -> None:
        """Raise client_disconnected event with given message."""
        print(f"{self.__class__.__name__}: {message}")
        if not self.manager_exists:
            print(
                f"{self.__class__.__name__}: Manager does not exist, not raising disconnect event.",
            )
            return
        await self.raise_event(Event("client_disconnected", message))
        await self.close()
        assert self.not_connected

    async def handle_read_event(
        self,
        tick_event: Event[TickEventData],
    ) -> None:
        """Raise events from server."""
        ##        async with self.tick_lock:
        ##print(f"{self.__class__.__name__}[{self.name}]: handle_read_event")
        if not self.manager_exists:
            return
        if self.not_connected:
            await self.raise_disconnect("Not connected to server.")
            return
        try:
            print("handle_read_event start")
            event = await self.read_event()
        except trio.ClosedResourceError:
            assert self.not_connected
            print("handle_read_event trio.ClosedResourceError")
            return
        except TimeoutException as exc:
            traceback.print_exception(exc)
            await self.raise_disconnect("Failed to read event from server.")
            return
        else:
            await self.raise_event(event)
        await self.raise_event(Event(f"client[{self.name}]_read_event", None))

    async def handle_client_connect(
        self,
        event: Event[tuple[str, int]],
    ) -> None:
        """Have client connect to address specified in event."""
        if not self.not_connected:
            return
        try:
            await self.connect(*event.data)
        except OSError as ex:
            traceback.print_exception(ex)
        else:
            await self.raise_event(
                Event(f"client[{self.name}]_read_event", None),
            )
            return
        await self.raise_disconnect("Error connecting to server.")

    async def read_create_piece(self, event: Event[bytearray]) -> None:
        """Read create_piece event from server."""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        piece_type = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("gameboard_create_piece", (piece_pos, piece_type)),
        )

    async def read_select_piece(self, event: Event[bytearray]) -> None:
        """Read create_piece event from server."""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        outline_value = buffer.read_value(StructFormat.BOOL)

        await self.raise_event(
            Event("gameboard_select_piece", (piece_pos, outline_value)),
        )

    async def read_create_tile(self, event: Event[bytearray]) -> None:
        """Read create_tile event from server."""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(Event("gameboard_create_tile", tile_pos))

    async def read_delete_tile(self, event: Event[bytearray]) -> None:
        """Read delete_tile event from server."""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(Event("gameboard_delete_tile", tile_pos))

    async def write_piece_click(self, event: Event[tuple[Pos, int]]) -> None:
        """Write piece click event to server."""
        if self.not_connected:
            return
        piece_position, piece_type = event.data

        buffer = Buffer()
        write_position(buffer, piece_position)
        buffer.write_value(StructFormat.UINT, piece_type)

        await self.write_event(Event("select_piece->server", buffer))

    async def write_tile_click(self, event: Event[Pos]) -> None:
        """Write tile click event to server."""
        if self.not_connected:
            return
        tile_position = event.data

        buffer = Buffer()
        write_position(buffer, tile_position)

        await self.write_event(Event("select_tile->server", buffer))

    async def read_delete_piece_animation(
        self,
        event: Event[bytearray],
    ) -> None:
        """Read delete_piece_animation event from server."""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(
            Event("gameboard_delete_piece_animation", tile_pos),
        )

    async def read_update_piece_animation(
        self,
        event: Event[bytearray],
    ) -> None:
        """Read update_piece_animation event from server."""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        piece_type = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("gameboard_update_piece_animation", (piece_pos, piece_type)),
        )

    async def read_move_piece_animation(self, event: Event[bytearray]) -> None:
        """Read move_piece_animation event from server."""
        buffer = Buffer(event.data)

        piece_current_pos = read_position(buffer)
        piece_new_pos = read_position(buffer)

        await self.raise_event(
            Event(
                "gameboard_move_piece_animation",
                (piece_current_pos, piece_new_pos),
            ),
        )

    async def read_animation_state(self, event: Event[bytearray]) -> None:
        """Read animation_state event from server."""
        buffer = Buffer(event.data)

        animation_state = buffer.read_value(StructFormat.BOOL)

        await self.raise_event(
            Event("gameboard_animation_state", animation_state),
        )

    async def read_game_over(self, event: Event[bytearray]) -> None:
        """Read update_piece event from server."""
        buffer = Buffer(event.data)

        winner = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(Event("game_winner", winner))

    async def read_action_complete(self, event: Event[bytearray]) -> None:
        """Read action_complete event from server.

        Sent when last action from client is done, great for AIs.
        As of writing, not used for main client.
        """
        buffer = Buffer(event.data)

        from_pos = read_position(buffer)
        to_pos = read_position(buffer)
        current_turn = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("game_action_complete", (from_pos, to_pos, current_turn)),
        )

    async def read_initial_config(self, event: Event[bytearray]) -> None:
        """Read initial_config event from server."""
        buffer = Buffer(event.data)

        board_size = read_position(buffer)
        current_turn = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("game_initial_config", (board_size, current_turn)),
        )

    async def read_playing_as(self, event: Event[bytearray]) -> None:
        """Read playing_as event from server."""
        print(f"read_playing_as {event = }")
        buffer = Buffer(event.data)

        playing_as = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("game_playing_as", playing_as),
        )

    async def handle_network_stop(self, event: Event[None]) -> None:
        """Send EOF if connected and close socket."""
        if self.not_connected:
            return
        else:
            await self.send_eof()
        await self.close()
        assert self.not_connected

    def __del__(self) -> None:
        print(f"del {self.__class__.__name__}")
