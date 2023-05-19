#!/usr/bin/env python3
# AI that plays checkers.

# IMPORTANT NOTE:
# For the game to recognize this as an
# AI, it's filename should have the words
# 'AI' in it.

NAME = "<AI NAME>"
AUTHOR = "<AUTHOR>"
__version__ = "0.0.0"

REGISTERED = False
# Please send your finnished version of your AI to CoolCat467 at Github
# for review and testing and obain permission to change this flag to True


def update(boardData):
    """This function is called by the game to inform the ai of any changes that have occored on the game board"""
    pass


def turn():
    """This function is called when the game requests the AI to return the piece it wants to move's id and the tile id the target piece should be moved to."""
    return None


def turnSuccess(tf):
    """This function is called immidiately after the ai's play is made, telling it if it was successfull or not"""


def stop():
    """This function is called immidiately after the game's window is closed"""
    pass


def init():
    """This function is called immidiately after the game imports the AI"""


##    send = {}
##    # Tell the game what the player names should be
##    send['player_names'] = ['Player '+str(i+1) for i in range(2)]
##    # Tell the game the starting turn
##    send['starting_turn'] = 1
##    # Tell the game it has to quit on a win
##    send['must_quit'] = True
##    return send

print("AI: NOT AI Module Loaded")
print("AI: " + NAME + " Created by " + AUTHOR)
