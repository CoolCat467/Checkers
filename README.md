# Checkers
Graphical Checkers Game with AI support

<!-- BADGIE TIME -->

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![code style: black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)

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

## How to play
In a two player game, the starting player is randomly selected, and that
player will be able to make a move.

Making a move:
All valid moves are pre-calculated by the game, and only a valid
move is able to be played successfully.

To move a piece, the user selects a game tile with a piece on it
by moving the mouse cursor over the tile and pressing the left click
button on the mouse/track pad.

Once a piece is selected, it will gain a yellow outline and all
valid tiles that the piece is able to be moved to gain a blue
outline. If no valid moves are found, no tiles will gain a blue
outline. The piece will now follow the mouse cursor, but the
tile selected's piece will remain.

If a piece is selected and one of the empty tiles are selected,
if that tile is a valid move, the selected piece will be played
to that empty tile, the original selected tile will vanish,
valid tiles will lose their blue outline, the cursor will no
longer be carrying the piece, and it will now be the other
player's turn.

If an AI is playing against the player, the player will make
plays as described above, but the AI (which is always the black
player) will make it's move instantly. While the opponent is making
it's play, the game will cease to run, and if the AI takes a
while to make it's play, the screen will freeze.

Once the game has been won, the game will display the winner
and in a two player game, a button will appear to return to the title.

If you are interested in making an AI for this game, there is a lot
of information in the game files and in the example checkers AI
