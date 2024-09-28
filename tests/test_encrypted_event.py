from __future__ import annotations

import pytest
import trio
import trio.testing

from checkers.component import Event
from checkers.encrypted_event import EncryptedNetworkEventComponent

pytest_plugins = ("pytest_trio",)


@pytest.mark.trio
async def test_event_transmission() -> None:
    one, two = trio.testing.memory_stream_pair()
    client_one = EncryptedNetworkEventComponent.from_stream("one", stream=one)
    client_two = EncryptedNetworkEventComponent.from_stream("two", stream=two)

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

    await client_one.close()
    await client_two.close()


@pytest.mark.trio
async def test_event_encrypted_transmission() -> None:
    verification_token = bytes.fromhex("da053623dd3dcd441e105ee5ce212ac8")
    shared_secret = bytes.fromhex(
        "95a883358f09cd5698b3cf8a414a8a659a35c4eb877e9b0228b7f64df85b0f26",
    )

    one, two = trio.testing.memory_stream_pair()
    client_one = EncryptedNetworkEventComponent.from_stream("one", stream=one)
    client_two = EncryptedNetworkEventComponent.from_stream("two", stream=two)

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
        == b"\x00\x00\x1eI will give my cat food to bob"
    )

    client_one.enable_encryption(shared_secret, verification_token)
    client_two.enable_encryption(shared_secret, verification_token)

    await client_one.write_event(event)
    read_event = await client_two.read_event()
    assert read_event.name == "reposted_event"
    assert read_event.data == event.data

    await client_one.write_event(event)
    assert await two.receive_some() == bytearray.fromhex(
        "80a24bdaf285718a7c33223da8d98567ca21bdb82c7ebdd46e33cb6dc14b94a230",
    )

    await client_one.close()
    await client_two.close()
