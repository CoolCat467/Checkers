import pytest

from checkers import async_clock

pytest_plugins = ("pytest_trio",)


@pytest.mark.trio
async def test_tick() -> None:
    clock = async_clock.Clock()

    await clock.tick(60)
    result = await clock.tick(60)
    assert isinstance(result, int)
    assert result >= 0
    assert repr(clock).startswith("<Clock(")
    assert isinstance(clock.get_fps(), float)
    assert isinstance(clock.get_rawtime(), int)
    assert isinstance(clock.get_time(), int)


@pytest.mark.trio
async def test_tick_fps() -> None:
    clock = async_clock.Clock()

    for _ in range(20):
        await clock.tick(60)
    fps = clock.get_fps()
    assert isinstance(fps, float)
    assert fps >= 0
