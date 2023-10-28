import traceback
from typing import NamedTuple

import trio

from .base_io import StructFormat
from .buffer import Buffer
from .component import Event
from .network import NetworkEventComponent, TimeoutException
from .network_shared import Pos, read_position, write_position


class TickEventData(NamedTuple):
    """Tick Event Data"""

    time_passed: float
    fps: float


class GameClient(NetworkEventComponent):
    """Game Client Network Event Component.

    This class handles connecting to the game server, transmitting events
    to the server, and reading and raising incoming events from the server."""

    __slots__ = ("tick_lock",)

    def __init__(self, name: str) -> None:
        super().__init__(name)

        # Five seconds until timeout is generous, but it gives server end wiggle
        # room.
        self.timeout = 5

        self.register_network_write_events(
            {
                "select_piece->server": 0,
                "select_tile->server": 1,
            }
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
            }
        )

        self.tick_lock = trio.Lock()

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
                "network_stop": self.handle_network_stop,
                "client_connect": self.handle_client_connect,
                "tick": self.handle_tick,
            }
        )

    async def print_no_actions(self, event: Event[bytearray]) -> None:
        """Print received `no_actions` event from server.

        This event is used as a sort of keepalive heartbeat, because
        it stops the connection from timing out."""
        print(f"print_no_actions {event = }")

    async def handle_tick(self, tick_event: Event[TickEventData]) -> None:
        """Raise events from server"""
        async with self.tick_lock:
            ##            print("handle_tick")
            if not self.manager_exists or self.not_connected:
                return
            try:
                event = await self.read_event()
            except trio.ClosedResourceError:
                return
            except TimeoutException as exc:
                await self.close()
                traceback.print_exception(exc)
                message = "Failed to read event from server."
                print(f"{self.__class__.__name__}: {message}")
                if self.manager_exists:
                    await self.raise_event(
                        Event("client_disconnected", message)
                    )
            else:
                await self.raise_event(event)

    async def handle_client_connect(
        self, event: Event[tuple[str, int]]
    ) -> None:
        """Have client connect to address specified in event"""
        if not self.not_connected:
            return
        try:
            await self.connect(*event.data)
            return
        except OSError as ex:
            traceback.print_exception(ex)
        message = "Error connecting to server."
        print(f"{self.__class__.__name__}: {message}")
        await self.close()
        await self.raise_event(Event("client_disconnected", message))

    async def read_create_piece(self, event: Event[bytearray]) -> None:
        """Read create_piece event from server"""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        piece_type = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("gameboard_create_piece", (piece_pos, piece_type))
        )

    async def read_select_piece(self, event: Event[bytearray]) -> None:
        """Read create_piece event from server"""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        outline_value = buffer.read_value(StructFormat.BOOL)

        await self.raise_event(
            Event("gameboard_select_piece", (piece_pos, outline_value))
        )

    async def read_create_tile(self, event: Event[bytearray]) -> None:
        """Read create_tile event from server"""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(Event("gameboard_create_tile", tile_pos))

    async def read_delete_tile(self, event: Event[bytearray]) -> None:
        """Read delete_tile event from server"""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(Event("gameboard_delete_tile", tile_pos))

    async def write_piece_click(self, event: Event[tuple[Pos, int]]) -> None:
        """Write piece click event to server"""
        if self.not_connected:
            return
        piece_position, piece_type = event.data

        buffer = Buffer()
        write_position(buffer, piece_position)
        buffer.write_value(StructFormat.UINT, piece_type)

        await self.write_event(Event("select_piece->server", buffer))

    async def write_tile_click(self, event: Event[Pos]) -> None:
        """Write tile click event to server"""
        if self.not_connected:
            return
        tile_position = event.data

        buffer = Buffer()
        write_position(buffer, tile_position)

        await self.write_event(Event("select_tile->server", buffer))

    async def read_delete_piece_animation(
        self, event: Event[bytearray]
    ) -> None:
        """Read delete_piece_animation event from server"""
        buffer = Buffer(event.data)

        tile_pos = read_position(buffer)

        await self.raise_event(
            Event("gameboard_delete_piece_animation", tile_pos)
        )

    async def read_update_piece_animation(
        self, event: Event[bytearray]
    ) -> None:
        """Read update_piece_animation event from server"""
        buffer = Buffer(event.data)

        piece_pos = read_position(buffer)
        piece_type = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("gameboard_update_piece_animation", (piece_pos, piece_type))
        )

    async def read_move_piece_animation(self, event: Event[bytearray]) -> None:
        """Read move_piece_animation event from server"""
        buffer = Buffer(event.data)

        piece_current_pos = read_position(buffer)
        piece_new_pos = read_position(buffer)

        await self.raise_event(
            Event(
                "gameboard_move_piece_animation",
                (piece_current_pos, piece_new_pos),
            )
        )

    async def read_animation_state(self, event: Event[bytearray]) -> None:
        """Read animation_state event from server"""
        buffer = Buffer(event.data)

        animation_state = buffer.read_value(StructFormat.BOOL)

        await self.raise_event(
            Event("gameboard_animation_state", animation_state)
        )

    async def read_game_over(self, event: Event[bytearray]) -> None:
        """Read update_piece event from server"""
        buffer = Buffer(event.data)

        winner = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(Event("game_winner", winner))

    async def read_action_complete(self, event: Event[bytearray]) -> None:
        """Read action_complete event from server.

        Sent when last action from client is done, great for AIs.
        As of writing, not used for main client."""
        buffer = Buffer(event.data)

        from_pos = read_position(buffer)
        to_pos = read_position(buffer)
        current_turn = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("game_action_complete", (from_pos, to_pos, current_turn))
        )

    async def read_initial_config(self, event: Event[bytearray]) -> None:
        """Read initial_config event from server"""
        buffer = Buffer(event.data)

        board_size = read_position(buffer)
        current_turn = buffer.read_value(StructFormat.UBYTE)

        await self.raise_event(
            Event("game_initial_config", (board_size, current_turn))
        )

    async def handle_network_stop(self, event: Event[None]) -> None:
        """Send EOF if connected and close socket."""
        if self.not_connected:
            return
        else:
            await self.send_eof()
        await self.close()

    def __del__(self) -> None:
        print(f"del {self.__class__.__name__}")
