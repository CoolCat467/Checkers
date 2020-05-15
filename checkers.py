#!/usr/bin/env python3
# Graphical Checkers Game with AI support
# Programmed by CoolCat467

# For AI Support, the python file has to have the text
# 'AI' in it somewhere, and has to have the '.py' extention.
# The game calls update(boardData) and tells the AI about
# the current state of the game board from gameboard.getData(),
# turn() to get the target piece tile id and target destination
# tile id from the AI to make a move, and calls init() after the
# AI is imported for it to initalize anything.

# Please send your finnished version of your AI to CoolCat467 at Github
# for review and testing and obain permission to change the REGISTERED
# flag to True, but it doesn't really do much anyways.

# IMPORTANT NOTE:
# The updating and turn calls halt execution, including display
# updates. This would be fixed with multiprocessing, but I am not
# very familiar with it and it also might cause some dy-syncronization
# problems.

# Note: Tile Ids are chess board tile names, A1 to H8
# A8 ... H8
# .........
# A1 ... H1

from math import sqrt
from pygame.locals import *
import pygame

from random import randint
import os
from shutil import copyfile

from base2d import *

NAME = 'Checkers'
__version__ = '0.0.1'

SCREENSIZE = (640, 480)

PICPATH = 'pic/'
##SNDPATH = 'sound/'

FPS = 60

def showHitboxes(world):
    """Make all entities show their hitbox (DEBUG COMMAND)"""
    # For each entity in the world,
    for entity in iter(world.entities.values()):
        # Tell the entity to show it's hitbox
        entity.showhitbox = True

def blit_text(fontname, fontsize, text, color, xy, dest, middle=True):
    """Blit rendered text to dest with the font at fontsize colored color at x, y"""
    # Get a surface of the rendered text
    surf = render_text(fontname, fontsize, text, color)
    # If rendering in the middle of the text,
    if middle:
        # Modify the xy choordinates to be in the middle
        w, h = surf.get_size()
        xy = [xy[0]-w/2, xy[1]-h/2]
    # Blit the text surface to the destination surface at the xy position
    dest.blit(surf, toint(xy))

def render_text(fontname, fontsize, text, color):
    """Render text with a given font at fontsize with the text in the color of color"""
    # Load the font at the size of fontsize
    font = pygame.font.Font(fontname, fontsize)
    # Using the loaded font, render the text in the color of color
    surf = font.render(str(text), False, color)
    return surf

class World(WorldBase):
    """This is the world. All entities are stored here."""
    def __init__(self, background):
        WorldBase.__init__(self)
        self.background = background.convert()
    
##    def process(self, gamestate, time_passed):
##        """Processes all entities in the world"""
##        
##        # For each entity, if it has the activegamestate attribute, make shure it matches the current game state 
##        time_passed_secconds = time_passed / 1000
##        for entity in list(self.entities.values()):
##            if hasattr(entity, 'activegamestate'):
##                if gamestate != entity.activegamestate:
##                    continue
##            entity.process(time_passed_secconds)
##    
    def render(self, surface):
        """Draw the background and render all entities"""
        # Prepare surface for additions
        surface.unlock()
        
        # Put the background on the display, covering everything
        surface.blit(self.background, (0, 0))
        
        renderList = {}
        renderVal = 0
        # For every entity we know about,
        for entity in self.entities.values():
            # If it has the 'renderpriority' attribute,
            if hasattr(entity, 'renderpriority'):
                # add it to the render list at the spot it want to be in
                renderList[entity.renderpriority] = entity
            else:
                # Otherwise, add it to the next avalable spot.
                renderList[renderVal] = entity
                renderVal += 1
        
        # For each render value in order from lowest to greatest,
        for renderVal in sorted(renderList.keys()):
            # Render the entity of that value
            renderList[renderVal].render(surface)
        
        # Modifications to the surface are done, so re-lock it
        surface.lock()
    pass

class Cursor(GameEntity):
    """This is the Cursor! It follows the mouse cursor!"""
    def __init__(self, world, **kwargs):
        GameEntity.__init__(self, world, 'cursor', None, **kwargs)
        
        # Create instances of each brain state
        follow_state = CursorStateFollowing(self)
        
        # Add states to brain
        self.brain.add_state(follow_state)
        
        # Set brain to the following state
        self.brain.set_state('following')
        
        # We are not carrying anything
        self.carryimage = None
        self.carrytile = None
        
        # We should be on top of everything
        self.renderpriority = 100
    
    def render(self, surface):
        """Render Carry Image if carrying anything"""
        # If we're carrying something,
        if self.isCarry():
            # Do stuff so it renders the image's middle to our location
            x, y = self.location
            w, h = self.carryimage.get_size()
            x -= w/2
            y -= h/2
            surface.blit(self.carryimage, (x, y))
    
    def getPressed(self):
        """Return True if the right mouse button is pressed"""
        return bool(pygame.mouse.get_pressed()[0])
    
    def carry(self, image):
        """Set the image we should be carrying to image"""
        self.carryimage = image
    
    def isCarry(self):
        """Return True if we are carrying something"""
        return not self.carryimage is None
    
    def drag(self, tile, image):
        """Grab the piece from a tile and carry it"""
        self.carrytile = tile
        self.carry(image)
    
    def drop(self, targetTile):
        """Drop the image we're carrying"""
        if not self.carrytile is None:
##            if not self.carrytile.board.tiles[targetTile].selected:
##                return
            # Get the tile who's piece we're carrying and tell the tile to move the piece to the target tile
            moves = getMoves(self.carrytile.board, self.carrytile.piece, self.carrytile)
            if targetTile in moves:
                self.carrytile.move_piece(targetTile)
                # After the tile has moved the piece, we shouldn't be carrying it anymore (lol)
                self.carryimage = None
            else:
                self.carrytile.board.tiles[targetTile].selected = False
        else:
            #targetTile.selected = False
            raise RuntimeError('Cannot drop an image to a target tile if not carrying an image!')
    pass

class CursorStateFollowing(State):
    """Cursor's main state, where it teleports to the mouse location"""
    def __init__(self, cursor):
        # Set up self as a state, with the name of 'following'
        State.__init__(self, 'following')
        # Store the cursor entity we're doing brain stuff for
        self.cursor = cursor
    
    def do_actions(self):
        """Move the cursor entity to the xy location of the mouse pointer"""
        self.cursor.location = Vector2(*pygame.mouse.get_pos())
        # also set destination to mouse pointer location in case anything wants to know where we're going
        self.cursor.destination = self.cursor.location
    pass

def getSides(xy):
    """Returns the tile xy choordinates on the top left, top right, bottom left, and bottom right sides of given xy choordinates"""
    # Convert xy coords tuple to a list of strings, and join the strings to a stringed number, convert that to an int, and add ten because of zero positions
    atnum = int(''.join(tostr(xy)))+10
    # Get the xy choords plus 1 on x for top left, top right, bottom left, bottom right
    nums = [atnum-11, atnum+9, atnum-9, atnum+11]
    # If any errored choordinates exist, delete them
    for i in range(len(nums)-1, -1, -1):
        if nums[i] < 10:
            nums[i] = '0'+str(abs(nums[i]))
    # Make the numbers back into usable xy choordinates by splitting each number into two seperate digits, taking the x minus one to fix the zero thing, and return a list of tuples
    return [toint([int(i[0])-1, i[1]]) for i in tostr(nums)]

def rmErrorXyNums(xynums):
    """Remove any string xy choordinate numbers less than ten"""
    # If any errored choordinates exist, delete them
    for i in range(len(xynums)-1, -1, -1):
        if xynums[i] < 10:
            del xynums[i]
    return xynums

def rmErrorXyChoords(xys):
    """Converts coords to string xy choordinate numbers and removes numbers less than ten and ''"""
    valid = []
    for xy in xys:
        if xy == '' or (int(''.join(tostr(xy)))+10) < 10:
            continue
        valid.append(xy)
    return valid

def rmFromList(lst, thing=''):
    """Removes all values matching thing from a list"""
    lst = list(lst)
    for i in range(len(lst)-1, -1, -1):
        if lst[i] == thing:
            del lst[i]
    return lst

def getTileFromCoords(coords, gameboard, replace=''):
    """Ask the gameboard for the tiles at the xy choords given and replaces None with ''"""
    tile = gameboard.getTile('xy', tuple(coords))
    if tile is None:
        tile = replace
    return tile

def getTilesFromCoords(choords, gameboard, replace=''):
    """Returns a list of tiles from the target gameboard based on xy coords and replaces blanks with ''"""
    tiles = gameboard.getTiles('xy', choords)
    for tile in tiles:
        if tile is None:
            tile = replace
    return tiles

def pawnModify(lst, pieceid):
    """Modifies a list based on piece id to take out invalid moves for pawns"""
    assert len(lst) == 4, 'List size MUST be four for this to return valid results!'
    if pieceid == 0:# If it's a white pawn, it can only move to top left and top right
        lst = lst[:2]
    if pieceid == 1:# If it's a black pawn, it can only move to bottom left anf bottom right
        lst = lst[2:]
    return lst

def getJumps(gameboard, pieceid, tile, _rec=0):
    """Gets valid jumps a piece can make"""
    # If the tile is None or the pieceid is invalid, return nothing for jumps.
    if tile is None or not pieceid in [i for i in range(4)]:
        return [], {}
    
    # If we are kinged, get a pawn version of ourselves.
    # Take that plus one mod 2 to get the pawn of the enemy
    enemyPawn = ((pieceid % 2) + 1) % 2
    # Then get the pawn and the king in a list so we can see if a piece is our enemy
    enemyPieces = [enemyPawn, enemyPawn+2]
    
    # Get the side choordinates of the tile and make them tuples so the scan later works properly.
    sideCoords = [tuple(i) for i in getSides(tile.xy)]
    # Make a dictionary to find what direction a tile is in if you give it the tile.
    sideTileDict = {gameboard.getTile('xy', sideCoords[i]):i for i in range(4)}
    
    # Make a dictionary for the valid jumps and the pieces they jump
    valid = {}
    # Make a list for the end tiles after valid jumps
    sideDirTiles = []
    
    # For each side tile in the jumpable tiles for this type of piece,
    for sideTile in gameboard.getTiles('xy', pawnModify(sideCoords, pieceid)):
        # If the tile doesn't exist/error, go on to the next tile
        if sideTile is None or sideTile == '':
            continue
        # Get the direction from the dictionary we made earlier
        direction = sideTileDict[sideTile]
        # If the tile's piece is one of the enemy pieces,
        if sideTile.piece in enemyPieces:
            # Get the coordiates of the tile on the side of the main tile's side in the same direction as the main tile's side
            sideDirSideCoord = tuple(getSides(sideTile.xy)[direction])
            # Get the tile from the game board by the main side's side coordinates
            sideDirSide = gameboard.getTile('xy', sideDirSideCoord)
            # If the side exists and it's open,
            if (not sideDirSide is None) and sideDirSide.isOpen():
                # Add it the valid jumps dictionary and add the tile to the list of end tiles.
                valid[sideDirSide.id] = [sideTile.id]
                sideDirTiles.append(sideDirSide)
    
    # If there are vaid end point tiles,
    if len(sideDirTiles):
        # For each end point tile in the list of end point tiles,
        for endTile in sideDirTiles:
            # Get the dictionary from the jumps you could make from that end tile
            w, h = gameboard.boardsize
            if _rec+1 > round(sqrt(sqrt(w**2 + h**2))):
                break
            _, addvalid = getJumps(gameboard, pieceid, endTile, _rec=_rec+1)
            # For each key in the new dictionary of valid tile's keys,
            for newKey in addvalid.keys():
                # If the key is not already existant in the list of valid destinations,
                if not newKey in valid.keys():
                    # Add that destination to the dictionary and every tile you have to jump to get there.
                    valid[newKey] = valid[endTile.id] + addvalid[newKey]
    
    return list(valid.keys()), valid

def getMoves(gameboard, pieceid, tile, mustopen=True):
    """Gets valid moves a piece can make"""
    # Get the side xy choords of the tile's xy pos, then modify results for pawns
    choords = [tuple(i) for i in pawnModify(getSides(tile.xy), pieceid)]
    moves = []
    tiles = gameboard.getTiles('xy', choords)
    
    if len(choords) >= 1:
        if mustopen:
            for i in range(len(tiles)-1, -1, -1):
                if not tiles[i] is None and not tiles[i] == '' and tiles[i].isOpen():
                    continue
                del tiles[i]
        moves = [tile.id for tile in tiles]
    # Add in valid moves from jumping
    jumps = []
    if not pieceid is None:
        jumps, _ = getJumps(gameboard, pieceid, tile)
    for jump in jumps:
        if not jump in moves:
            moves.append(jump)
    return tuple(moves)

def checkForWins(gameboard):
    """Checks a gameboard for wins, returns the player number if there is one, otherwise return None"""
    # As far as we know, no one has won the game.
    winner = None
    # Get all the tiles pieces can be on, in this case black tiles
    tiles = gameboard.getTiles('color', [0])
    # Set up piece count and number of plays count for each player
    count = [0]*2
    plays = [0]*2
    # For each of the two players,
    for player in range(2):
        # Get that player's possible pieces
        playerPieces = [player, player+2]
        # For each tile in the playable tiles,
        for tile in tiles:
            # If the tile's piece is one of the player's pieces,
            if tile.piece in playerPieces:
                # Increment number of pieces for that player by one
                count[player] += 1
    # If a player has no pieces,
    if 0 in count:
        # The other player wins
        winner = (count.index(0) + 1) % 2
    else:
        # Otherwise, find out if either of the players can't move.
        # For each of the two players,
        for player in range(2):
            # Get that player's possible pieces
            playerPieces = [player, player+2]
            # For each tile in the playable tiles,
            for tile in tiles:
                # If the tile's piece is one of the player's pieces,
                if tile.piece in playerPieces:
                    # Add the number of moves that piece can make to the number of possible plays
                    plays[player] += len(getMoves(gameboard, tile.piece, tile))
        # If a player has no plays,
        if 0 in plays:
            # The other player wins.
            winner = (plays.index(0) + 1) % 2
    # Return the player that won, or None
    return winner

class Tile(object):
    """Object for storing data about tiles"""
    def __init__(self, board, tile_id, location, color, xy):
        # Store data about the game board, what tile id we are, where we live, what color we are, xy positions, basic stuff.
        self.board = board
        self.id = tile_id
        self.location = Vector2(*location)
        self.color = color
        self.xy = xy
        # We shouldn't have any pieces on us
        self.piece = None
        # Get the width and height of self
        wh = [self.board.tilesize]*2
        # Get our location x and y, width, and height for collison later
        self.xywh = (self.location[0], self.location[1], wh[0], wh[1])
        # Set up how long untill we can be clicked again
        self.clickDelay = 0.1
        # We are not clicked
        self.clickTime = 0
        # We are not selected
        self.selected = False
        # We are not glowing
        self.glowing = False
    
    def __repr__(self):
        return '<Tile %s %s %i %s>' % (self.id, str(self.location), self.color, str(self.xy))
    
    def getData(self):
        """Returns a dictionary of important data that is safe to send to an AI"""
        # Set up the dictionary we're going to send
        send = {}
        # Send if this tile is open
        send['open'] = bool(self.piece is None)
        # Send this tile's piece
        send['piece'] = str(self.piece)
        # If we're an open tile,
        if self.isOpen():
            # We have no jumps or moves to send
            send['moves'] = []
            send['jumps'] = [[], {}]
        else:
            # Otherwise, send the jumps and moves our piece can make
            send['moves'] = list(getMoves(self.board, self.piece, self))
            send['jumps'] = list(getJumps(self.board, self.piece, self))
        # Send our xy position
        send['xy'] = tuple(self.xy)
        # Send our color value
        send['color'] = int(self.color)
##        send['id'] = str(self.id)
        # No telling id required, board's dictionary has our id as the key.
        # Send the dictionary
        return send
    
    def getCursor(self):
        """Gets the cursor from the world and returns it"""
        # Tell the world to find an entity with the name of 'cursor'
        cursor = self.board.world.get_type('cursor')
        # If the world found anything and there is at least one cursor entity,
        if (not cursor is None) and len(cursor):
            # Set what we should return to the first (and in regular cases the only) cursor entity
            cursor = cursor[0]
        # Return None if the world didn't find any matches, and return the first cursor entity if the world did find anything
        return cursor
    
    def getPressed(self):
        """Return True if the cursor is over tile and right click down"""
        # Get the cursor
        cursor = self.getCursor()
        # If the cursor exists,
        if not cursor is None:
            # See if the right mouse button is down
            if cursor.getPressed():
                # If it is, see if the cursor is over our image
                point_x, point_y = self.board.convertLoc(cursor.location)
                x, y, w, h = self.xywh
                
                in_x = point_x >= x and point_x < x + w
                in_y = point_y >= y and point_y < y + h
                # If it is, this will return True
                return in_x and in_y
        # Otherwise, return False
        return False
    
    def isOpen(self):
        """Return True if tile is empty"""
        return self.piece is None
    
    def setGlowingTiles(self, truefalse):
        """Sets the glowing state of tiles our piece can move to"""
        # Get the tiles our piece can move to
        tileids = getMoves(self.board, self.piece, self, mustopen=truefalse)
        # Get the tiles
        tiles = [self.board.tiles[tid] for tid in tileids]
        # Make the tiles that our piece can move to glow
        for tile in tiles:
            tile.glowing = bool(truefalse)
    
    def process(self, time_passed):
        """Do stuff like tell the cursor to carry pieces and drop them and click time and crazyness"""
        # Get the cursor
        cursor = self.getCursor()
        if (self.piece is None) or (self.piece in ((1, 3), (0, 2), ())[self.board.playing]):
            # If we are selected and haven't been clicked recently,
            if self.getPressed() and not self.clickTime:
                # Toggle selected
                self.selected = not self.selected
                # If the cursor exists,
                if not cursor is None:
                    # If we are now selected
                    if self.selected:
                        # If we have a piece on us
                        if not self.isOpen():
                            # If the cursor is not carrying a piece,
                            if not cursor.isCarry():
                                # Tell the cursor to carry our piece
                                cursor.drag(self, self.board.pieceMap[self.piece])
                                self.setGlowingTiles(True)
                            else:
                                # Otherwise, we shouldn't be selected
                                self.selected = False
                        else:
                            # If we don't have a piece on us
                            if not self.color:
                                # If we are a black tile, tell the cursor to drop the piece it's carrying onto us
                                if cursor.isCarry():
                                    cursor.drop(self.id)
                                else:
                                    self.selected = False
                            else:
                                # If we are a red tile, we shouldn't be selected.
                                self.selected = False
                    else:# If we are now not selected,
                        # If the cursor is carrying our piece and we've been un-selected, tell the cursor to give our piece back.
                        if cursor.isCarry() and cursor.carrytile.id == self.id:
                            cursor.carryimage = None
                            cursor.carrytile = None
                        # Get the tiles our piece could have moved to
                        tileids = getMoves(self.board, self.piece, self, mustopen=False)
                        # Get the tiles
                        tiles = [self.board.tiles[tid] for tid in tileids]
                        # Make the tiles that our piece could have moved to not glow anymore
                        for tile in tiles:
                            tile.glowing = False
            else:
                # If we have been clicked recently, decement the time variable that tells us we were clicked recently
                self.clickTime = max(self.clickTime-time_passed, 0)
            if self.getPressed():
                # If we have been clicked just now, reset the time variable that tells us we've been clicked recently
                self.clickTime = self.clickDelay
    
    def isSelected(self):
        """Return True if we are selected"""
        return self.selected
    
    def isGlowing(self):
        """Return True if we are glowing"""
        return self.glowing
    
    def play(self, pieceid):
        """If tile is empty, set piece to piece id"""
        # If we have no pieces on us,
        if self.isOpen():
            # If the piece has made it to the opposite side,
            if (pieceid == 0 and self.id[1] == '8') or (pieceid == 1 and self.id[1] == '1'):
                # King that piece
                pieceid += 2
            # Put the piece on us
            self.piece = pieceid
    
    def clear(self):
        """Clear tile of any pieces"""
        # Delete any pieces that are on us.
        self.piece = None
    
    def move_piece(self, tolocid):
        """Return true if successfully moved piece from self to target tile"""
        # Get the target tile from the game board
        target = self.board.tiles[tolocid]
        # If the target tile has no piece on it and it's a valid move,
        if target.isOpen() and tolocid in getMoves(self.board, self.piece, self):
            # Set the tiles the tile set to glowing back to false
            self.setGlowingTiles(False)
            # Get the moves that are jumps and the dictionary that has jumped piece tile ids in it
            jumpmoves, jumped = getJumps(self.board, self.piece, self)
            # If the destination is a jump,
            if tolocid in jumpmoves:
                # For each tile with a piece that got jumped in it,
                for tileid in jumped[tolocid]:
                    # Get the tile from the gameboard and clear it.
                    self.board.tiles[tileid].clear()
            # Play our piece onto target tile
            target.play(self.piece)
            # We just played our piece to the target tile, we shouldn't have it anymore
            self.clear()
            # Niether of us are selected, we just made a play
            self.selected = False
            target.selected = False
            # Also set the target's glowing value to false if it was glowing
            target.glowing = False
            # Toggle the playing value to the next player's turn
            self.board.playing = (self.board.playing + 1) % 2
    pass

class GameBoard(GameEntity):
    """Entity that stores data about the game board and renders it"""
    def __init__(self, world, boardsize, tilesize, **kwargs):
        # Make a blank surface of the proper size by multiplying the board size by the tile size
        image = pygame.Surface(toint(amol(toflt(boardsize), m=float(tilesize))))
        # Fill the blank surface with green so we know if anything is broken/not updating
        image.fill(GREEN)
        GameEntity.__init__(self, world, 'board', image, **kwargs)
        
        # Define Tile Color Map and Piece Map
        self.tileColorMap = [BLACK, RED]
        red = (160, 0, 0)
        black = [40]*3# Define Black Pawn color to be more of a dark grey so you can see it
        # Define each piece by giving what color it should be and an image to recolor
        self.pieceMap = [[red, 'Pawn'], [black, 'Pawn'], [red, 'King'], [black, 'King']]
        
        # Store the Board Size and Tile Size
        self.boardsize = toint(boardsize)
        self.tilesize = int(tilesize)
        
        # Convert Tile Color Map and Piece Map into Dictionarys
        self.tileColorMap = {i:self.tileColorMap[i] for i in range(len(self.tileColorMap))}
        self.pieceMap = {i:self.pieceMap[i] for i in range(len(self.pieceMap))}
        
        # Generate Tile Surfaces for each color of tile stored in the Tile Color Map Dictionary
        self.tile_surfs = {color_id:self.genTileSurf(self.tileColorMap[color_id], [self.tilesize]*2) for color_id in self.tileColorMap.keys()}
        
        # Generate a Pice Surface for each piece using a base image and a color
        self.pieceMap = {i:replaceWithColor(pygame.transform.scale(IMAGES[self.pieceMap[i][1]], [tilesize]*2), self.pieceMap[i][0]) for i in range(len(self.pieceMap))}
        
        # Generate tile data
        self.genTiles()
        
        # Set playing side
        self.playing = randint(0, 1)
        
        # No one has won.
        self.won = None

    def render(self, surface):
        """Generates the board surface and blits it to surface"""
        # Generate the board surface and store it as self.image
        self.image = self.genBoardSurf()
        # Render self.image in the correct location on the screen
        GameEntity.render(self, surface)
    
    def process(self, time_passed):
        """Processes the game board and each of it's tiles and pieces"""
        # Process the GameEntity part of self, which really doesn't do anything since the board doesn't move
        GameEntity.process(self, time_passed)
        
        # For each tile,
        for tile in iter(self.tiles.values()):
            # Process mouse clicks and stuff
            tile.process(time_passed)
        
        # If no one has won,
        if self.won is None:
            # Check for wins
            win = checkForWins(self)
            # If someone has won,
            if not win is None:
                # Don't let anybody move
                self.playing = 2
                # The winner is the person checkForWins found.
                self.won = win
    
    def getData(self):
        """Returns imporant data that is safe to send to an AI"""
        # Set up the dictionary we're going to send
        send = {}
        # Send the game board size
        send['boardsize'] = tuple(self.boardsize)
        # Send who's won the game
        send['won'] = str(self.won)
        # Send all tile data
        send['tiles'] = {tile.id:tile.getData() for tile in self.tiles.values()}
        # Send the dictionary
        return send
    
    def genTileSurf(self, color, size):
        """Generate the image used for a tile"""
##        surf = pygame.Surface(toint(size))
##        surf.fill(BLACK)
##        inside = roundall(amol(toint(size), m=0.95))
##        inside_surf = pygame.Surface(inside)
##        inside_surf.fill(color)
##        pos = roundall(Vector2(*toint(size)) - Vector2(*inside))
##        surf.blit(inside_surf, pos)
        # Make a blank surface of the size we're given
        surf = pygame.Surface(toint(size))
        # Fill the blank surface with the color given
        surf.fill(color)
        # Return a rectangular (or square if width and height of size are the same) image of the color given
        return surf
    
    def outlineSurf(self, surface, color):
        """Add an outline of a given color to a surface"""
        # Get the size of the surface
        w, h = surface.get_size()
        # Make a blank surface of that size
        surf = pygame.Surface((w, h))
        # Replace all color on the image with yellow and blit it to the blank surface
        surf.blit(replaceWithColor(surface, color), (0, 0))
        # Get 90% of the width and height
        inside = roundall(amol([w, h], m=0.90))
        # Make the surface be 90% of it's size
        inside_surf = pygame.transform.scale(surface, inside)
        # Get the proper position the modified image should be at
        pos = amol(list(Vector2(w, h) - Vector2(*inside)), d=2)
        # Add the modified image to the correct location
        surf.blit(inside_surf, pos)
        # Return image with yellow outline
        return surf
    
    def genTiles(self):
        """Generate data about each tile"""
        # Reset tile data
        self.tiles = {}
        location = Vector2(0, 0)
        # Get where pieces should be placed
        ztoI = round(self.boardsize[1]/3)#White
        ztoII = (self.boardsize[1] - (ztoI*2)) + ztoI#Black
        # For each xy position in the area of where tiles should be,
        for y in range(self.boardsize[1]):
            # Reset the x pos to 0
            location.x = 0
            for x in range(self.boardsize[0]):
                # Get the proper name of the tile we're creating ('A1' to 'H8')
                name = chr(65 + x)+str(self.boardsize[1]-y)
                # Get the color of that spot by adding x and y mod the number of different colors
                color = (x+y)%len(self.tile_surfs.keys())
                # Create the tile
                tile = Tile(self, name, location, color, (x, y))
                # If a piece should be placed on that tile and the tile is not Red,
                if (not color) and ( (y <= ztoI-1) or (y >= ztoII) ):
                    # Set the piece to White Pawn or Black Pawn depending on the current y pos
                    tile.piece = {True:1, False:0}[y <= ztoI]
                # Add the tile to the tiles dictionary with a key of it's name ('A1' to 'H8')
                self.tiles[name] = tile
                # Increment the x counter by tilesize
                location.x += self.tilesize
            # Increment the y counter by tilesize
            location.y += self.tilesize
    
    def getTile(self, by, value):
        """Get a spicific tile by an atribute it has, otherwise return None"""
        by = str(by)
        # For each tile on the game board,
        for tile in self.tiles.values():
            # See if the tile has the attribute we're looking at, and if it does see if it matches value
            if hasattr(tile, by) and getattr(tile, by) == value:
                # If it's a match, return that tile
                return tile
        return None
    
    def getTiles(self, by, values):
        """Gets all tiles whos attribute of by is in value, and if there are no matches return None"""
        by = str(by)
        matches = []
        # For each tile on the game board,
        for tile in self.tiles.values():
            # See if it has the attribute we're looking for, and if it does have it, see if it's a match to the given value.
            if hasattr(tile, by) and getattr(tile, by) in values:
                # If it's a match, add it to matches
                matches.append(tile)
        if matches:
            # Return all tiles that matched our query
            return matches
        return [None]
    
    def genBoardSurf(self):
        """Generate an image of a game board"""
        location = Vector2(0, 0)
        # Get a surface the size of everything
        surf = pygame.Surface(amol(self.boardsize, m=self.tilesize))
        # Fill it with green so we know if anything is broken
        surf.fill(GREEN)
        # For each tile xy choordinate,
        for y in range(self.boardsize[1]):
            for x in range(self.boardsize[0]):
                # Get the correct tile at that position
                tile = self.tiles[chr(65 + x)+str(self.boardsize[1]-y)]
                # Get the color id of the tile, and get the tile surface that corrolates to that id
                tileimage = self.tile_surfs[tile.color]
                # If the tile has no piece on it and it's selected,
                if tile.piece is None and tile.isSelected():
                    # Make the tile have a yellow outline to indicate it's selected
                    tileimage = self.outlineSurf(tileimage, YELLOW)
                if tile.isGlowing():
                    # Make the tile glow blue
                    tileimage = self.outlineSurf(tileimage, BLUE)
                # Blit the tile image to the surface at the tile's location
                surf.blit(tileimage, tile.location)
                # If the tile does have a piece on it,
                if not tile.piece is None:
                    # Get the piece surface that corrolates to that piece id
                    piece = self.pieceMap[tile.piece]
                    # If the tile is also selected,
                    if tile.isSelected():
                        # Add a yellow outline to the piece to indicate it's selected
                        piece = self.outlineSurf(piece, YELLOW)
                    # Blit the piece to the surface at the tile's location
                    surf.blit(piece, tile.location)
                # Blit the id of the tile at the tile's location
                #value = int(''.join(tostr(tile.xy)))+10
                #blit_text('VeraSerif.ttf', 20, value, GREEN, tile.location, surf, False)
        return surf
    
    def convertLoc(self, location):
        """Converts a screen location to a location on the game board like tiles use"""
        # Get where zero zero would be in tile location data,
        zero = self.location - Vector2(*amol(self.image.get_size(), d=2))
        # and return the given location minus zero zero to get tile location data
        return Vector2(*location) - zero
    pass

def showWin(valdisplay):
    """Called when the value display requests text to render"""
    # Get the board
    boards = world.get_type('board')
    if len(boards):
        board = boards[0]
    else:
        # If the board not exist, nothing to return
        return ''
    # If the game has been won,
    if not board.won is None:
        # Rendered text should be "<Da Winnah player name> Won!"
        return '%s Won!' % PLAYERS[board.won]
    return ''

class ValDisplay(GameEntity):
    """Entity that displays the value of a string returned by calling valuefunction(self)"""
    def __init__(self, world, fontname, fontsize, valuefunction, **kwargs):
        GameEntity.__init__(self, world, 'valdisplay', None, **kwargs)
        # Store the font name, font size, and value function
        self.fontname = str(fontname)
        self.fontsize = int(fontsize)
        self.value = valuefunction
        # By default text is not centered
        self.centered = True
        # By default text is black
        self.color = BLACK
        
        # Read keyword arguments and act on them appropriately.
        if 'centered' in kwargs.keys():
            self.centered = bool(kwargs['centered'])
        if 'color' in kwargs.keys():
            self.color = tuple(kwargs['color'])
        if 'renderPriority' in kwargs.keys():
            self.renderpriority = kwargs['renderPriority']
    
    def render(self, surface):
        """Render text and blit it to surface"""
        blit_text(self.fontname, self.fontsize, str(self.value(self)), self.color, self.location, surface, middle=self.centered)
    pass

class Button(BaseButton):
    """Button that only shows when a player has won the game"""
    def process(self, time_passed):
        """Does regular button processing AND makes it so button only shows when the game has been won"""
        # Do regular button processing
        BaseButton.process(self, time_passed)
        # Get the game board
        boards = world.get_type('board')
        if len(boards):
            board = boards[0]
            # Show if the game has been won
            self.show = not board.won is None
    pass

##def soundEffect(name, priority=0, endevent=None, volume=1):
##    """Play a sound on the SFX channel"""
##    global SFX
##    global SFX_PRIORITY
##    if DO_EFKS and (name in SOUNDS.keys()):
##        if (not SFX.get_busy()) or (SFX_PRIORITY < priority):
##            SFX_PRIORITY = priority
##            if SFX.get_busy():
##                SFX.stop()
####            if SFX.get_busy():
####                SFX.fadeout(0.1)
####            while SFX.get_busy():
####                clock.tick(0.01)
##            if endevent is None:
##                SFX.set_endevent()
##            else:
##                SFX.set_endevent(endevent)
##            sound = pygame.mixer.Sound(SOUNDS[name])
##            sound.set_volume(volume)
##            SFX.play(sound)

def backPressed(button):
    """This function is called when the back buttons is pressed"""
    boards = world.get_type('board')
    # Get the game board from the world
    if len(boards):
        board = boards[0]
        # If the game is won and this button is pressed,
        if not board.won is None:
            # Reset the game board
            board.genTiles()# Reset all tiles to defaults
            board.won = None# No one has won
            board.playing = randint(0, 1)# Player who can play now is random

def genButton(text, size):
    """Generates a button surface by rendering text with size onto the base button image"""
    baseimage = IMAGES['button']
    buttonimage = scale_surf(baseimage, 4)
    xy = amol(buttonimage.get_size(), d=2)
    blit_text('VeraSerif.ttf', size, text, GREEN, xy, buttonimage)
    return buttonimage

def aiPlay(targetTileid, toTileId):
    """Does pretty much everything that tiles and the cursor do to move a piece combined without visuals"""
    boards = world.get_type('board')
    if len(boards):
        board = boards[0]
        targetTile = board.tiles[targetTileid]
        toTile = board.tiles[toTileId]
        if targetTile.piece in (1, 3) and toTile.isOpen():
            if not toTile.color:
                moves = getMoves(board, targetTile.piece, targetTile)
                if toTileId in moves:
                    targetTile.move_piece(toTileId)
                    return True
    return False

def loadAI(name):
    """Copys the module name + '.py' to 'temp.py' and imports it as AI and calls AI.init()"""
    if name in findAis():
        copyfile(name+'.py', 'temp.py')
        global AI
        import temp as AI
        AI.init()

def findAis():
    """Returns the filename without the '.py' extention of any python files with 'AI' in their filename"""
    ais = []
    for filename in os.listdir(os.getcwd()):
        if '.py' in filename and 'AI' in filename:
            ais.append(''.join(filename.split('.py')))
    return ais

def playAi():
    """If there are AI modules, ask the user if they would like to play one and load it if so"""
    ais = findAis()
    if ais:
        print('\nAI Files found in this folder!')
        print('Would you like to play against an AI?')
        inp = input('(y / n) : ').lower()
        if inp in ('y'):
            print('\nList of AIs:')
            for i in range(len(ais)):
                print('%i : %s' % (i+1, ais[i]))
            print('\nWhich AI would you like to play against?')
            inp = input('(Number between 1 and %i) : ' % len(ais))
            if inp.isalnum():
                num = abs(int(inp)-1) % len(ais)
                loadAI(ais[num])
                return True
            else:
                print('Answer is not a number. Starting two player game.')
        else:
            print('Starting two player game.')
    else:
        print('Starting two player game.')
    return False

def run():
    """Main loop of everything"""
    print(NAME+' '+__version__)
    computer = playAi()
    # Set up globals
    global world
    global IMAGES
    global SOUNDS
    global DO_EFKS
    global DO_MUSIC
    global SFX
    global clock
    global PLAYERS
##    # Initialize the 44KHz 16-bit stereo sound 44100 22050 
##    pygame.mixer.pre_init(44100, -16, 2, 4096)
    # Initialize everything else
    pygame.init()
    
    # Set up the screen
    screen = pygame.display.set_mode(SCREENSIZE, 0, 32)
    pygame.display.set_caption(NAME+' '+__version__)
    
    # Set up the FPS clock
    clock = pygame.time.Clock()
    
    # Get the program path, and use it to find the picture path and sound path
    PROGPATH = os.path.split(os.sys.argv[0])[0]
    picpath = os.path.join(PROGPATH, PICPATH)
##    sndpath = os.path.join(PROGPATH, SNDPATH)
    
    # Get all picture and sound filenames
    pics = os.listdir(picpath)
##    snds = os.listdir(sndpath)
    
    # Create a dictionary containing the image surfaces
    IMAGES = {}
    for picname in pics:
        name = picname.split('.png')[0]
        image = pygame.image.load(picpath+picname).convert_alpha()
        IMAGES[name] = scale_surf(image, 0.25)
    
##    # Create a dictionary containing the sound filenames
##    SOUNDS = {}
##    for sndname in snds:
##        name = sndname.split('.wav')[0]
##        data = sndpath+sndname
##        SOUNDS[name] = data
    
    # Remove this from final, but now it is a good way to see everything    
##    print(IMAGES.keys())
##    print(SOUNDS.keys())
    
    # Get any additional images
    background = pygame.Surface(SCREENSIZE)
    background.fill(WHITE)
    
    # Define animations
    backAnim = [genButton('Play Again', 35)]
    
    # Set up the world
    world = World(background)
    
    # Set up players
    if computer:
        PLAYERS = ['Player', 'Computer']
    else:
        PLAYERS = ['Red Player', 'Black Player']
    
    # Get the screen width and height for a lot of things
    w, h = SCREENSIZE
    
    # Add entities
    world.add_entity(Cursor(world))
    world.add_entity(GameBoard(world, [8]*2, 45, location=amol(SCREENSIZE, d=2)))
    world.add_entity(ValDisplay(world, 'VeraSerif.ttf', 60, showWin, location=amol(SCREENSIZE, d=2), color=GREEN, renderPriority=5))
    world.add_entity(Button(world, backAnim, 'cursor', backPressed, states=1, location=Vector2(*amol(SCREENSIZE, d=2))+Vector2(0, 80)))
    
##    # Set up music
##    #pygame.mixer.music.load(SOUNDS['eggs'])
    
##    # Set up the sfx channel
##    SFX = pygame.mixer.Channel(1)
    
##    # Set additional events
##    GAME_PAUSE = USEREVENT + 2
##    GAME_OVER = USEREVENT + 3
##    MUSIC_END = USEREVENT + 1#This event is sent when a music track ends
    
##    # Set music end to actually do the thing
##    pygame.mixer.music.set_endevent(MUSIC_END)
    
    # Set up some important stuff
##    do_render = True
##    DO_MUSIC = True
    RUNNING = True
    
    # While the game is active
    while RUNNING:
        # Event handler
        for event in pygame.event.get():
            if event.type == QUIT:
                RUNNING = False
                computer = False
##            if event.type == KEYDOWN:
##                 if event.key == K_SPACE:
##                    do_render = not do_render
##                    print('Render = '+str(do_render))
##            if event.type == MUSIC_END:
##                # If the music track has ended, restart it
##                if DO_MUSIC:
##                    pygame.mixer.music.rewind()
##                    pygame.mixer.music.play()        
        
        time_passed = clock.tick(FPS)
        
        # Process entities
        world.process(time_passed)
        
##        if do_render:
        # Render the world to the screen
        world.render(screen)
        
        # If we are playing against a computer,
        if computer:
            # Get the game board from the world
            boards = world.get_type('board')
            # If there are game board(s)
            if len(boards):
                # Get the first one
                board = boards[0]
                # If it is the black player's turn it's the AI
                if not board.playing:
##                    target = input()
##                    dest = input()
                    # Send board data to the AI
                    AI.update(board.getData())
                    # Get the target piece id and destination piece id from the AI
                    target, dest = AI.turn()
                    # Play play the target piece id to the destination tile id
                    success = aiPlay(str(target), str(dest))
        
        # Update the display
        pygame.display.update()
    pygame.quit()

if __name__ == '__main__':
    # If we're not imported as a module, run.
    run()
