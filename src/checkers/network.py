"""Network - Module for sending events over the network."""

# Programmed by CoolCat467

# Copyright (C) 2023-2024  CoolCat467
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

__title__ = "Network"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "0.0.0"


import contextlib
from typing import (
    TYPE_CHECKING,
    Any,
    AnyStr,
    Generic,
    Literal,
    NoReturn,
    SupportsIndex,
    TypeAlias,
)

import trio

from checkers.base_io import (
    BaseAsyncReader,
    BaseAsyncWriter,
    StructFormat,
)
from checkers.component import (
    Component,
    ComponentManager,
    Event,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import TracebackType

    from typing_extensions import Self

    BytesConvertable: TypeAlias = SupportsIndex | Iterable[SupportsIndex]
else:
    BytesConvertable = Generic


class NetworkTimeoutError(Exception):
    """Network Timeout Error."""

    __slots__ = ()


class NetworkStreamNotConnectedError(RuntimeError):
    """Network Stream Not Connected Error."""

    __slots__ = ()


class NetworkComponent(Component, BaseAsyncReader, BaseAsyncWriter):
    """Network Component (client)."""

    __slots__ = ("_stream", "timeout")

    def __init__(self, name: str) -> None:
        """Initialize Network Component."""
        super().__init__(name)

        self.timeout: int | float = 3
        self._stream: trio.SocketStream | None = None

    @property
    def not_connected(self) -> bool:
        """Is stream None?."""
        return self._stream is None

    @property
    def stream(self) -> trio.SocketStream:
        """Trio SocketStream or raise NetworkStreamNotConnectedError."""
        if self._stream is None:
            raise NetworkStreamNotConnectedError("Stream not connected!")
        return self._stream

    @classmethod
    def from_stream(
        cls,
        *args: object,
        kwargs: dict[str, object] | None = None,
        stream: trio.SocketStream,
    ) -> Self:
        """Initialize from stream."""
        if kwargs is None:
            kwargs = {}
        self = cls(*args, **kwargs)  # type: ignore[arg-type]
        self._stream = stream
        return self

    async def connect(self, host: str, port: int) -> None:
        """Connect to host:port on TCP."""
        if not self.not_connected:
            raise RuntimeError("Already connected!")
        try:
            self._stream = await trio.open_tcp_stream(host, port)
        except OSError:  # pragma: nocover
            await self.close()
            raise

    async def read(self, length: int) -> bytearray:
        """Read `length` bytes from stream.

        Can raise following exceptions:
            NetworkStreamNotConnectedError
            NetworkTimeoutError - Timeout or no data
            OSError - Stopped responding
        """
        content = bytearray()
        while max_read_count := length - len(content):
            received = b""
            ##            try:
            with trio.move_on_after(self.timeout):
                received = await self.stream.receive_some(max_read_count)
            ##            except (trio.BrokenResourceError, trio.ClosedResourceError):
            ##                await self.close()
            ##                raise
            content.extend(received)
            if len(received) == 0:
                # No information at all
                if len(content) == 0:
                    raise NetworkTimeoutError(
                        "Server did not respond with any information. "
                        "This may be from a connection timeout.",
                    )
                # Only sent a few bytes, but we requested more
                raise OSError(
                    f"Server stopped responding (got {len(content)} bytes, "
                    f"but expected {length} bytes)."
                    f" Partial obtained packet: {content!r}",
                )
        return content

    async def write(self, data: bytes) -> None:
        """Write data to stream."""
        await self.stream.send_all(data)

    ##        try:
    ##            await self.stream.send_all(data)
    ##        except (trio.BrokenResourceError, trio.ClosedResourceError):
    ##            await self.close()
    ##            raise

    async def close(self) -> None:
        """Close the stream."""
        if self._stream is None:
            await trio.lowlevel.checkpoint()
            return
        await self._stream.aclose()
        self._stream = None

    async def send_eof(self) -> None:
        """Close the sending half of the stream."""
        with contextlib.suppress(trio.ClosedResourceError):
            await self.stream.send_eof()

    async def wait_write_might_not_block(self) -> None:
        """stream.wait_send_all_might_not_block."""
        return await self.stream.wait_send_all_might_not_block()

    async def __aenter__(self) -> Self:
        """Async context manager enter."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()


##    async def send_eof_and_close(self) -> None:
##        """Send EOF and close."""
##        await self.send_eof()
##        await self.close()


class NetworkEventComponent(NetworkComponent):
    """Network Event Component - Send events over the network."""

    __slots__ = (
        "_read_packet_id_to_event_name",
        "_write_event_name_to_packet_id",
        "read_lock",
        "write_lock",
    )

    packet_id_format: Literal[StructFormat.USHORT] = StructFormat.USHORT

    def __init__(self, name: str) -> None:
        """Initialize Network Event Component."""
        super().__init__(name)
        self._read_packet_id_to_event_name: dict[int, str] = {}
        self._write_event_name_to_packet_id: dict[str, int] = {}
        self.read_lock = trio.Lock()
        self.write_lock = trio.Lock()

    def bind_handlers(self) -> None:
        """Register serverbound event handlers."""
        self.register_handlers(
            {
                name: self.write_event
                for name in self._write_event_name_to_packet_id
            },
        )

    def register_network_write_event(
        self,
        event_name: str,
        packet_id: int,
    ) -> None:
        """Map event name to serverbound packet id."""
        if event_name in self._write_event_name_to_packet_id:
            raise ValueError(f"{event_name!r} event already registered!")
        if self._read_packet_id_to_event_name.get(packet_id) == event_name:
            raise ValueError(
                f"{event_name!r} events are also being received "
                f"from server with packet id {packet_id!r}, "
                "which will would lead to infinite looping over network",
            )
        self._write_event_name_to_packet_id[event_name] = packet_id
        if self.manager_exists:
            self.register_handler(event_name, self.write_event)

    def register_network_write_events(self, event_map: dict[str, int]) -> None:
        """Map event names to serverbound packet ids."""
        for event_name, packet_id in event_map.items():
            self.register_network_write_event(event_name, packet_id)

    async def write_event(self, event: Event[bytearray]) -> None:
        """Send event to network."""
        packet_id = self._write_event_name_to_packet_id.get(event.name)
        if packet_id is None:
            raise RuntimeError(f"Unhandled network event name {event.name!r}")
        async with self.write_lock:
            await self.write_value(self.packet_id_format, packet_id)
            await self.write_bytearray(event.data)

    async def read_event(self) -> Event[bytearray]:
        """Receive event from network."""
        async with self.read_lock:
            packet_id = await self.read_value(self.packet_id_format)
            event_data = await self.read_bytearray()
        event_name = self._read_packet_id_to_event_name.get(packet_id)
        if event_name is None:
            raise RuntimeError(f"Unhandled packet ID {packet_id!r}")
        return Event(event_name, event_data)

    def register_read_network_event(
        self,
        packet_id: int,
        event_name: str,
    ) -> None:
        """Map clientbound packet id to event name."""
        if packet_id in self._read_packet_id_to_event_name:
            raise ValueError(f"Packet ID {packet_id!r} already registered!")
        if self._write_event_name_to_packet_id.get(event_name) == packet_id:
            raise ValueError(
                f"Packet id {packet_id!r} packets are also being received"
                f"from server with as {event_name!r} events, "
                "which will would lead to infinite looping over network",
            )
        self._read_packet_id_to_event_name[packet_id] = event_name

    def register_read_network_events(self, packet_map: dict[int, str]) -> None:
        """Map clientbound packet ids to event names."""
        for packet_id, event_name in packet_map.items():
            self.register_read_network_event(packet_id, event_name)


class Server(ComponentManager):
    """Asynchronous TCP Server."""

    __slots__ = ("cancel_scope",)

    def __init__(self, name: str, own_name: str | None = None) -> None:
        """Initialize Server."""
        super().__init__(name, own_name)
        self.cancel_scope: trio.CancelScope | None = None

    def stop_serving(self) -> None:
        """Cancel serve scope immediately.

        This method is idempotent, i.e., if the scope was already
        cancelled then this method silently does nothing.
        """
        if self.cancel_scope is None:
            return
        self.cancel_scope.cancel()

    async def serve(  # type: ignore[misc]  # "Implicit return in function which does not return"
        self,
        port: int,
        host: AnyStr | None = None,
        backlog: int | None = None,
    ) -> NoReturn:
        """Serve over TCP. See trio.open_tcp_listeners for argument details."""
        self.cancel_scope = trio.CancelScope()
        async with trio.open_nursery() as nursery:
            listeners = await trio.open_tcp_listeners(
                port,
                host=host,
                backlog=backlog,
            )

            async def handle_serve(
                task_status: trio.TaskStatus[Any] = trio.TASK_STATUS_IGNORED,
            ) -> None:
                assert self.cancel_scope is not None
                try:
                    with self.cancel_scope:
                        await trio.serve_listeners(
                            self.handler,
                            listeners,
                            handler_nursery=nursery,
                            task_status=task_status,
                        )
                except trio.Cancelled:
                    # Close all listeners
                    async with trio.open_nursery() as cancel_nursery:
                        for listener in listeners:
                            cancel_nursery.start_soon(listener.aclose)

            await nursery.start(handle_serve)

    async def handler(self, stream: trio.SocketStream) -> None:
        """Handle new client streams.

        Override in a subclass - Default only closes the stream
        """
        try:
            await stream.send_eof()
        finally:
            await stream.aclose()


if __name__ == "__main__":  # pragma: nocover
    print(f"{__title__}\nProgrammed by {__author__}.\n")
