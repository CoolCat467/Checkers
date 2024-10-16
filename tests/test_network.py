from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import trio
import trio.testing

from checkers.component import ComponentManager, Event
from checkers.network import (
    NetworkComponent,
    NetworkEventComponent,
    NetworkStreamNotConnectedError,
    NetworkTimeoutError,
    Server,
)

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.trio
async def client_connect(port: int, stop_server: Callable[[], None]) -> None:
    await trio.sleep(0.05)
    # manager = ComponentManager("manager")

    client = NetworkEventComponent("client")
    # manager.add_component(client)

    await client.connect("127.0.0.1", port)

    client.register_network_write_event("echo_event", 0)
    client.register_read_network_event(1, "reposted_event")

    event = Event(
        "echo_event",
        bytearray("I will give my cat food to bob", "utf-8"),
        3,
    )

    # await client.raise_event(event)
    await client.write_event(event)
    print(f"{await client.read_event() = }")

    await client.close()
    stop_server()


@pytest.mark.trio
async def run_async() -> None:
    class TestServer(Server):
        async def handler(self, stream: trio.SocketStream) -> None:
            client = NetworkEventComponent.from_stream("client", stream=stream)

            client.register_read_network_event(0, "repost_event")
            client.register_network_write_event("repost_event", 1)

            await client.write_event(await client.read_event())
            await stream.aclose()

    server = TestServer("server")
    port = 3004
    async with trio.open_nursery() as nursery:
        nursery.start_soon(server.serve, port)
        nursery.start_soon(client_connect, port, server.stop_serving)
        nursery.start_soon(client_connect, port, server.stop_serving)


def test_not_connected() -> None:
    client = NetworkComponent("name")
    assert client.not_connected
    with pytest.raises(NetworkStreamNotConnectedError):
        print(client.stream)


@pytest.mark.trio
async def test_from_stream() -> None:
    stream = trio.testing.MemorySendStream()

    named = NetworkComponent.from_stream(
        kwargs={"name": "name"},
        stream=stream,
    )
    with pytest.raises(RuntimeError, match="Already connected!"):
        await named.connect("example.com", 80)
    await named.close()


@pytest.mark.trio
async def test_register_network_write_event() -> None:
    client = NetworkEventComponent("client")
    client.register_network_write_event("echo_event", 0)
    with pytest.raises(ValueError, match="event already registered"):
        client.register_network_write_event("echo_event", 0)
    client.register_read_network_event(0, "reposted_event")
    with pytest.raises(ValueError, match="events are also being received"):
        client.register_network_write_events({"reposted_event": 0})
    with pytest.raises(RuntimeError, match="Unhandled network event name"):
        await client.write_event(Event("jerald event", bytearray()))
    client.register_network_write_events({})


@pytest.mark.trio
async def test_register_network_read_event() -> None:
    one, two = trio.testing.memory_stream_pair()
    client_one = NetworkEventComponent.from_stream("one", stream=one)
    client_two = NetworkEventComponent.from_stream("two", stream=two)
    client_one.register_network_write_event("echo_event", 0)
    await client_one.write_event(
        Event(
            "echo_event",
            bytearray("I will give my cat food to bob", "utf-8"),
        ),
    )
    with pytest.raises(RuntimeError, match="Unhandled packet ID 0"):
        await client_two.read_event()
    with pytest.raises(ValueError, match="Packet id 0 packets are also"):
        client_one.register_read_network_event(0, "echo_event")
    client_two.register_read_network_event(0, "reposted_event")
    with pytest.raises(ValueError, match="Packet ID 0 already registered!"):
        client_two.register_read_network_events({0: "type_two"})
    client_two.register_read_network_events({})


@pytest.mark.trio
async def test_event_transmission() -> None:
    one, two = trio.testing.memory_stream_pair()
    client_one = NetworkEventComponent.from_stream("one", stream=one)
    manager = ComponentManager("manager")
    async with NetworkEventComponent.from_stream(
        "two",
        stream=two,
    ) as client_two:
        manager.add_component(client_one)

        assert not client_one.not_connected

        client_one.register_network_write_event("echo_event", 0)
        client_two.register_read_network_event(0, "reposted_event")

        event = Event(
            "echo_event",
            bytearray("I will give my cat food to bob", "utf-8"),
            3,
        )

        await client_one.write_event(event)
        read_event = await client_two.read_event()
        assert read_event.name == "reposted_event"
        assert read_event.data == event.data

        await client_one.write_event(event)
        assert (
            await two.receive_some()
            == b"\x00\x1eI will give my cat food to bob"
        )

        await client_one.wait_write_might_not_block()
        await one.send_all(b"")
        client_two.timeout = 0.05
        with pytest.raises(NetworkTimeoutError):
            await client_two.read_event()
        await one.send_all(b"cat")
        with pytest.raises(OSError, match="Server stopped responding"):
            await client_two.read(4)

        await client_one.send_eof()
        await client_one.send_eof()

        await client_one.close()
        await client_one.close()


def test_server() -> None:
    server = Server("name")
    server.stop_serving()
    server.serve_cancel_scope = trio.CancelScope()
    server.stop_serving()
