import checkers.MiniMax_AI as ai


def generate_pieces(board_size: tuple[int, int]) -> dict[tuple[int, int], int]:
    """Generate data about each tile."""
    pieces: dict[tuple[int, int], int] = {}

    board_width, board_height = board_size
    # Reset tile data
    # Get where pieces should be placed
    z_to_1 = round(board_height / 3)  # White
    z_to_2 = (board_height - (z_to_1 * 2)) + z_to_1  # Black
    # For each xy position in the area of where tiles should be,
    for y in range(board_height):
        # Reset the x pos to 0
        for x in range(board_width):
            # Get the color of that spot by adding x and y mod the number of different colors
            color = (x + y) % 2
            # If a piece should be placed on that tile and the tile is not Red,
            if (not color) and ((y <= z_to_1 - 1) or (y >= z_to_2)):
                # Set the piece to White Pawn or Black Pawn depending on the current y pos
                piece = int(y <= z_to_1)
                pieces[(x, y)] = piece
    return pieces


def test_run() -> None:
    minimax = ai.CheckersMinimax()
    board_size = (8, 8)
    state = ai.State(board_size, True, generate_pieces(board_size))
    print(state)
    turns = 0

    while not minimax.terminal(state):
        print(f"\nTurn {turns}")
        value, action = minimax.adaptive_depth_minimax(state, 4, 6)
        state = minimax.result(state, action)
        print(state)
        turns += 1

    print(f"\nGame reached terminal state after {turns} turns")


def run() -> None:
    test_run()


if __name__ == "__main__":
    run()
