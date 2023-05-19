#!/usr/bin/env python3
# AI that plays checkers.

# IMPORTANT NOTE:
# For the game to recognize this as an
# AI, it's filename should have the words
# 'AI' in it.

# This is an example AI, and is no way perfect, except maybe the
# jumping part of it lol.

__title__ = "Super Simple AI Example"
__author__ = "CoolCat467"
__version__ = "0.0.2"
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 2

__game__ = "Checkers"

import random

global BOARD


def update(boardData):
    """This function is called by the game to inform the ai of any changes that have occored on the game board"""
    global BOARD
    BOARD = boardData
    # Below is an example of empty board data that would be sent with an empty board to this ai
    emptyBoardData = {
        "boardsize": (8, 8),
        "won": "None",
        "tiles": {
            "A8": {
                "open": False,
                "piece": "1",
                "moves": [],
                "jumps": [[], {}],
                "xy": (0, 0),
                "color": 0,
            },
            "B8": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (1, 0),
                "color": 1,
            },
            "C8": {
                "open": False,
                "piece": "1",
                "moves": [],
                "jumps": [[], {}],
                "xy": (2, 0),
                "color": 0,
            },
            "D8": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (3, 0),
                "color": 1,
            },
            "E8": {
                "open": False,
                "piece": "1",
                "moves": [],
                "jumps": [[], {}],
                "xy": (4, 0),
                "color": 0,
            },
            "F8": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (5, 0),
                "color": 1,
            },
            "G8": {
                "open": False,
                "piece": "1",
                "moves": [],
                "jumps": [[], {}],
                "xy": (6, 0),
                "color": 0,
            },
            "H8": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (7, 0),
                "color": 1,
            },
            "A7": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (0, 1),
                "color": 1,
            },
            "B7": {
                "open": False,
                "piece": "1",
                "moves": [],
                "jumps": [[], {}],
                "xy": (1, 1),
                "color": 0,
            },
            "C7": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (2, 1),
                "color": 1,
            },
            "D7": {
                "open": False,
                "piece": "1",
                "moves": [],
                "jumps": [[], {}],
                "xy": (3, 1),
                "color": 0,
            },
            "E7": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (4, 1),
                "color": 1,
            },
            "F7": {
                "open": False,
                "piece": "1",
                "moves": [],
                "jumps": [[], {}],
                "xy": (5, 1),
                "color": 0,
            },
            "G7": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (6, 1),
                "color": 1,
            },
            "H7": {
                "open": False,
                "piece": "1",
                "moves": [],
                "jumps": [[], {}],
                "xy": (7, 1),
                "color": 0,
            },
            "A6": {
                "open": False,
                "piece": "1",
                "moves": ["B5"],
                "jumps": [[], {}],
                "xy": (0, 2),
                "color": 0,
            },
            "B6": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (1, 2),
                "color": 1,
            },
            "C6": {
                "open": False,
                "piece": "1",
                "moves": ["B5", "D5"],
                "jumps": [[], {}],
                "xy": (2, 2),
                "color": 0,
            },
            "D6": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (3, 2),
                "color": 1,
            },
            "E6": {
                "open": False,
                "piece": "1",
                "moves": ["D5", "F5"],
                "jumps": [[], {}],
                "xy": (4, 2),
                "color": 0,
            },
            "F6": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (5, 2),
                "color": 1,
            },
            "G6": {
                "open": False,
                "piece": "1",
                "moves": ["F5", "H5"],
                "jumps": [[], {}],
                "xy": (6, 2),
                "color": 0,
            },
            "H6": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (7, 2),
                "color": 1,
            },
            "A5": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (0, 3),
                "color": 1,
            },
            "B5": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (1, 3),
                "color": 0,
            },
            "C5": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (2, 3),
                "color": 1,
            },
            "D5": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (3, 3),
                "color": 0,
            },
            "E5": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (4, 3),
                "color": 1,
            },
            "F5": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (5, 3),
                "color": 0,
            },
            "G5": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (6, 3),
                "color": 1,
            },
            "H5": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (7, 3),
                "color": 0,
            },
            "A4": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (0, 4),
                "color": 0,
            },
            "B4": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (1, 4),
                "color": 1,
            },
            "C4": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (2, 4),
                "color": 0,
            },
            "D4": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (3, 4),
                "color": 1,
            },
            "E4": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (4, 4),
                "color": 0,
            },
            "F4": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (5, 4),
                "color": 1,
            },
            "G4": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (6, 4),
                "color": 0,
            },
            "H4": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (7, 4),
                "color": 1,
            },
            "A3": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (0, 5),
                "color": 1,
            },
            "B3": {
                "open": False,
                "piece": "0",
                "moves": ["A4", "C4"],
                "jumps": [[], {}],
                "xy": (1, 5),
                "color": 0,
            },
            "C3": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (2, 5),
                "color": 1,
            },
            "D3": {
                "open": False,
                "piece": "0",
                "moves": ["C4", "E4"],
                "jumps": [[], {}],
                "xy": (3, 5),
                "color": 0,
            },
            "E3": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (4, 5),
                "color": 1,
            },
            "F3": {
                "open": False,
                "piece": "0",
                "moves": ["E4", "G4"],
                "jumps": [[], {}],
                "xy": (5, 5),
                "color": 0,
            },
            "G3": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (6, 5),
                "color": 1,
            },
            "H3": {
                "open": False,
                "piece": "0",
                "moves": ["G4"],
                "jumps": [[], {}],
                "xy": (7, 5),
                "color": 0,
            },
            "A2": {
                "open": False,
                "piece": "0",
                "moves": [],
                "jumps": [[], {}],
                "xy": (0, 6),
                "color": 0,
            },
            "B2": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (1, 6),
                "color": 1,
            },
            "C2": {
                "open": False,
                "piece": "0",
                "moves": [],
                "jumps": [[], {}],
                "xy": (2, 6),
                "color": 0,
            },
            "D2": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (3, 6),
                "color": 1,
            },
            "E2": {
                "open": False,
                "piece": "0",
                "moves": [],
                "jumps": [[], {}],
                "xy": (4, 6),
                "color": 0,
            },
            "F2": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (5, 6),
                "color": 1,
            },
            "G2": {
                "open": False,
                "piece": "0",
                "moves": [],
                "jumps": [[], {}],
                "xy": (6, 6),
                "color": 0,
            },
            "H2": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (7, 6),
                "color": 1,
            },
            "A1": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (0, 7),
                "color": 1,
            },
            "B1": {
                "open": False,
                "piece": "0",
                "moves": [],
                "jumps": [[], {}],
                "xy": (1, 7),
                "color": 0,
            },
            "C1": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (2, 7),
                "color": 1,
            },
            "D1": {
                "open": False,
                "piece": "0",
                "moves": [],
                "jumps": [[], {}],
                "xy": (3, 7),
                "color": 0,
            },
            "E1": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (4, 7),
                "color": 1,
            },
            "F1": {
                "open": False,
                "piece": "0",
                "moves": [],
                "jumps": [[], {}],
                "xy": (5, 7),
                "color": 0,
            },
            "G1": {
                "open": True,
                "piece": "None",
                "moves": [],
                "jumps": [[], {}],
                "xy": (6, 7),
                "color": 1,
            },
            "H1": {
                "open": False,
                "piece": "0",
                "moves": [],
                "jumps": [[], {}],
                "xy": (7, 7),
                "color": 0,
            },
        },
    }


def turn():
    """This function is called when the game requests the AI to return the piece it wants to move's id and the tile id the target piece should be moved to."""
    global BOARD
    # If the game is not won,
    if BOARD["won"] == "None":
        # We have no idea what jumps we can make nor tiles we can select
        jumpTiles = {}
        selectTiles = {}
        # Get the tiles from the board data we got
        tiles = BOARD["tiles"]
        # Get the tile ids
        tileIds = tiles.keys()
        # For each tile id in tileids
        for tileId in tileIds:
            # Get the data for that tile
            tileData = tiles[tileId]
            # If the tile's piece is one of ours,
            if tileData["piece"] in ("1", "3"):
                # If this our piece can make jumps,
                if tileData["jumps"][0]:
                    # Get the jumps the piece can make
                    jumpsdict = tileData["jumps"][1]
                    # Get the number of jumps each end point would make
                    v = [len(v) for v in list(jumpsdict.values())]
                    # Get the end point with the most jumps
                    k = list(jumpsdict.keys())[v.index(max(v))]
                    # Store the target tile id and the end point with the most jumps in dictionary
                    # with the number of jumps that moves makes
                    jumpTiles[max(v)] = [tileId, k]
                # Get the moves our piece can make
                moves = tileData["moves"]
                # If our piece can move,
                if len(moves):
                    # Add it's moves to the dictonary of movable pieces at key of target tile id
                    selectTiles[tileId] = moves
        # If there are no jumps we can make,
        if not jumpTiles:
            # Get a list of selectable target tiles
            selectable = list(selectTiles.keys())
            # Choose a random target from the selectable target tile list
            target = random.choice(selectable)
            # Get the possible moves that piece can make
            possibleMoves = selectTiles[target]
            # Choose a random valid destination that piece can make as our destination tile id
            destination = random.choice(
                possibleMoves
            )  # [len(possibleMoves)-1]
        else:
            # If we can make jumps,
            # Get the jump with the most jumps possible
            select = max(jumpTiles.keys())
            # Set our target to that jump's starting tile id
            target = jumpTiles[select][0]
            # Set our destination to that jump's end tile id
            destination = jumpTiles[select][1]
        # Tell the game about our decision
        return target, destination
    # Otherwise, send that we don't know what to do.
    return None
    # In extreme cases, it may be necessary to quit the game,
    # for example, if your AI connects to the internet in some way.
    # In this case, you can also return 'QUIT', but PLEASE,
    # ONLY USE THIS IF IT IS TRULY NECESSARY


def turn_success(tf):
    """This function is called immidiately after the ai's play is made, telling it if it was successfull or not"""
    if not tf:
        print("AI: Something went wrong playing move...")


def stop():
    """This function is called immidiately after the game's window is closed"""
    pass


def init():
    """This function is called immidiately after the game imports the AI"""
    # We dunno what the board looks like, so set it to blank.
    global BOARD
    BOARD = {}


print("AI: AI Module Loaded")
print("AI: " + __title__ + " Created by " + __author__)
