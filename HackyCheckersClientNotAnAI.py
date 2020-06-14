#!/usr/bin/env python3
# NOT AI that is really a client for a checkers AI server.
# -*- coding: utf-8 -*-

# IMPORTANT NOTE:
# I know this may not be efficiant, but this is a bit of
# a challange I made for myself, in using nothing but
# what is already existant in the checkers game already
# to make a networked game. I did have to make some changes,
# though, that were absolutely necessary for proper function.

import os, socket
from random import choice
# Import choice for the event that something wierd happens
# (see turn() for information)

HOST = None# Given to us by user (but can be set to a default value here)
PORT = 8673# Port is this, which according to my research, nothing important in the public domain uses.
BUFSIZE = 1040# Standard message size is somewere around 300 bytes long, so this is fine.
WAKEUP = 60*3.5# Wake up/Re-sync every three and a half minnutes
WAKEUPMSG = 'Wake up and re-sync you fool!'# Re-sync message lul

NAME = 'Socket Checkers Client (Not an AI)'
AUTHOR = 'CoolCat467'
__version__ = '0.0.1'

REGISTERED = True
# Please send your finnished version of your AI to CoolCat467 at Github
# for review and testing and obain permission to change this flag to True.
# Flag doesn't really do much anyways, just a thing to indicate this AI has
# been tested by the creator for proper functionality.

global BOARD

emptyBoardData = {'boardsize': (8, 8), 'won': 'None', 'tiles': {'A8': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (0, 0), 'color': 0}, 'B8': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 0), 'color': 1}, 'C8': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (2, 0), 'color': 0}, 'D8': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 0), 'color': 1}, 'E8': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (4, 0), 'color': 0}, 'F8': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 0), 'color': 1}, 'G8': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (6, 0), 'color': 0}, 'H8': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 0), 'color': 1}, 'A7': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 1), 'color': 1}, 'B7': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (1, 1), 'color': 0}, 'C7': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 1), 'color': 1}, 'D7': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (3, 1), 'color': 0}, 'E7': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 1), 'color': 1}, 'F7': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (5, 1), 'color': 0}, 'G7': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 1), 'color': 1}, 'H7': {'open': False, 'piece': '1', 'moves': [], 'jumps': [[], {}], 'xy': (7, 1), 'color': 0}, 'A6': {'open': False, 'piece': '1', 'moves': ['B5'], 'jumps': [[], {}], 'xy': (0, 2), 'color': 0}, 'B6': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 2), 'color': 1}, 'C6': {'open': False, 'piece': '1', 'moves': ['B5', 'D5'], 'jumps': [[], {}], 'xy': (2, 2), 'color': 0}, 'D6': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 2), 'color': 1}, 'E6': {'open': False, 'piece': '1', 'moves': ['D5', 'F5'], 'jumps': [[], {}], 'xy': (4, 2), 'color': 0}, 'F6': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 2), 'color': 1}, 'G6': {'open': False, 'piece': '1', 'moves': ['F5', 'H5'], 'jumps': [[], {}], 'xy': (6, 2), 'color': 0}, 'H6': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 2), 'color': 1}, 'A5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 3), 'color': 1}, 'B5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 3), 'color': 0}, 'C5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 3), 'color': 1}, 'D5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 3), 'color': 0}, 'E5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 3), 'color': 1}, 'F5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 3), 'color': 0}, 'G5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 3), 'color': 1}, 'H5': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 3), 'color': 0}, 'A4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 4), 'color': 0}, 'B4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 4), 'color': 1}, 'C4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 4), 'color': 0}, 'D4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 4), 'color': 1}, 'E4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 4), 'color': 0}, 'F4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 4), 'color': 1}, 'G4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 4), 'color': 0}, 'H4': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 4), 'color': 1}, 'A3': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 5), 'color': 1}, 'B3': {'open': False, 'piece': '0', 'moves': ['A4', 'C4'], 'jumps': [[], {}], 'xy': (1, 5), 'color': 0}, 'C3': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 5), 'color': 1}, 'D3': {'open': False, 'piece': '0', 'moves': ['C4', 'E4'], 'jumps': [[], {}], 'xy': (3, 5), 'color': 0}, 'E3': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 5), 'color': 1}, 'F3': {'open': False, 'piece': '0', 'moves': ['E4', 'G4'], 'jumps': [[], {}], 'xy': (5, 5), 'color': 0}, 'G3': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 5), 'color': 1}, 'H3': {'open': False, 'piece': '0', 'moves': ['G4'], 'jumps': [[], {}], 'xy': (7, 5), 'color': 0}, 'A2': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (0, 6), 'color': 0}, 'B2': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (1, 6), 'color': 1}, 'C2': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (2, 6), 'color': 0}, 'D2': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (3, 6), 'color': 1}, 'E2': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (4, 6), 'color': 0}, 'F2': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (5, 6), 'color': 1}, 'G2': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (6, 6), 'color': 0}, 'H2': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (7, 6), 'color': 1}, 'A1': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (0, 7), 'color': 1}, 'B1': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (1, 7), 'color': 0}, 'C1': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (2, 7), 'color': 1}, 'D1': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (3, 7), 'color': 0}, 'E1': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (4, 7), 'color': 1}, 'F1': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (5, 7), 'color': 0}, 'G1': {'open': True, 'piece': 'None', 'moves': [], 'jumps': [[], {}], 'xy': (6, 7), 'color': 1}, 'H1': {'open': False, 'piece': '0', 'moves': [], 'jumps': [[], {}], 'xy': (7, 7), 'color': 0}}}

# PURE DATA SENDING WOULD REQUIRE A BUFFER 6275 BYTES LONG
##def dictToLst(dictionary):
##    data = ['{']
##    for key in dictionary.keys():
##        data.append(key)
##        data.append(':')
##        data.append(dictionary[key])
##        data.append(',')
##    data.append('}')
##    return data
##
##def changetostronly(board):
##    data = ['{']
##    for key in board.keys():
##        data.append(key)
##        if hasattr(board[key], 'keys'):
##            data.append(':')
##            data += dictToLst(board[key])
##            data.append('}')
##        else:
##            data.append('=')
##            data.append(board[key])
##    data.append('}')
##    return ' '.join([str(i) for i in data])

def board_data_to_str(board, flip=False):
    """Make the board data into a compressed string"""
    global TIDSHIFT
    # If the game has not been won, say 'N' insted of 'None'
    w = 'N' if board['won'] == 'None' else board['won']
    # The compressed string should start being 'w=' and then who's won, then '-'
    data = ['w='+str(w+'-')]
    # For each tile id in the game board's tile,
    for tid in board['tiles'].keys():
        # If the tile indicated by the tile id's color is black (playable tile)
        if not board['tiles'][tid]['color']:#If it's a playable tile
            # If data should be flipped,
            if flip:
                # Flip the tile id using the TIDSHIFT dictionary generated in init()
                data += [TIDSHIFT[tid]+'=']
            else:
                # Othewise, just put the tile in the data.
                data += [tid+'=']
            # Get the tile's piece.
            p = board['tiles'][tid]['piece']
            # If the piece is 'None', replace it with 'N'
            p = 'N' if p == 'None' else p
            # If the data should be flipped,
            if flip:
                # Flip the pieceid to be on the proper team
                p = {'0':'1', '1':'0', '2':'3', '3':'2', 'N':'N'}[p]
            # Add the piece to the list of data
            data.append(p)
            # If the piece was not None,
            if not p == 'N':
                # Get the moves that piece can make
                m = board['tiles'][tid]['moves']
                # If the data should be flipped,
                if flip:
                    # Flip the tile ids of the valid moves
                    m = [TIDSHIFT[i] for i in m]
                # If there are no moves, moves = 'N', otherwise join all valid moves by slashes
                m = 'N' if not len(m) else '/'.join(m)
                # Add the move data to the list of data
                data += ['=', m]
            # Add a dash to inicate we're going on to the next tile
            data.append('-')
    # Finally, return all the data as a string except the very last line, which is blank
    return ''.join(data)[:-1]

def str_to_board_info(string):#, flip=False):
    """Convert a board data sting into a board info list"""
    global TIDSHIFT
    # Split the data into each individual tile (dashes), and then spit the individual data declarations.
    data = [i.split('=') for i in string.split('-')]
    # Revision is initialized with who's won at index zero
    rev = [data[0]]
    # For each bit of tile data (everything but the won information in data)
    for i in data[1:]:
        # If the tile had no piece and didn't define it's moves,
        if len(i) == 2:
            # Get the tile id and piece from the data
            tid, p = i
            # Add the tile id, the piece id, and no moves to the revised data
            rev.append([tid, p, 'N'])
        elif len(i) == 3:# If the data is normal,
            # Just add it to the revised data with no changes
            rev.append(i)
##    if flip:
##        fdata = list(data[0])
##        for i in data[1:]:
##            fdata.append([TIDSHIFT[i[0]],
##                          {'0':'1', '1':'0', '2':'3', '3':'2', 'N':'N'}[i[1]],
##                          i[2]])
##        return fdata
    return rev

def findChange(old, new):
    """Find changes in and old board data string vs a new copy of the board and return moves"""
    global TIDSHIFT
    # Get the board info lists from each board string, ignoring won information
    one = str_to_board_info(old)[1:]#Ignore won information
    two = str_to_board_info(new)[1:]
    # Reverse the new piece of data so it can be used properly
    two = [i for i in reversed(two)]
    ## Get valid moves the old board can make
    # Get the start tile id and valid moves that tile can make if there are valid moves
    moves = [[i[0], i[2]] for i in one if i[2] != 'N']
    # Convert the move information so that each start tile corrosponds to each end tile, insted of
    # refrencing all end tiles.
    moves = sum([[[i[0], f] for f in i[1].split('/')] for i in moves], [])
    # Get all start and end points seperated
    startends = {i[0]:i[1] for i in moves}
##    starters = [i[0] for i in moves]
##    enders = [i[1] for i in moves]
    # Make a dictionary recoring the new data's index positions for each tile id
    # pointing to the tile's piece id value
    twotidpids = {two[i][0]:two[i][1] for i in range(len(two))}
    #twotids = {two[i][0]:i for i in range(len(two))}
##    twoends = [i for i in enders if two[twotids[i]][1] != 'N']
##    twostarts = [i for i in starters if two[twotids[i]][1] == 'N']
##    # Look at new data starting and ending positions for changes
##    twoends = [i for i in startends.values() if two[twotids[i]][1] != 'N']
##    twostarts = [i for i in startends.keys() if two[twotids[i]][1] == 'N']
    ## Get tiles that changed in the way that a valid move would
    # Get the end point tiles that their new version's piece id is not none
    twoends = [i for i in startends.values() if twotidpids[i] != 'N']
    # Get the start point tiles that their new version's piece id is now empty
    twostarts = [i for i in startends.keys() if twotidpids[i] == 'N']
    ## Find the proper move that was made
    # No found valid moves yet
    allmoves = []
    # For all the starting tile ids
    for s in twostarts:
        # For all the ending tile ids
        for e in twoends:
            # Get the move as it would appear in the valid moves list
            se = [s, e]#[TIDSHIFT[s], TIDSHIFT[e]]
            # If the move is valid and is not already in the list of moves to return,
            if se in moves and not se in allmoves:
                # Add the move the the list of moves
                allmoves.append(se)
    # Return all the valid moves that were made we found
    return allmoves

def disconnectFromServer():
    """Disconnect from the server socket"""
    global S
    try:
        S.send(b'[S] bye')
    except BaseException:
        pass
    S.close()

def update(boardData):
    """This function is called by the game to inform the ai of any changes that have occored on the game board"""
    global BOARD
    global S
    global OPPONENT
    global LASTSENT
    # If the game has been won,
    if not boardData['won'] == 'None':
        # Dissconnect from the server
        print('AI: Game Won!\nDisconnecting from Server...')
        disconnectFromServer()
    # If the board size is not 8 x 8,
    if not boardData['boardsize'] == (8, 8):
        # Break cause we can't handle that (theoretically COULD do 9 x 9, but no more tho...)
        raise RuntimeError('Board Size is not 8 x 8, and is not compatable with this AI Module (not an ai lol)')
    print('AI: Transmitting board data...')
##    changes = findChange(board_data_to_str(BOARD), boardData)
##    send += '-'.join(['/'.join(change) for change in changes])
    # Send the server a message addressed to our opponent with our new copy
    # of the board data.
    send = '['+OPPONENT+'] '+board_data_to_str(boardData, True)
##    if not send == LASTSENT:
    # Try to send the message to the server
    try:
        S.sendall(send.encode('utf-8'))
    except OSError:
        # If something broke, disconnect from the server
        print('AI: An error occored when trying to send board data to server.', file=os.sys.stderr)
        disconnectFromServer()
    else:
        # If it worked, record what we sent and tell the user it worked
        LASTSENT = str(send)
        print('AI: Transmission Sent.')
##    else:
##        print('Repeated message; skipping.')
    # Once we've sent everything, update our copy of board data
    BOARD = boardData

def turn():
    """This function is called when the game requests the AI to return the piece it wants to move's id and the tile id the target piece should be moved to."""
    global BOARD
    global S
    global OPPONENT
    global LASTRCVD
    global WAKEUPMSG
    print('AI: Awaiting Server for Play Data...')
    # Try to recieve data from the server
    try:
        rcvdData = S.recv(BUFSIZE).decode()
    except OSError:
        # If something broke, data is '', which gets processed as server ded.
        rcvdData = ''
    else:
        # Otherwise, tell the user we recieved data properly
        print('AI: Transmission recieved.')
    # If the data was None (somehow), replace it with ''. Otherwise, leave it how it is.
    rcvdData = '' if rcvdData is None else rcvdData
    # If the word 'bye' is in the list of words in any message,
    if 'bye' in sum([i.lower().split(' ') for i in rcvdData.split(';')], []):
        # Disconnect from the server and quit
        print('AI: Server shutting down. Quitting...', file=os.sys.stderr)
        disconnectFromServer()
        return 'QUIT'
    elif rcvdData == '':# If the server died
        # Tell the user it died and disconnect from server and quit
        print('AI: Server died. Quitting...', file=os.sys.stderr)
        disconnectFromServer()
        return 'QUIT'
##    data = rcvdData[:-1].split(';')
##    newdata = data[len(data)-1].split(' ')[1]
##    changes = findChange(board_data_to_str(BOARD), newdata)
##    if changes:
##        return changes[len(changes)-1]
##    send += ';'+'-'.join(['/'.join(change) for change in changes])
    # Split up the data by the semicolons (seperates messages),
    # and then split each message by spaces.
    data = [i.split(' ') for i in rcvdData[:-1].split(';')]
    # For each message we recieved,
    for i in data:
        # If the message (re-combined spacing) is the wakeup message,
        if ' '.join(i[1:-1]) == WAKEUPMSG or ' '.join(i[1:]) == WAKEUPMSG:
            # Tell the user we recieved a re-sync message
            print('AI: Re-Sync Message Recieved (Happens every %i secconds).' % round(WAKEUP))
            continue
        # If the message is not a wake up message and the length is not two,
        if len(i) != 2:
            # Tell the user we recieved an invalid message
            print('AI: Invalid Message from Server.')
            print(i)
            continue
        # If it's a valid message, spit the data to who it's from and the message
        f, msg = i
        # Get who it's from properly
        frm = f[1:-1]
        # If the message is from our opponent and it's board data,
        if frm == OPPONENT and msg.startswith('w='):
            # If this is not a duplicate message (would cause de-sync),
            if msg != LASTRCVD:
                # Find the changes from our opponent's new board data and our old
                # board data.
                changes = findChange(board_data_to_str(BOARD), msg)
                # Set our last recieved message to this new message
                LASTRCVD = str(msg)
                # If there are board data changes,
                if changes:
                    # Return the last indexed change
                    return changes[len(changes)-1]
            else:
                # If this is a duplicate message, find the changes between
                # the current board data and the last recieved message
                changes = findChange(board_data_to_str(BOARD), LASTRCVD)
                # If there were changes,
                if changes:
                    # Instead of returning the last one, return a random one.
                    # (hopefully re-sync?)
                    return choice(changes)
        elif frm == 'S':# If the message is from the server,
            # If the message is our set re-sync message,
            if msg == WAKEUPMSG:
                # Prepare to send our opponent board data
                send = '['+OPPONENT+'] '+board_data_to_str(boardData, True)
                # Send our message to the server
                S.sendall(send.encode('utf-8'))
    return None

def turnSuccess(tf):
    """This function is called immidiately after the ai's play is made, telling it if it was successfull or not"""
    if not tf:
        print('AI: Something went wrong playing move...')

def stop():
    """This function is called immidiately after the game's window is closed"""
    disconnectFromServer()

def init():
    """This function is called immidiately after the game imports the AI"""
    # We dunno what the board looks like, so set it to blank.
    global PLAYERS
    global BOARD
    global TIDSHIFT
    global S
    global HOST
    global PORT
    global CID
    global CLIENTS
    global OPPONENT
    global LASTSENT
    global LASTRCVD
    # Version 0.0.3 added ability to send a bit of data to board on init
    send = {}
    # Set board data to an empty board
    BOARD = dict(emptyBoardData)
    # We have not sent or recieved anything yet
    LASTSENT = None
    LASTRCVD = None
    # Generate board flip tile id translation table
    nermal = []
    modded = []
    for y in range(8):
        for x in range(8):
            # Generate normal tile ids (nermal da cat lul)
            nermal.append(chr(65 + x)+str(8-y))
            # Generate shifted tile ids
            modded.append(chr(65 + (7-x))+str(y+1))
    # Combine the two in a dictionary
    TIDSHIFT = {nermal[i]:modded[i] for i in range(64)}
    # Initalize the socket we'll be using to send and recive data
    S = socket.socket()
    # Setup the timeout time to none so it doesn't time out
    S.settimeout(None)
    # While a connection has not been established,
    success = False
    while not success:
        # While the HOST value is None,
        while HOST is None:
            # Start a loop of trying to get the user to tell us the IP address
            while True:
                # Ask the user for the server IP Address
                print('AI: Please enter the IP Address of the Hacky Checkers Server.')
                ip = input('IP : ')
                # If the entered data os not text, and there are 3 periods,
                # and everything is correct, break out of the loop
                if not (ip.isalpha() or ip.isspace()):#If it's not text
                    if '.' in ip and ip.count('.') == 3:# If there are 3 periods in text
                        if [i.isnumeric() for i in ip.split('.')] == [True]*4:# If each thing seperated by periods is a number,
                            break
                print('AI: Please enter a valid IP Address.\n', file=os.sys.stderr)
            # Set the host the valid IP address we just got
            HOST = str(ip)
        # Connect the socket to the host at the game port
        print('AI: Attempting connection to %s:%i' % (HOST, PORT))
        connErrCode = S.connect_ex((HOST, PORT))
        # If there was an error,
        success = not connErrCode
        if connErrCode:
            # Tell the user about the error and ask if they want to try a different host
            print('AI: Error: '+os.strerror(connErrCode), file=os.sys.stderr)
            if input('AI: Reset IP Address? (y/n) : ').lower() in ('y', 'yes'):
                HOST = None
        else:
            print('AI: Connection Established!')
    # Once we're connected to the server, wait for the confermation message
    print('AI: Waiting for confermation message from server (happens once two clients join)...')
    rcvdData = S.recv(BUFSIZE).decode()
    print('AI: Recieved confermation message from server.')
    # Get our Client ID from the server's message
    CID = rcvdData.split(';')[0].split(' ')[1][1:-1]
    # Get the IDs of all connected clients from the server's message
    CLIENTS = rcvdData.split(';')[0].split(' ')[3][1:-1].split('/')
    # Get our opponent's id
    OPPONENT = CLIENTS[(CLIENTS.index(CID) + 1) % len(CLIENTS)]
    # Send the server a message that we wish to be woken up every <WAKEUP> secconds
    S.sendall(('[S] Wakeup %s %s' % (str(round(WAKEUP)), WAKEUPMSG)).encode('utf-8'))
    # If we are going to be the first client active,
    if int(CID) != 0:
        # Tell the user we are waiting for our opponent to make a move
        print('AI: Waiting for opponent to make a move. (A black screen/freezing is normal)')
        # Send the resync message to ourselves so at least the screen isn't black
        S.sendall(('[%s] %s' % (CID, WAKEUPMSG)).encode('utf-8'))
    else:
        # Otherwise, tell them the screen might freeze during the opponent's turn
        print('AI: Important: When it is the opponent\'s turn, the screen may freeze or go to black.')
    # Set our socket's timeout time to be five secconds after we're supposed
    # to get our wakeup message, so if the server dies without us knowing,
    # the socket disconnects and nothing breaks
    S.settimeout(round(WAKEUP)+5)
    # Tell the game what the player names should be
    send['player_names'] = ['Player '+cid for cid in CLIENTS]
    # Tell the game the starting turn
    send['starting_turn'] = OPPONENT
    # Tell the game it has to quit on a win
    send['must_quit'] = True
    return send

print('AI: NOT AI Module Loaded')
print('AI: '+NAME+' Created by '+AUTHOR)
