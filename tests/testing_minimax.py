import time

import MiniMax_AI as ai

from checkers.state import State, generate_pieces


def test_run() -> None:
    minimax = ai.CheckersMinimax()
    board_size = (8, 8)
    state = State(board_size, generate_pieces(*board_size))
    print(state)
    turns = 0

    while not minimax.terminal(state):
        print(f"\nTurn {turns}")
        start = time.perf_counter_ns()
        _value, action = minimax.alphabeta(state, 4)
        end = time.perf_counter_ns()
        print(f"Took {(end - start) / 1e9:.2} seconds")
        state = minimax.result(state, action)
        print(state)
        turns += 1

    print(f"\nGame reached terminal state after {turns} turns")


def run() -> None:
    test_run()


if __name__ == "__main__":
    run()
