from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import trio
from checkers.component import Event
from checkers.network import NetworkEventComponent, Server

if TYPE_CHECKING:
    from collections.abc import Callable

pytest_plugins = ("pytest_trio",)


@pytest.mark.trio()
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


@pytest.mark.trio()
async def run_async() -> None:
    "Run asynchronous test"

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
