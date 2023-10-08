#!/usr/bin/env python3
# Network - Module for sending events over the network

"Network - Module for sending events over the network"

# Programmed by CoolCat467

__title__ = "Network"
__author__ = "CoolCat467"
__version__ = "0.0.0"


from collections.abc import Callable, Iterable
from typing import (
    Any,
    AnyStr,
    NoReturn,
    Self,
    SupportsIndex,
    TypeAlias,
)

import trio
from base_io import BaseAsyncReader, BaseAsyncWriter, StructFormat
from component import Component, ComponentManager, Event

BytesConvertable: TypeAlias = SupportsIndex | Iterable[SupportsIndex]


class Timeout(Exception):
    __slots__ = ()


class NetworkComponent(Component, BaseAsyncReader, BaseAsyncWriter):
    """Network Component (client)"""

    __slots__ = ("stream", "timeout")

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.stream: trio.SocketStream
        self.timeout: int | float = 3

    @classmethod
    def from_stream(cls, name: str, stream: trio.SocketStream) -> Self:
        self = cls(name)
        self.stream = stream
        return self

    async def connect(self, host: str, port: int) -> None:
        """Connect to host:port on TCP"""
        self.stream = await trio.open_tcp_stream(host, port)

    async def read(self, length: int) -> bytearray:
        """Read length bytes from stream"""
        content = bytearray()
        while max_read_count := length - len(content):
            recieved = b""
            with trio.move_on_after(self.timeout):
                recieved = await self.stream.receive_some(max_read_count)
                content.extend(recieved)
            if len(recieved) == 0:
                # No information at all
                if len(content) == 0:
                    raise Timeout(
                        "Server did not respond with any information. "
                        "This may be from a connection timeout."
                    )
                # Only sent a few bytes, but we requested more
                raise OSError(
                    f"Server stopped responding (got {len(content)} bytes, "
                    f"but expected {length} bytes)."
                    f" Partial obtained data: {content!r}"
                )
        return content

    async def write(self, data: bytes) -> None:
        """Write data to stream"""
        await self.stream.send_all(data)

    async def close(self) -> None:
        """Close the stream"""
        await self.stream.aclose()

    async def close_sending(self) -> None:
        """Close the sending half of the stream (send EOF)"""
        await self.stream.send_eof()


class NetworkEventComponent(NetworkComponent):
    """Network Event Component - Send events over the network"""

    __slots__ = ("_id_name_map", "_name_id_map")

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._id_name_map: dict[int, str] = {}
        self._name_id_map: dict[str, int] = {}

    def bind_handlers(self) -> None:
        """Register serverbound event handlers"""
        self.register_handlers(
            {name: self.write_event for name in self._name_id_map}
        )

    def register_serverbound_event(
        self, event_name: str, packet_id: int
    ) -> None:
        """Map event name to serverbound packet id"""
        if event_name in self._name_id_map:
            raise ValueError(f"{event_name!r} event already registered!")
        if self._id_name_map.get(packet_id) == event_name:
            raise ValueError(
                f"{event_name!r} events are also being recieved"
                f"from server with packet id {packet_id!r}, "
                "which will would lead to infinite looping over network"
            )
        self._name_id_map[event_name] = packet_id
        if self.manager_exists:
            self.register_handler(event_name, self.write_event)

    def register_serverbound_events(self, event_map: dict[str, int]) -> None:
        """Map event names to serverbound packet ids"""
        for event_name, packet_id in event_map.items():
            self.register_serverbound_event(event_name, packet_id)

    async def write_event(self, event: Event[bytearray]) -> None:
        """Send event to network"""
        await self.write_value(
            StructFormat.UINT, self._name_id_map[event.name]
        )
        await self.write_bytearray(event.data)

    async def read_event(self) -> Event[bytearray]:
        """Recieve event from network"""
        packet_id = await self.read_value(StructFormat.UINT)
        event_name = self._id_name_map[packet_id]
        event_data = await self.read_bytearray()
        return Event(event_name, event_data)

    async def raise_event_from_server(self) -> None:
        """Raise event recieved from server"""
        try:
            event = await self.read_event()
        except Timeout:
            return
        await self.raise_event(event)

    async def raise_events_from_server(self) -> None:
        """Raise events recieved from server"""
        while True:
            await self.raise_event_from_server()

    def register_clientbound_event(
        self, packet_id: int, event_name: str
    ) -> None:
        """Map clientbound packet id to event name"""
        if packet_id in self._id_name_map:
            raise ValueError(f"Packet ID {packet_id!r} already registered!")
        if self._name_id_map.get(event_name) == packet_id:
            raise ValueError(
                f"Packet id {packet_id!r} packets are also being recieved"
                f"from server with as {event_name!r} events, "
                "which will would lead to infinite looping over network"
            )
        self._id_name_map[packet_id] = event_name

    def register_clientbound_events(self, packet_map: dict[int, str]) -> None:
        """Map clientbound packet ids to event names"""
        for packet_id, event_name in packet_map.items():
            self.register_clientbound_event(packet_id, event_name)


class Server(ComponentManager):
    """Asynchronous TCP Server"""

    __slots__ = ("cancel_scope",)

    def __init__(self, name: str, own_name: str | None = None) -> None:
        super().__init__(name, own_name)
        self.cancel_scope: trio.CancelScope | None = None

    def stop_serving(self) -> None:
        """Cancels serve scope immediately.

        This method is idempotent, i.e., if the scope was already
        cancelled then this method silently does nothing."""
        if self.cancel_scope is None:
            return
        self.cancel_scope.cancel()

    async def serve(  # type: ignore[return-value]
        self,
        port: int,
        host: AnyStr | None = None,
        backlog: int | None = None,
    ) -> NoReturn:
        """Serve over TCP. See trio.open_tcp_listeners for argument details."""
        self.cancel_scope = trio.CancelScope()
        async with trio.open_nursery() as nursery:
            listeners = await trio.open_tcp_listeners(
                port, host=host, backlog=backlog
            )

            async def handle_serve(
                task_status: Any = trio.TASK_STATUS_IGNORED,
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
        """Main handler for new clients

        Override in a subclass - Default only closes the stream"""
        await stream.aclose()


def run() -> None:
    "Run test of module"

    async def client_connect(
        port: int, stop_server: Callable[[], None]
    ) -> None:
        await trio.sleep(0.05)
        # manager = ComponentManager("manager")

        client = NetworkEventComponent("client")
        # manager.add_component(client)

        await client.connect("127.0.0.1", port)

        client.register_serverbound_event("echo_event", 0)
        client.register_clientbound_event(1, "reposted_event")

        event = Event("echo_event", b"I will give my cat food to bob", 3)

        # await client.raise_event(event)
        await client.write_event(event)
        print(f"{await client.read_event() = }")

        await client.close()
        stop_server()

    async def run_async() -> None:
        "Run asynchronous test"

        class TestServer(Server):
            async def handler(self, stream: trio.SocketStream) -> None:
                client = NetworkEventComponent.from_stream("client", stream)

                client.register_clientbound_event(0, "repost_event")
                client.register_serverbound_event("repost_event", 1)

                await client.write_event(await client.read_event())
                await stream.aclose()

        server = TestServer("server")
        port = 3004
        async with trio.open_nursery() as nursery:
            nursery.start_soon(server.serve, port)
            nursery.start_soon(client_connect, port, server.stop_serving)
            nursery.start_soon(client_connect, port, server.stop_serving)

    trio.run(run_async)


if __name__ == "__main__":
    print(f"{__title__}\nProgrammed by {__author__}.\n")
    run()
