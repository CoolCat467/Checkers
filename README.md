# Checkers
Graphical Checkers Game with AI support

<!-- BADGIE TIME -->

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/CoolCat467/Checkers/main.svg)](https://results.pre-commit.ci/latest/github/CoolCat467/Checkers/main)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- END BADGIE TIME -->

## Installation
Ensure Python 3 is installed, and use pip to install this project.

```bash
pip install git+https://github.com/CoolCat467/Checkers.git
```

## Usage
After installing using the command above, running the following command
will start the game.

```bash
checkers_game
```

## Types of Play
On the title screen there are 3 play options:
1. Singleplayer
2. Host Networked Game
3. Join Networked Game

In a singleplayer game, the program hosts an internal server and the client can control both players.

In Host Networked Game, program hosts the server on the local network and posts advertisements every 2 seconds or so until two clients connect (includes hosting computer)

In Join Networked Game, program will listen for server advertisements on the local network and display said servers, and when you click on a discovered LAN server client will connect and game should begin.

Once game has begun, if server was hosted, LAN server advertisements stop and play begins

## How to Play
As per official American Checkers rules, Black plays first.

To perform a turn, click on the piece you would like to move with the mouse cursor.
Once this happens, all valid move destinations will be displayed via tiles with green outlines.

Following official American Checkers rules, note that if a capture (jumping over an opponent's piece, taking that piece out of play) is available, it must be taken and otherwise valid moves non-capture moves will not be available.

Once green outline tiles appear, you can either click one of the valid destination tiles to complete your turn or click a different piece to select that piece instead.

Once you click a valid destination, that move is performed, a movement animation will be shown, and it is now the other player's turn.

Play continues indefinitely until either a player no longer has pieces they are able to move or there is no valid move they are able to complete. In these events, said player's opponent wins.

Initially, all player have pawns, which are only able to move forward towards the player's opponent's side of the board.

In the event a pawn reaches the opposite side of the board, it is "kinged" and is now able to move in all directions.

In American Checkers, pawns can only capture in the forward direction, just like their movement. Kings do not have this limitation, likewise like their movement.


## Playing Against A Computer Player (AI)
There are two computer players I have made for this game. Both connect to all discovered LAN servers and play until the game is over.
To start playing against Minimax AI:
```bash
python computer_players/MiniMax_AI.py
```

To start playing against Max Y Position Jumping AI (very dumb):
```bash
python computer_players/Y_Max_Jumper_AI.py
```


### Links
* Source Code - https://github.com/CoolCat467/Checkers.git
* Issues      - https://github.com/CoolCat467/Checkers/issues

### License
-------
Code and documentation are available according to the GNU General Public License v3.0 (see [LICENSE](https://github.com/CoolCat467/Checkers/blob/HEAD/LICENSE)).
