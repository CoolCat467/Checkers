import gc

import pytest

from checkers.statemachine import (
    AsyncState,
    AsyncStateMachine,
    State,
    StateMachine,
)


def test_state() -> None:
    state = State[StateMachine]("waffle_time")

    assert state.name == "waffle_time"

    with pytest.raises(
        RuntimeError,
        match="^State has no statemachine bound$",
    ):
        print(state.machine)


def test_state_repr() -> None:
    state = State[StateMachine]("waffle_time")
    assert repr(state) == "State('waffle_time')"


def test_async_state() -> None:
    state = AsyncState[AsyncStateMachine]("waffle_time")

    assert state.name == "waffle_time"

    with pytest.raises(
        RuntimeError,
        match="^State has no statemachine bound$",
    ):
        print(state.machine)


def test_state_machine_add() -> None:
    machine = StateMachine()
    add_actions_run = False

    class TestState(State[StateMachine]):
        def add_actions(self) -> None:
            nonlocal add_actions_run
            add_actions_run = True

    machine.add_state(TestState("test"))
    bob = State[StateMachine]("bob")
    with pytest.raises(RuntimeError, match="State has no statemachine bound"):
        assert bob.machine is not None
    with pytest.raises(TypeError, match="is not an instance of State!"):
        machine.add_state(AsyncState("test"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="is not a registered State."):
        machine.remove_state("waffle")
    machine.add_state(bob)
    assert add_actions_run

    assert bob.machine is machine

    del machine
    # make sure gc collects machine
    for _ in range(3):
        gc.collect()

    with pytest.raises(RuntimeError, match="State has no statemachine bound"):
        assert bob.machine is not None


def test_state_machine_think() -> None:
    machine = StateMachine()
    machine.think()
    assert repr(machine) == "<StateMachine {}>"
    machine.add_states(())
    machine.add_states((State("jerald"),))
    assert repr(machine) == "<StateMachine {'jerald': State('jerald')}>"
    machine.add_state(State("bob"))
    machine.set_state("jerald")
    machine.set_state("bob")
    machine.set_state("jerald")
    machine.think()
    machine.remove_state("jerald")
    machine.remove_state("bob")
    machine.set_state(None)
    with pytest.raises(KeyError, match="not found in internal states"):
        machine.set_state("bob")
    machine.add_state(State("bob"))

    class ToBob(State[StateMachine]):
        __slots__ = ()

        def check_conditions(self) -> str:
            return "bob"

    machine.add_state(ToBob("tom"))
    machine.set_state("tom")
    machine.think()


@pytest.mark.trio
async def test_async_state_machine_add() -> None:
    machine = AsyncStateMachine()

    machine.add_state(AsyncState("test"))
    bob = AsyncState[AsyncStateMachine]("bob")
    with pytest.raises(RuntimeError, match="State has no statemachine bound"):
        assert bob.machine is not None
    with pytest.raises(TypeError, match="is not an instance of AsyncState!"):
        machine.add_state(State("test"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="is not a registered AsyncState."):
        machine.remove_state("waffle")
    machine.add_state(bob)

    assert bob.machine is machine

    del machine
    # make sure gc collects machine
    for _ in range(3):
        gc.collect()

    with pytest.raises(RuntimeError, match="State has no statemachine bound"):
        assert bob.machine is not None


@pytest.mark.trio
async def test_async_state_machine_think() -> None:
    machine = AsyncStateMachine()
    await machine.think()
    machine.add_states(())
    jerald = AsyncState[AsyncStateMachine]("jerald")
    machine.add_states((jerald,))
    machine.add_state(AsyncState("bob"))
    await machine.set_state("jerald")
    await machine.set_state("bob")
    await machine.set_state("jerald")
    await machine.think()
    machine.remove_state("jerald")
    await jerald.exit_actions()
    machine.remove_state("bob")
    await machine.set_state(None)
    with pytest.raises(KeyError, match="not found in internal states"):
        await machine.set_state("bob")
    machine.add_state(AsyncState("bob"))

    class ToBob(AsyncState[AsyncStateMachine]):
        __slots__ = ()

        async def check_conditions(self) -> str:
            await super().check_conditions()
            return "bob"

    machine.add_state(ToBob("tom"))
    await machine.set_state("tom")
    await machine.think()
