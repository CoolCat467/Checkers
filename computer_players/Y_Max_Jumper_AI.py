#!/usr/bin/env python3
# AI that plays checkers.

__title__ = "Get to other side + best jump AI"
__author__ = "CoolCat467"
__version__ = "1.0.0"
__ver_major__ = 1
__ver_minor__ = 0
__ver_patch__ = 0


import random
from typing import TypeVar

import trio
from checkers import GameClient
from component import (
    Component,
    ComponentManager,
    Event,
    ExternalRaiseManager,
)
from state import Action, Pos, State

T = TypeVar("T")

PORT = 31613


def turn(state: State) -> Action:
    """This function is called when the game requests the AI to return the piece it wants to move's id and the tile id the target piece should be moved to."""
    # We have no idea what jumps we can make nor tiles we can select
    jump_tiles = {}
    select_tiles = {}

    # For each tile id in tileids
    for piece_pos, piece_type in state.get_pieces():
        # If the tile's piece is one of ours,
        if piece_type in {state.turn, state.turn + 2}:
            action_set = state.get_actions_set(piece_pos)
            # If this our piece can make jumps,
            if action_set.jumps:
                # Get the number of jumps each end point would make
                v = [len(v) for v in list(action_set.jumps.values())]
                # Get the end point with the most jumps
                k = list(action_set.jumps.keys())[v.index(max(v))]
                # Store the target tile id and the end point with the most jumps in dictionary
                # with the number of jumps that moves makes
                jump_tiles[max(v)] = [piece_pos, k]
            # Get the moves our piece can make
            moves = action_set.moves
            # If our piece can move,
            if moves:
                # Add it's moves to the dictionary of movable pieces at key of target tile id
                select_tiles[piece_pos] = moves
    # If there are no jumps we can make,
    if not jump_tiles:
        # Get a list of selectable target tiles
        selectable = list(select_tiles.keys())
        y_pos = {}
        for target in selectable:
            possible_moves = select_tiles[target]
            ##                print(target)
            ##                print(possible_moves)
            for move in possible_moves:
                _x, y = move
                if y not in y_pos:
                    y_pos[y] = []
                y_pos[y].append([target, move])
        max_y = max(y_pos)
        best_y = y_pos[max_y]
        for target, _dest in best_y:
            if int(state.pieces[target]) >= 2:
                # If kinged is best, make it start to come back
                y_pos = {}
                for move in select_tiles[target]:
                    _x, y = move
                    if y not in y_pos:
                        y_pos[y] = []
                    y_pos[y].append([target, move])
                min_y = min(y_pos)
                return state.action_from_points(
                    *random.choice(  # noqa: S311  # Not important to be cryptographically safe
                        y_pos[min_y]
                    )
                )
        ##            target = random.choice(selectable)
        ##            # Get the possible moves that piece can make
        ##            possibleMoves = select_tiles[target]
        ##            # Choose a random valid destination that piece can make as our destination tile id
        ##            destination= random.choice(possibleMoves)#[len(possibleMoves)-1]
        return state.action_from_points(
            *random.choice(  # noqa: S311  # Not important to be cryptographically safe
                best_y
            )
        )
    else:
        # If we can make jumps,
        # Get the jump with the most jumps possible
        select = max(jump_tiles.keys())
        # Set our target to that jump's starting tile id
        target = jump_tiles[select][0]
        # Set our destination to that jump's end tile id
        destination = jump_tiles[select][1]
    # Tell the game about our decision
    return state.action_from_points(target, destination)


class RemoteState(Component):
    __slots__ = ("state", "pieces", "has_initial", "playing_as")

    def __init__(self) -> None:
        super().__init__("remote_state")

        self.state = State((8, 8), False, {})
        self.has_initial = False
        self.pieces: dict[Pos, int] = {}

        self.playing_as = 1

    def bind_handlers(self) -> None:
        self.register_handlers(
            {
                "game_action_complete": self.handle_action_complete,
                "game_winner": self.handle_game_over,
                "game_initial_config": self.handle_initial_config,
                "gameboard_create_piece": self.handle_create_piece,
            }
        )

    async def preform_action(self, action: Action) -> None:
        """Raise events to perform game action."""
        await self.raise_event(
            Event(
                "gameboard_piece_clicked",
                (
                    action.from_pos,
                    self.state.pieces[action.from_pos],
                ),
            )
        )
        await self.raise_event(Event("gameboard_tile_clicked", action.to_pos))

    async def preform_turn(self) -> None:
        """Perform turn"""
        print("preform_turn")
        if self.state.check_for_win() is not None:
            print("Terminal state, not performing turn")
            return
        action = turn(self.state)
        await self.preform_action(action)

    async def handle_action_complete(
        self, event: Event[tuple[Pos, Pos, int]]
    ) -> None:
        """Perform action on internal state and perform our turn if possible."""
        from_pos, to_pos, turn = event.data
        action = self.state.action_from_points(from_pos, to_pos)
        self.state = self.state.preform_action(action)
        ##        print(f'{turn = }')
        if turn == self.playing_as:
            await self.preform_turn()

    async def handle_create_piece(self, event: Event[tuple[Pos, int]]) -> None:
        """Update internal pieces if we haven't had the initial setup event."""
        if self.has_initial:
            return
        pos, type_ = event.data
        self.pieces[pos] = type_

    async def handle_initial_config(
        self, event: Event[tuple[Pos, int]]
    ) -> None:
        """Set up initial state and perform our turn if possible."""
        board_size, turn = event.data
        self.state = State(board_size, turn, self.pieces)
        self.has_initial = True
        if turn == self.playing_as:
            await self.preform_turn()

    async def handle_game_over(self, event: Event[int]) -> None:
        """Raise network_stop event so we disconnect from server."""
        self.has_initial = False
        await self.raise_event(Event("network_stop", None))


class MachineClient(ComponentManager):
    __slots__ = ("running",)

    def __init__(self) -> None:
        super().__init__("machine_client")

        self.running = True

        self.add_components((RemoteState(), GameClient("game_client")))

    def bind_handlers(self) -> None:
        self.register_handlers({"network_stop": self.handle_network_stop})

    ##    async def raise_event(self, event: Event) -> None:
    ##        """Raise event but also log it if not tick."""
    ##        if event.name not in {"tick"}:
    ##            print(f'{event = }')
    ##        return await super().raise_event(event)

    async def handle_network_stop(self, event: Event[None]) -> None:
        """Set self.running to false on network disconnect."""
        self.running = False


async def run_client() -> None:
    """Run machine client and raise tick events."""
    async with trio.open_nursery() as main_nursery:
        event_manager = ExternalRaiseManager(
            "checkers", main_nursery, "client"
        )
        client = MachineClient()
        event_manager.add_component(client)
        await event_manager.raise_event(
            Event("client_connect", ("127.0.0.1", PORT))
        )
        print("Connected to server")
        while client.running:
            await event_manager.raise_event(Event("tick", None))

            # Not sure why we need this but nothing seems to work without it...
            await trio.sleep(0.01)


def run() -> None:
    """Synchronous entry point."""
    trio.run(run_client)


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    run()
