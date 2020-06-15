# Checkers
Graphical Checkers Game with AI support

How to run the game:
1. Download all files into one folder
2. Run "checkers.py"

How to play:
If pygame or any important modules are not found, the program
will try to install or request the user to install all required
files.

Once the program starts, if AI files are found, it will ask you if
you wish to play against an AI. If you say yes, it will list the names
of all found AIs and request the user to input the number corresponding to
the AI they wish to play. If a valid number is returned, the game will then
load that AI and the game will begin. If no AIs are found or the user
does not wish to play against an AI, a two player game will begin.

In a two player game, the starting player is randomly selected, and that
player will be able to make a move.

In a game against an AI, the starting player can be defined by the AI,
but if the AI does not define a starting player, the program will
randomly select a starting player as in a two player game.

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
player) will make it's move instantly. While the AI is making
it's play, the game will cease to run, and if the AI takes a
while to make it's play, the screen will freeze.

Once the game has been won, the game will display the winner
and in a two player game, a button will appear to play again.
If an AI is loaded, the AI can control whether the button will
cause the game to restart, or cause the game to close.

If you are interested in making an AI for this game, there is a lot
of information in the game files and in the example checkers AI

# Hacky Checkers Client and Server usage
The Hacky Checkers Not AI is a client for the Hacky Checkers Server,
but acts as an AI in the view of the game. In reality, the AI acts
as a network connection, allowing two players to play checkers
across a local network, or even accost separate networks if the
server is hosted from a address accessible from outside the local
network. 

To use the Hacky Checkers Not AI, the user needs to start the
checkers game program, select they wish to play against an AI,
and select the Hacky Checkers Not AI's number in the displayed
list. If the Hacky Checkers Not AI does not appear in the
list, ensure the file is in the same folder as the game
and that the filename has not been modified. Once selected,
the game will attempt to initiate the "AI" as soon as it is loaded.
Once the client is initiated, it will ask the user for an IP address
to connect to. If a server is not active on that address, the
client will very likely tell the user that the connection was
refused. If this occurs, ensure the server is active on that
address, that you have entered the IP Address correctly, and
that a game is not already running on that server.

To use the Hacky Checkers Server, the user must run the
server program. If the program cannot bind to the host
computer's IP Address, ensure no other programs are
attempting to use your computer's IP Address on port
"8673" and that your computer is connected to the
internet. Once the server successfully starts, it
will wait for exactly two clients to connect to it,
no more, no less, and once this occurs, it will run
until either an error occurs or a client disconnects.
When this happens, the server will wait for five
seconds for all clients to leave the server, and once
this time elapses, if clients are still connected, the server
will attempt to forcefully disconnect them. In both cases,
after words the server will close and the program will terminate.

When both clients are connected, both game windows will appear
and one client will be able to make a play. The other client
will be frozen, unable to do anything until its opponent has
made its move. Once this occurs, the client that was waiting will
now be able to make a move, and the client that made a move will
wait for the other client to make it's move. This will continue
indefinitely until the game has been won by either client,
upon which the game will display the winner, and a button will
appear to close the game.
