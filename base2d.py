#!/usr/bin/env python3
# Pygame Sprite Module

"""Two-Dimentional Game Base Module"""

NAME = '2d Game Base Module'
__version__ = '0.0.1'

import pygame
from math import *
from pygame.locals import *
from Vector2 import Vector2
from random import randint

class Base2DError(Exception):
    """Base2D Exceptions"""
    # Base2D Exception class
    def __init__(self, code, description):
        Exception.__init__(self)
        self.code = code
        self.description = description

    def __str__(self):
        return "%s (%s)" % (self.description, self.code)
    
    def __repr__(self):
        return str(self)
    pass

def amol(lst, **kwargs):
    """All Math On List; a=Add, s=Subtract, m=Multiply, d=Divide, p=To the power of"""
    # Math Operator acting appon All values of a List
    data = list(lst)
    rng = range(len(data))
    operators = kwargs.keys()
    if 'a' in operators:#add
        for i in rng:
            data[i] += kwargs['a']
    if 's' in operators:#subtract
        for i in rng:
            data[i] -= kwargs['s']
    if 'm' in operators:#multiply
        for i in rng:
            data[i] *= kwargs['m']
    if 'd' in operators:#divide
        for i in rng:
            data[i] /= kwargs['d']
    if 'p' in operators:#power
        for i in rng:
            data[i] **= kwargs['p']
    return tuple(data)

def partquotes(string, sep="'", offset=1):
    """Splits strings by what is inside matching sep value of string"""
    data = str(string).split(str(sep))[int(offset):]
    tmp = []
    for i in range(len(data)):
        if not i % 2:
            tmp.append(data[i])
    return list(tmp)

def toint(lst):
    """Makes all values of a list into intigers"""
    return [int(i) for i in list(lst)]

def toflt(lst):
    """Makes all values of a list into floats"""
    return [float(i) for i in list(lst)]

def tostr(lst):
    """Makes all values of a list into strings"""
    return [str(i) for i in list(lst)]

def roundall(lst):
    """Rounds all values of a list"""
    return [round(i) for i in list(lst)]

def absall(lst):
    """Makes all values of a list into the absolute value of that number"""
    return [abs(i) for i in list(lst)]

def tochr(lst):
    """Converts every value of a list into a character"""
    return [chr(i) for i in list(lst)]

def heading_to_degrees(heading):
    """Converts a normalized vector (heading) into a mesurement of degrees"""
    x, y = list(heading)
    deg = (-degrees(atan2(y, x))) + 90
    if deg < 0:
        deg += 360
    return deg

def degrees_to_heading(deg):
    """Converts a mesurement of degrees into a normalized vector (heading)"""
    x = radians(deg)
    return Vector2(sin(x), cos(x))

def scale_surf(surface, scalar):
    """Scales surfaces by a scalar"""
    size = surface.get_size()
    return pygame.transform.scale(surface, toint(amol(size, m=float(scalar))))

def scale_surfs(surfaces, scalar):
    """Scales multiple surfaces by a scalar"""
    return [scale_surf(surface, scalar) for surface in surfaces]

def set_surf_size(surface, wh):
    """Sets the size of a surface"""
    return pygame.transform.scale(surface, toint(wh))

def get_surf_len(surface):
    """Get the length of a surface"""
    return sqrt(sum(amol(surface.get_size(), p=2)))

def get_surf_lens(surfaces):
    """Get the lengths of multiple surfaces"""
    return [get_surf_len(surf) for surf in surfaces]

def getColors(surface):
    """Returns a list of all different colors in a surface"""
    surface = surface.copy()
    w, h = surface.get_size()
    colors = []
    for x in range(w):
        for y in range(h):
            color = surface.get_at((x, y))[:3]
            if not color in colors:
                colors.append(color)
    return tuple(colors)

def averageColor(surface):
    """Returns the average RGB value of a surface"""
    sr, sg, sb = [0]*3
    colors = getColors(surface)
    for color in colors:
        r, g, b = color
        sr += r
        sg += g
        sb += b
    return toint(amol([sr, sg, sb], d=len(colors)))

def replaceWithColor(surface, color):
    """Fill all pixels of the surface with color, preserve transparency."""
    surface = surface.copy().convert_alpha()
    w, h = surface.get_size()
    r, g, b = color
    for x in range(w):
        for y in range(h):
            a = surface.get_at((x, y))[3]
            surface.set_at((x, y), pygame.Color(r, g, b, a))
    return surface

def replaceColor(surface, targetcolor, replacecolor):
    """Fill all pixels of the surface of a color with color, preserve transparency."""
    surface = surface.copy().convert_alpha()
    w, h = surface.get_size()
    r, g, b = replacecolor
    for x in range(w):
        for y in range(h):
            data = surface.get_at((x, y))
            if data[:3] == tuple(targetcolor):
                a = data[3]
                surface.set_at((x, y), pygame.Color(r, g, b, a))
    return surface

def get_deltas(number, lst):
    """Returns a list of the change from a number each value of a list is"""
    return [abs(i - number) for i in lst]

def closest(number, lst):
    """Returns the closest value of lst a number is"""
    delta = get_deltas(number, lst)
    return lst[delta.index(min(delta))]

def farthest(number, lst):
    """Returns the farthest value of lst a number is"""
    delta = get_deltas(number, lst)
    return lst[delta.index(max(delta))]

def bounce(entity, wall):
    """When an entity detects collision, if you also tell it to "bounce", it will bounce off that wall"""
    # VERY MUCH BROKEN PLZ FIX
    vec = Vector2.from_points(entity.location, entity.destination)
    heading = vec.get_normalized()
    tmp = heading.copy()
    heading = -heading
    deg = heading_to_degrees(heading)
    
    if wall.addname in ('top', 'bottom'):
        deg += 90
    
    deg = 180 - deg
    
    if wall.addname in ('top', 'bottom'):
        deg -= 90
    
    if deg < 0:
        deg += 360
    
    heading = degrees_to_heading(deg)
    entity.destination = heading * (vec.get_magnitude() + 100)
    #heading = Vector2.from_points(entity.location, entity.destination).get_normalized()
    entity.location = heading *50
    
##    if self.y < ball_size:
##        deg = -deg
##        y = 2*ball_size - y
##    elif y > DISPLAY_HEIGHT - ball_size:
##        deg = -deg
##        y = 2*(DISPLAY_HEIGHT - ball_size) - y

def wallCollision(entity, wall):
    """Collide with walls and prevent entities from clipping through them"""
    if hasattr(wall, 'side'):
        ecol = entity.get_col_rect()
        wcol = wall.get_col_rect()
        
        x, y = entity.location
        xy = {'x':x, 'y':y}
        val = {'left':'x', 'right':'x', 'top':'y', 'bottom':'y'}
        direct = {'left':ecol.right, 'right':ecol.left, 'top':ecol.bottom, 'bottom':ecol.top}
        base = {'left':0, 'right':wcol.left, 'top':0, 'bottom':wcol.top}
        minus = {'left':ecol.centerx, 'right':ecol.centerx, 'top':ecol.centery, 'bottom':ecol.centery}
        
        xy[val[wall.side]] = base[wall.side] + (direct[wall.side] - minus[wall.side])
        
        entity.location = Vector2(*list(xy.values()))
    else:
        raise Base2DError(0, 'Cannot do wall collision with entities that have no side attribute')

def entityCollision(entity, nonmove):
    """Collide with a non-moveable entity and prevent entities from going through them"""
    # RELATIVE SIDE IS BROKEN, SO THIS IS NOT RELIABLE
    side = entity.relative_side(nonmove)
    if not side is None:
        ecol = entity.get_col_rect()
        wcol = nonmove.get_col_rect()
        
        x, y = entity.location
        xy = {'x':x, 'y':y}
        val = {'left':'x', 'right':'x', 'top':'y', 'bottom':'y'}
        direct = {'left':ecol.right, 'right':ecol.left, 'top':ecol.bottom, 'bottom':ecol.top}
        base = {'left':0, 'right':wcol.left, 'top':0, 'bottom':wcol.top}
        minus = {'left':ecol.centerx, 'right':ecol.centerx, 'top':ecol.centery, 'bottom':ecol.centery}
        
        xy[val[side]] = base[side] + (direct[side] - minus[side])
        
        entity.location = Vector2(*list(xy.values()))
    else:
        raise Base2DError(0, 'Cannot do entity collision with an entity with no relitive side')

class Sprite(object):
    """Old, probrally broken idea for what has now become GameEntity. Do not use."""
    def __init__(self, name, image, position, alpha=True):
        self.name = name
        self.position = position
        self.image = image
        if alpha:
            self.image.convert_alpha()
        else:
            self.image.convert()
    
    def __repr__(self):
        x, y = self.position
        return '<Sprite %s at %i, %i>' % (self.name, x, y)
    
    def render(self, surface):
        # Render at the center of image
        w, h = self.image.get_size()
        x, y = self.position
        x -= w/2
        y -= h/2
        surface.blit(self.image, (x, y))
    
    def collision(self, point):
        # Return True if a point is over image
        point_x, point_y = point
        x, y = self.position
        w, h = self.image.get_size()
        x -= w/2
        y -= h/2
        
        in_x = point_x >= x and point_x < x + w
        in_y = point_y >= y and point_y < y + h
        
        return in_x and in_y
    
    def setheading(self, xy):
        x, y = list(xy)
        heading = Vector2(x, y)
        heading.normalize()
        self.heading = heading
    
    def point_at(self, point):
        surf, xy = self.getdisplay()
        destination = Vector2(dest) - Vector2(surf.get_size())/2
        heading = Vector2.from_points(self.xy(), point)
        self.setheading(heading)
    
    def timemove(self, time_passed_fps_clock):
        tps = int(time_passed_fps_clock) / 1000
        self.move((self.speed * tps))
    
    def move(self, steps):
        pos = Vector2(self.xy())
        self._lastpos = pos
        pos += self.heading * float(steps)
        self.x, self.y = pos
        self._updaterot()
    
    def get_pos(self):
        return self.x, self.y
    
    def collide(self, sprites, action):
        for sprite in sprites:
            if self.collision(sprite):
                action(self, sprite)
    
    def bounceoff(self, sprite, must_be_visible=False):
        do = True
        if must_be_visible:
            do = sprite.visible and self.visible
        if self.collision(sprite) and do:
            test = Vector2.from_points(self.xy(), self._lastpos)
            test.normalize()
            if list(test) == list(self.heading):
                x2, y2 = self.xy()
                x3, y3 = self._lastpos
                x1, y1 = x2, y3
                
                a = sqrt(((x1 - x2)**2)+((y1 - y2)**2))
                b = sqrt(((x1 - x3)**2)+((y1 - y3)**2))
                c = sqrt(((x2 - x3)**2)+((y2 - y3)**2))
                
                try:
                    x = acos( ((b**2) - (a**2) - (c**2)) / (2*a*c) )
                except ZeroDivisionError:
                    pass
                else:
                    y = radians(180 - degrees(x))
                    self.heading = Vector2(cos(y), sin(y))
                    self.speed *= sprite.bouncinesss
    pass

class State(object):
    """Base Class for all StateMachine States"""
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return '<State %s>' % self.name
    
    def __str__(self):
        return '<State %s>' % self.name
    
    def do_actions(self):
        pass
    
    def check_conditions(self):
        pass
    
    def entry_actions(self):
        pass
    
    def exit_actions(self):
        pass
    pass

class StateMachine(object):
    """Brain of all GameEntities"""
    def __init__(self):
        self.states = {} # Stores the states
        self.active_state = None # The currently active state
    
    def __repr__(self):
        return '<StateMachine '+str(self.states)+'>' #', Active : '+self.active_state+'>'
    
    def add_state(self, state):
        """Add a state to the internal dictionary"""
        # Add a state to the internal dictionary
        if not state is None:
            self.states[state.name] = state
        else:
            raise Base2DError(1, 'Cannot add %s to StateMachine' % partquotes(type(None))[0])
    
    def set_state(self, new_state_name):
        """Changes states and preforms any entry / exit actions"""
        # Change states and preform any exit / entry actions
        if not self.active_state is None:
            self.active_state.exit_actions()
        
        #print('changing state %s to %s' % (self.active_state, self.states[new_state_name]))
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()
    
    def think(self):
        """Preform the actions of the active state and change states if there is an active state"""
        #Only continue if there is an active state
        if self.active_state is None:
            return
        
        # Preform the actions of the active state, and check conditions
        self.active_state.do_actions()
        
        new_state_name = self.active_state.check_conditions()
        if not new_state_name is None:
            self.set_state(new_state_name)
    pass

class GameEntity(object):
    """Base Class for all entities"""
    def __init__(self, world, name, image, **kwargs):
        self.world = world
        self.name = name
        self.image = image
        self.base_image = image
        
        self.location = Vector2()
        self.destination = Vector2()
        self.speed = 0
        self.scan = 100
        if not self.image is None:
            self.scan = int(get_surf_len(self.image)/2) + 2
        
        self.showhitbox = False
        self.show = True
        self.doprocess = True
        
        keys = list(kwargs.keys())
        if 'location' in keys:
            self.location = Vector2(*kwargs['location'])
        if 'destination' in keys:
            self.location = Vector2(*kwargs['destination'])
        if 'speed' in keys:
            self.speed = kwargs['speed']
        if 'hitbox' in keys:
            self.showhitbox = bool(kwargs['hitbox'])
        if 'scan' in keys:
            self.scan = int(kwargs['scan'])
        if 'show' in keys:
            self.show = bool(kwargs['show'])
        
        self.brain = StateMachine()
        
        self.id = 0
    
    def __repr__(self):
        return '<%s GameEntity>' % self.name.title()
    
    def __str__(self):
        return self.__repr__
    
    def render(self, surface):
        """Render an entity and it's hitbox if showhitbox is True, and blit it to the surface"""
        x, y = list(self.location)
        try:
            x, y = float(x), float(y)
        except TypeError as e:
            print(x, y)
            print('TypeError in Render!')
            raise TypeError(str(e))
        w, h = self.image.get_size()
        if self.show:
            surface.blit(self.image, (x-w/2, y-h/2))
        if self.showhitbox:
            pygame.draw.rect(surface, [0]*3, self.get_col_rect(), 1)
            if self.scan:
                pygame.draw.circle(surface, [0, 0, 60], toint([x, y]), self.scan, 1)
        
    
    def process(self, time_passed):
        """Process brain and move according to time passed if speed > 0 and not at destination"""
        if self.doprocess:
            self.brain.think()
            
            if self.speed > 0 and self.location != self.destination:
                #vec_to_dest = self.destination - self.location
                #distance_to_dest = vec_to_dest.get_length()
                vec_to_dest = Vector2.from_points(self.location, self.destination)
                distance_to_dest = self.location.get_distance_to(self.destination)
                heading = vec_to_dest.get_normalized()
                # prevent going back and forward really fast once it make it close to destination
                travel_distance = min(distance_to_dest, (time_passed * self.speed))
                self.location += heading * round(travel_distance)
    
    def get_xywh(self):
        """Return x and y position and width and height of self.image for collision"""
        # Return x pos, y pos, width, and height for collision
        x, y = self.location
        w, h = (0, 0)
        if not self.image is None:
            w, h = self.image.get_size()
        x -= w/2
        y -= h/2
        return x, y, w, h
    
    def get_col_rect(self):
        """Return a rect for collision"""
        rect = pygame.rect.Rect(*self.get_xywh())
        return rect
    
    def is_over(self, point):
        """Return True if point is over self.image"""
        # Return True if a point is over image
        point_x, point_y = point
        x, y, w, h = self.get_xywh()
        
        in_x = point_x >= x and point_x < x + w
        in_y = point_y >= y and point_y < y + h
        
        return in_x and in_y
    
    def collision(self, sprite):
        """Return True if a sprite's image is over self.image"""
        # Return True if a sprite's image is over our image
        rs = self.get_col_rect()#rect self
        ro = sprite.get_col_rect()#rect other
        
        return bool(rs.colliderect(ro))
    
    def collide(self, entityname, action):
        """For every entity with the name of entityname, call action(self, entity)"""
        for entity in self.world.get_type(entityname):
            if entity is not None:
                if self.collision(entity):
                    action(self, entity)
    
    def relative_side(self, entity):
        """Return what side of an entity we are on, to be used with collision"""
        # THIS IS VERY BROKEN PLZ FIX
        wall = hasattr(entity, 'side')
        sides = ['top', 'right', 'bottom', 'left']# 45:'top right', 135:'bottom right', 225:'bottom left', 315:'top left'}
        sloc = self.location
        eloc = entity.location
        rect = entity.get_col_rect()
        vec = Vector2.from_points(sloc, eloc)
        if not wall:
            final = [i*90 for i in range(4)]
            first = [i*45 for i in range(8)]
            rsides = [rect.midtop, rect.midright, rect.midbottom, rect.midleft]
            #rsides = [Vector2(x, y) for x, y in rsides]
            #side_deg = [atan2(v.y, v.x) for v in rsides]
            side_deg = [round((heading_to_degrees( Vector2.from_points(entity.location, Vector2(x, y)).get_normalized()) + 360) % 360) for x, y in rsides]
            deg = 360 - round((heading_to_degrees(vec.get_normalized())) % 360)
            if deg <= 45:
                deg = 0
            sdeg = closest(round(deg), side_deg)
            num = side_deg.index(sdeg)
            
            return sides[num]
        elif wall:
            return entity.side
        return None
    pass

class BaseWall(GameEntity):
    """Wall to stop entities from going to invalid places"""
    def __init__(self, world, location, wh, side='left', **kwargs):
        GameEntity.__init__(self, world, 'wall', None, **kwargs)
        self.image = pygame.surface.Surface(toint(wh)).convert()
        self.location = Vector2(*toint(location))
        self.side = side
        self.scan = 0
    
    def render(self, surface):
        """Renders hitbox to screen if self.showhitbox = True, otherwise nothing."""
        self.show = False
        GameEntity.render(self, surface)
    pass

class BaseButton(GameEntity):
    """Base button, if entity self.trigger is over image and mouse down, call self.action(self)"""
    def __init__(self, world, anim, trigger, action, states=0, **kwargs):
        GameEntity.__init__(self, world, 'button', anim[0], **kwargs)
        self.trigger = trigger
        self.action = action
        self.value = 0
        self.maxvalue = int(states)
        self.anim = anim
        self.presstime = 1
        self.lastpress = 0
        self.scan = int(max(get_surf_lens(self.anim)) / 2)+2
        
        keys = list(kwargs.keys())
        if 'time' in keys:
            self.presstime = float(kwargs['time'])
    
    def process(self, time_passed):
        """Call self.action(self) if any self.trigger entity is over self"""
        # Do regular processing
        GameEntity.process(self, time_passed)
        
        # If not recently pressed,
        self.lastpress -= time_passed
        if self.lastpress < 0:
            self.lastpress = 0
        if pygame.mouse.get_pressed()[0] and not self.lastpress:#get_pressed returns (left, middle, right)
            self.lastpress = self.presstime
            # Test if pressed, and if so call self.action(self)
            trigger = self.world.get_closest_entity(self.trigger, self.location, self.scan)
            if trigger is not None:
                if self.is_over(trigger.location):
                    self.value = (self.value + 1) % self.maxvalue
                    self.action(self)
        
        # Update animation
        self.image = self.anim[self.value % len(self.anim)]
    pass

class WorldBase(object):
    """Base class of world objects"""
    def __init__(self):
        self.entities = {} # Store all the entities
        self.entity_id = 0 # Last entity id assigned
            
    def __repr__(self):
        return '<World Object>'
    
    def add_entity(self, entity):
        """Stores the entity then advances the current id"""
        # stores the entity then advances the current id
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1
    
    def add_entities(self, entities):
        """Add multiple entities from a list"""
        for entity in entities:
            self.add_entity(entity)
    
    def remove_entity(self, entity):
        """Remove an entity from the world"""
        del self.entities[entity.id]
    
    def remove_entities(self, entities):
        """Remove multiple entities from a list"""
        for entity in entities:
            self.remove_entity(entity)
    
    def get(self, entity_id):
        """Find an entity, given it's id, and return None if it's not found"""
        # find the entity, given it's id, (or None if it's not found)
        if (not entity_id is None) and (entity_id in self.entities):
            return self.entities[entity_id]
        return None
    
    def get_type(self, entityname):
        """Returns all entities by the name of entityname in the world"""
        matches = []
        for entity in self.entities.values():
            if entity.name == entityname:
                matches.append(entity)
        return matches
    
    def process(self, time_passed):
        """Process every entity stored the world"""
        # process every entity in the world
        time_passed_secconds = time_passed / 1000
        for entity in list(self.entities.values()):
            entity.process(time_passed_secconds)
    
    def render(self, surface):
        """Draw the background and render all entities"""
        # draw the background and all it's entites
        surface.unlock()
        surface.blit(self.background, (0, 0))
        for entity in self.entities.values():
            entity.render(surface)
        surface.lock()
    
    def get_close_entity(self, name, location, rnge=100):
        """Find an entity with name within range of location"""
        # find an entity within range of location
        location = Vector2(*location)
        
        for entity in self.entities.values():
            if entity.name == name:
                distance = location.get_distance_to(entity.location)
                if distance < rnge:
                    return entity
        return None
    
    def get_closest_entity(self, name, location, rnge=100):
        """Find the closest entity with name within range of location"""
        # find the closest entity within range of location
        location = Vector2(*location)
        
        matches = {}
        for entity in self.entities.values():
            if entity.name == name:
                distance = location.get_distance_to(entity.location)
                if distance < rnge:
                    matches[distance] = entity
        
        if matches:
            return matches[min(matches.keys())]
        return None
    pass

BLACK   = (0, 0, 0)
BLUE    = (0, 0, 255)
GREEN   = (0, 255, 0)
CYAN    = (0, 255, 255)
RED     = (255, 0, 0)
MAGENTA = (255, 0, 255)
YELLOW  = (255, 255, 0)
WHITE   = (255, 255, 255)
