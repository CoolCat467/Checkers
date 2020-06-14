#!/usr/bin/env python3
# NOT AI that is really a client for a checkers AI server.

# IMPORTANT NOTE:
# I know this may not be efficiant, but this is a bit of
# a challange I made for myself, in using nothing but
# what is already existant in the checkers game already
# to make a networked game

import os, socket
from random import choice

HOST = None#Given to us by user
PORT = 8673
BUFSIZE = 1040
WAKEUP = 30#60*3.5
WAKEUPMSG = 'Wake up and re-sync you fool!'

NAME = "Socket Checkers Client (Not an AI)"
AUTHOR = 'CoolCat467'
__version__ = '0.0.0'

REGISTERED = True
# Please send your finnished version of your AI to CoolCat467 at Github
# for review and testing and obain permission to change this flag to True

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
    global TIDSHIFT
    w = 'N' if board['won'] == 'None' else board['won']
    data = ['w='+str(w+'-')]
    for tid in board['tiles'].keys():
        if not board['tiles'][tid]['color']:#If it's a playable tile
            if flip:
                data += [TIDSHIFT[tid]+'=']
            else:
                data += [tid+'=']
            p = board['tiles'][tid]['piece']
            p = 'N' if p == 'None' else p
            if flip:
                p = {'0':'1', '1':'0', '2':'3', '3':'2', 'N':'N'}[p]
            data.append(p)
            if not p == 'N':
                m = board['tiles'][tid]['moves']
                if flip:
                    m = [TIDSHIFT[i] for i in m]
                m = 'N' if not len(m) else '/'.join(m)
                data += ['=', m]
            data.append('-')
    return ''.join(data)[:-1]

def str_to_board_info(string):#, flip=False):
    global TIDSHIFT
    data = [i.split('=') for i in string.split('-')]
    rev = [data[0]]
    for i in data[1:]:
        if len(i) == 2:
            tid, p = i
            rev.append([tid, p, 'N'])
        elif len(i) == 3:
            rev.append(i)
    data = rev
##    if flip:
##        fdata = list(data[0])
##        for i in data[1:]:
##            fdata.append([TIDSHIFT[i[0]],
##                          {'0':'1', '1':'0', '2':'3', '3':'2', 'N':'N'}[i[1]],
##                          i[2]])
##        return fdata
    return data

def findChange(old, new):
    global TIDSHIFT
    one = str_to_board_info(old)[1:]#Ignore won information
    two = str_to_board_info(new)[1:]
    two = [i for i in reversed(two)]
    # Get valid moves the old board can make
    moves = [[i[0], i[2]] for i in one if i[2] != 'N']
    moves = sum([[[i[0], f] for f in i[1].split('/')] for i in moves], [])
    # Get all start and end points seperated
    starters = [i[0] for i in moves]
    enders = [i[1] for i in moves]
    # Look at new data starting and ending positions for changes
    twotids = {two[i][0]:i for i in range(len(two))}
    twoends = [i for i in enders if two[twotids[i]][1] != 'N']
    twostarts = [i for i in starters if two[twotids[i]][1] == 'N']
    # Find the proper move that was made
    allmoves = []
    for s in twostarts:
        for e in twoends:
            se = [s, e]#[TIDSHIFT[s], TIDSHIFT[e]]
            if se in moves and not se in allmoves:
                allmoves.append(se)
    return allmoves

def disconnectFromServer():
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
    if not boardData['won'] == 'None':
        print('AI: Game Won!\nDisconnecting from Server...')
        disconnectFromServer()
    if not boardData['boardsize'] == (8, 8):
        raise RuntimeError('Board Size is not 8 x 8, and is not compatable with this AI Module (not an ai lol)')
    print('AI: Transmitting board data...')
##    changes = findChange(board_data_to_str(BOARD), boardData)
##    send += '-'.join(['/'.join(change) for change in changes])
    send = '['+OPPONENT+'] '+board_data_to_str(boardData, True)
##    if not send == LASTSENT:
    try:
        S.sendall(send.encode('utf-8'))
    except OSError:
        print('AI: An error occored when trying to send board data to server.', file=os.sys.stderr)
        disconnectFromServer()
    else:
        LASTSENT = str(send)
        print('AI: Transmission Sent.')
##    else:
##        print('Repeated message; skipping.')
    BOARD = boardData

def turn():
    """This function is called when the game requests the AI to return the piece it wants to move's id and the tile id the target piece should be moved to."""
    global BOARD
    global S
    global OPPONENT
    global LASTRCVD
    global WAKEUPMSG
    print('AI: Awaiting Server for Play Data...')
    try:
        rcvdData = S.recv(BUFSIZE).decode()
    except OSError:
        rcvdData = ''
    else:
        print('AI: Transmission recieved.')
    rcvdData = '' if rcvdData is None else rcvdData
    if 'bye' in sum([i.lower().split(' ') for i in rcvdData.split(';')], []):
        print('AI: Server shutting down. Quitting...', file=os.sys.stderr)
        disconnectFromServer()
        return 'QUIT'
    elif rcvdData == '':
        print('AI: Server died. Quitting...', file=os.sys.stderr)
        disconnectFromServer()
        return 'QUIT'
##    data = rcvdData[:-1].split(';')
##    newdata = data[len(data)-1].split(' ')[1]
##    changes = findChange(board_data_to_str(BOARD), newdata)
##    if changes:
##        return changes[len(changes)-1]
##    send += ';'+'-'.join(['/'.join(change) for change in changes])
    data = [i.split(' ') for i in rcvdData[:-1].split(';')]
    for i in data:
        if ' '.join(i[1:-1]) == WAKEUPMSG or ' '.join(i[1:]) == WAKEUPMSG:
            print('AI: Re-Sync Message Recieved (Happens every %i secconds).' % round(WAKEUP))
            continue
        if len(i) != 2:
            print('AI: Invalid Message from Server.')
            print(i)
            continue
        f, msg = i
        frm = f[1:-1]
        if frm == OPPONENT and msg.startswith('w='):
            if msg != LASTRCVD:
                changes = findChange(board_data_to_str(BOARD), msg)
                LASTRCVD = str(msg)
                if changes:
                    return changes[len(changes)-1]
            else:
                changes = findChange(board_data_to_str(BOARD), LASTRCVD)
                if changes:
                    return choice(changes)
        elif frm == 'S':
            if msg == WAKEUPMSG:
                send = '['+OPPONENT+'] '+board_data_to_str(boardData, True)
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
    BOARD = dict(emptyBoardData)
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
    # Initalize the socket
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
    # Tell the game what the player names should be
    send['player_names'] = ['Player '+cid for cid in CLIENTS]
    # Tell the game the starting turn
    send['starting_turn'] = OPPONENT
    # Tell the game it has to quit on a win
    send['must_quit'] = True
    return send

print('AI: NOT AI Module Loaded')
print('AI: '+NAME+' Created by '+AUTHOR)
