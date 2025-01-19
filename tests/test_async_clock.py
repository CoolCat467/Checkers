from __future__ import annotations

import pytest

from checkers.async_clock import Clock


@pytest.fixture
def clock() -> Clock:
    return Clock()


def test_initial_values(clock: Clock) -> None:
    assert clock.fps == 0.0
    assert clock.fps_count == 0


def test_get_fps(clock: Clock) -> None:
    assert clock.get_fps() == 0.0


def test_get_rawtime(clock: Clock) -> None:
    assert clock.get_rawtime() == 0


def test_get_time(clock: Clock) -> None:
    assert clock.get_time() == 0


@pytest.mark.trio
async def test_tick_elapsed(clock: Clock) -> None:
    time_passed = await clock.tick()
    assert time_passed >= 0

    # Test with a specific framerate
    time_passed = await clock.tick(60)
    assert time_passed >= int(1e9 // 60)

    # Test with a zero framerate
    time_passed = await clock.tick(0)
    assert time_passed >= 0


@pytest.mark.trio
async def test_tick(clock: Clock) -> None:
    await clock.tick(60)
    result = await clock.tick(60)
    assert isinstance(result, int)
    assert result >= int(1e9 // 60)
    assert repr(clock).startswith("<Clock(")
    assert isinstance(clock.get_fps(), float)
    assert isinstance(clock.get_rawtime(), int)
    assert isinstance(clock.get_time(), int)


@pytest.mark.trio
async def test_tick_fps(clock: Clock) -> None:
    for _ in range(20):
        await clock.tick(60)
    fps = clock.get_fps()
    assert isinstance(fps, float)
    assert fps >= 0
