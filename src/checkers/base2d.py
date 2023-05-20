#!/usr/bin/env python3
# Pygame Sprite Module

"Two-Dimentional Game Base Module"

from __future__ import annotations

__title__ = "2d Game Base Module"
__version__ = "0.0.1"

import math
from typing import Any, Callable, Collection, Iterable, TypeVar, cast

import pygame
from pygame.locals import *
from Vector2 import Vector2


class Base2DError(Exception):
    "Base2D Exceptions"
    __slots__ = ("code", "description")

    # Base2D Exception class
    def __init__(self, code: int, description: str) -> None:
        Exception.__init__(self)
        self.code = code
        self.description = description

    def __str__(self) -> str:
        return f"{self.description} ({self.code})"

    def __repr__(self) -> str:
        return str(self)


def amol(
    lst: Iterable[int | float], **kwargs: int | float
) -> tuple[int | float, ...]:
    "All Math On List; a=Add, s=Subtract, m=Multiply, d=Divide, p=To the power of"
    # Math Operator acting appon All values of a List
    data = list(lst)
    rng = range(len(data))
    operators = kwargs.keys()
    if "a" in operators:  # add
        for i in rng:
            data[i] += kwargs["a"]
    if "s" in operators:  # subtract
        for i in rng:
            data[i] -= kwargs["s"]
    if "m" in operators:  # multiply
        for i in rng:
            data[i] *= kwargs["m"]
    if "d" in operators:  # divide
        for i in rng:
            data[i] /= kwargs["d"]
    if "p" in operators:  # power
        for i in rng:
            data[i] **= kwargs["p"]
    return tuple(data)


def part_quotes(text: str, which: int, quotes: str = "'") -> str:
    """Return part which of text within quotes."""
    return text.split(quotes)[which * 2 + 1]


def to_int(lst: Iterable[int | float]) -> list[int]:
    "Makes all values of a list into intigers"
    return [int(i) for i in lst]


def to_flt(lst: Iterable[int | float]) -> list[float]:
    "Makes all values of a list into floats"
    return [float(i) for i in lst]


def to_str(lst: Iterable[int | float]) -> list[str]:
    "Makes all values of a list into strings"
    return [str(i) for i in lst]


def round_all(lst: Iterable[int | float]) -> list[int]:
    "Rounds all values of a list"
    return [round(i) for i in lst]


def abs_all(lst: Iterable[int | float]) -> list[int | float]:
    "Makes all values of a list into the absolute value of that number"
    return [abs(i) for i in lst]


def to_chr(lst: Iterable[int | float]) -> list[str]:
    "Converts every value of a list into a character"
    return [chr(i) for i in lst]


def heading_to_degrees(heading: tuple[int, int] | Vector2) -> float:
    "Converts a normalized vector (heading) into a mesurement of degrees"
    x_pos, y_pos = heading
    deg = (-math.degrees(math.atan2(y_pos, x_pos))) + 90
    if deg < 0:
        deg += 360
    return deg


def degrees_to_heading(deg: float | int) -> Vector2:
    "Converts a mesurement of degrees into a normalized vector (heading)"
    rads = math.radians(deg)
    return Vector2(math.sin(rads), math.cos(rads))


def scale_surf(
    surface: pygame.surface.Surface, scalar: float
) -> pygame.surface.Surface:
    "Scales surfaces by a scalar"
    size = surface.get_size()
    return pygame.transform.scale(surface, to_int(amol(size, m=float(scalar))))


def scale_surfs(
    surfaces: Iterable[pygame.surface.Surface], scalar: float
) -> list[pygame.surface.Surface]:
    "Scales multiple surfaces by a scalar"
    return [scale_surf(surface, scalar) for surface in surfaces]


def set_surf_size(
    surface: pygame.surface.Surface, width_height: tuple[int, int]
) -> pygame.surface.Surface:
    "Sets the size of a surface"
    return pygame.transform.scale(surface, to_int(width_height))


def get_surf_len(surface: pygame.surface.Surface) -> float:
    "Get the length of a surface"
    return math.sqrt(sum(amol(surface.get_size(), p=2)))


def get_surf_lens(surfaces: Iterable[pygame.surface.Surface]) -> list[float]:
    "Get the lengths of multiple surfaces"
    return [get_surf_len(surf) for surf in surfaces]


def get_colors(
    surface: pygame.surface.Surface,
) -> tuple[tuple[int, int, int], ...]:
    "Returns a list of all different colors in a surface"
    surface = surface.copy()
    width, height = surface.get_size()
    colors = []
    for x in range(width):
        for y in range(height):
            color = cast(tuple[int, int, int], surface.get_at((x, y))[:3])
            if not color in colors:
                colors.append(color)
    return tuple(colors)


def average_color(surface: pygame.surface.Surface) -> list[int]:
    "Returns the average RGB value of a surface"
    s_r, s_g, s_b = [0] * 3
    colors = get_colors(surface)
    for color in colors:
        r, g, b = color
        s_r += r
        s_g += g
        s_b += b
    return to_int(amol([s_r, s_g, s_b], d=len(colors)))


def replace_with_color(
    surface: pygame.surface.Surface, color: tuple[int, int, int]
) -> pygame.surface.Surface:
    "Fill all pixels of the surface with color, preserve transparency."
    surface = surface.copy().convert_alpha()
    width, height = surface.get_size()
    r, g, b = color
    for x in range(width):
        for y in range(height):
            a = surface.get_at((x, y))[3]
            surface.set_at((x, y), pygame.Color(r, g, b, a))
    return surface


def replace_color(
    surface: pygame.surface.Surface,
    targetcolor: tuple[int, int, int],
    replace_color: Any,
) -> pygame.surface.Surface:
    "Fill all pixels of the surface of a color with color, preserve transparency."
    surface = surface.copy().convert_alpha()
    w, h = surface.get_size()
    r, g, b = replace_color
    for x in range(w):
        for y in range(h):
            data = surface.get_at((x, y))
            if data[:3] == targetcolor:
                a = data[3]
                surface.set_at((x, y), pygame.Color(r, g, b, a))
    return surface


def get_deltas(
    number: int | float, lst: Iterable[int | float]
) -> list[int | float]:
    "Returns a list of the change from a number each value of a list is"
    return [abs(i - number) for i in lst]


L = TypeVar("L", bound=int | float)


def closest(number: int | float, lst: list[L]) -> L:
    "Returns the closest value of lst a number is"
    delta = get_deltas(number, lst)
    return lst[delta.index(min(delta))]


def farthest(number: int | float, lst: list[L]) -> L:
    "Returns the farthest value of lst a number is"
    delta = get_deltas(number, lst)
    return lst[delta.index(max(delta))]


##def bounce(entity, wall):
##    "When an entity detects collision, if you also tell it to 'bounce', it will bounce off that wall"
##    # VERY MUCH BROKEN PLZ FIX
##    vec = Vector2.from_points(entity.location, entity.destination)
##    heading = vec.get_normalized()
##    # pylint: W0612: Unused variable 'tmp'
##    tmp = heading.copy()
##    heading = -heading
##    deg = heading_to_degrees(heading)
##
##    if wall.addname in ('top', 'bottom'):
##        deg += 90
##
##    deg = 180 - deg
##
##    if wall.addname in ('top', 'bottom'):
##        deg -= 90
##
##    if deg < 0:
##        deg += 360
##
##    heading = degrees_to_heading(deg)
##    entity.destination = heading * (vec.get_magnitude() + 100)
##    #heading = Vector2.from_points(entity.location, entity.destination).get_normalized()
##    entity.location = heading *50
##
####    if self.y < ball_size:
####        deg = -deg
####        y = 2*ball_size - y
####    elif y > DISPLAY_HEIGHT - ball_size:
####        deg = -deg
####        y = 2*(DISPLAY_HEIGHT - ball_size) - y
##
##def wall_collision(entity, wall):
##    "Collide with walls and prevent entities from clipping through them"
##    if hasattr(wall, 'side'):
##        ecol = entity.get_col_rect()
##        wcol = wall.get_col_rect()
##
##        x, y = entity.location
##        xy = {'x':x, 'y':y}
##        val = {'left':'x', 'right':'x', 'top':'y', 'bottom':'y'}
##        direct = {'left':ecol.right, 'right':ecol.left, 'top':ecol.bottom, 'bottom':ecol.top}
##        base = {'left':0, 'right':wcol.left, 'top':0, 'bottom':wcol.top}
##        minus = {'left':ecol.centerx,
##                 'right':ecol.centerx,
##                 'top':ecol.centery,
##                 'bottom':ecol.centery}
##
##        xy[val[wall.side]] = base[wall.side] + (direct[wall.side] - minus[wall.side])
##
##        entity.location = Vector2(*list(xy.values()))
##    else:
##        raise Base2DError(0, 'Cannot do wall collision with entities that have no side attribute')
##
##def entity_collision(entity, nonmove):
##    "Collide with a non-moveable entity and prevent entities from going through them"
##    # RELATIVE SIDE IS BROKEN, SO THIS IS NOT RELIABLE
##    side = entity.relative_side(nonmove)
##    if not side is None:
##        ecol = entity.get_col_rect()
##        wcol = nonmove.get_col_rect()
##
##        # pylint: C0103: Variable name "y" doesn't conform to snake_case naming style
##        # pylint: C0103: Variable name "x" doesn't conform to snake_case naming style
##        x, y = entity.location
##        # pylint: C0103: Variable name "xy" doesn't conform to snake_case naming style
##        xy = {'x':x, 'y':y}
##        val = {'left':'x', 'right':'x', 'top':'y', 'bottom':'y'}
##        direct = {'left':ecol.right, 'right':ecol.left, 'top':ecol.bottom, 'bottom':ecol.top}
##        base = {'left':0, 'right':wcol.left, 'top':0, 'bottom':wcol.top}
##        # pylint: C0301: Line too long (102/100)
##        minus = {'left':ecol.centerx, 'right':ecol.centerx, 'top':ecol.centery, 'bottom':ecol.centery}
##
##        xy[val[side]] = base[side] + (direct[side] - minus[side])
##
##        entity.location = Vector2(*list(xy.values()))
##    else:
##        raise Base2DError(0, 'Cannot do entity collision with an entity with no relitive side')
##
##class Sprite:
##    "Old, probrally broken idea for what has now become GameEntity. Do not use."
##    def __init__(self, name, image, position, alpha=True):
##        self.name = name
##        self.position = position
##        self.image = image
##        self.heading = Vector2(0, 0)
##        if alpha:
##            self.image.convert_alpha()
##        else:
##            self.image.convert()
##
##    def __repr__(self):
##        x, y = self.position
##        return f'<Sprite {self.name} at {x}, {y}>'
##
##    def render(self, surface):
##        "Render sprite"
##        # Render at the center of image
##        w, h = self.image.get_size()
##        x, y = self.position
##        x -= w/2
##        y -= h/2
##        surface.blit(self.image, (x, y))
##
##    def collision(self, point):
##        "Sprite collision"
##        # Return True if a point is over image
##        point_x, point_y = point
##        x, y = self.position
##        w, h = self.image.get_size()
##        x -= w/2
##        y -= h/2
##
##        in_x = point_x >= x and point_x < x + w
##        in_y = point_y >= y and point_y < y + h
##
##        return in_x and in_y
##
##    def setheading(self, xy):
##        "Set heading"
##        x, y = list(xy)
##        heading = Vector2(x, y)
##        heading.normalize()
##        self.heading = heading
##
##    def point_at(self, point):
##        "Point twords point"
##        surf, xy = self.getdisplay()
##        destination = Vector2(dest) - Vector2(surf.get_size())/2
##        heading = Vector2.from_points(self.xy(), point)
##        self.setheading(heading)
##
##    def time_move(self, time_passed_fps_clock):
##        "Move based on time"
##        tps = int(time_passed_fps_clock) / 1000
##        self.move((self.speed * tps))
##
##    def move(self, steps):
##        "Move given number of steps."
##        pos = Vector2(self.xy())
##        self._lastpos = pos
##        pos += self.heading * float(steps)
##        self.x, self.y = pos
##        self._updaterot()
##
##    def get_pos(self):
##        "Return x, y"
##        return self.x, self.y
##
##    def collide(self, sprites, action):
##        "Collide with sprites and preform action on collision"
##        for sprite in sprites:
##            if self.collision(sprite):
##                action(self, sprite)
##
##    def bounceoff(self, sprite, must_be_visible=False):
##        do = True
##        if must_be_visible:
##            do = sprite.visible and self.visible
##        if self.collision(sprite) and do:
##            test = Vector2.from_points(self.xy(), self._lastpos)
##            test.normalize()
##            if list(test) == list(self.heading):
##                x2, y2 = self.xy()
##                x3, y3 = self._lastpos
##                x1, y1 = x2, y3
##
##                a = sqrt(((x1 - x2)**2)+((y1 - y2)**2))
##                b = sqrt(((x1 - x3)**2)+((y1 - y3)**2))
##                c = sqrt(((x2 - x3)**2)+((y2 - y3)**2))
##
##                try:
##                    x = acos( ((b**2) - (a**2) - (c**2)) / (2*a*c) )
##                except ZeroDivisionError:
##                    pass
##                else:
##                    y = radians(180 - degrees(x))
##                    self.heading = Vector2(cos(y), sin(y))
##                    self.speed *= sprite.bouncinesss


class State:
    "Base Class for all StateMachine States"
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"<State {self.name}>"

    def __str__(self) -> str:
        return f"<State {self.name}>"

    def do_actions(self) -> None:
        "Preform actions"
        pass

    def check_conditions(self) -> str | None:
        "Check conditions and return new state if needed"
        return None

    def entry_actions(self) -> None:
        "Called on enter of state"
        pass

    def exit_actions(self) -> None:
        "Called just before state changed to new"
        pass


class StateMachine:
    "Brain of all GameEntities"

    def __init__(self) -> None:
        self.states: dict[str, State] = {}  # Stores the states
        self.active_state: State | None = None  # The currently active state

    def __repr__(self) -> str:
        return f"<StateMachine {self.states}>"
        #', Active : '+self.active_state+'>'

    def add_state(self, state: State) -> None:
        "Add a state to the internal dictionary"
        # Add a state to the internal dictionary
        if state is not None:
            self.states[state.name] = state
        else:
            raise Base2DError(1, f"Cannot add {type(state)} to StateMachine")

    def set_state(self, new_state_name: str) -> None:
        "Changes states and preforms any entry / exit actions"
        # Change states and preform any exit / entry actions
        if self.active_state is not None:
            self.active_state.exit_actions()

        # print(f'changing state {self.active_state} to {self.states[new_state_name]}')
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()

    def think(self) -> None:
        "Preform the actions of the active state and change states if there is an active state"
        # Only continue if there is an active state
        if self.active_state is None:
            return

        # Preform the actions of the active state, and check conditions
        self.active_state.do_actions()

        new_state_name = self.active_state.check_conditions()
        if new_state_name is not None:
            self.set_state(new_state_name)


class GameEntity:
    "Base Class for all entities"

    def __init__(
        self,
        world: "WorldBase",
        name: str,
        image: pygame.surface.Surface,
        **kwargs: Any,
    ) -> None:
        self.world = world
        self.name = name
        self.image = image
        self.base_image = image

        self.location = Vector2()
        self.destination = Vector2()
        self.speed = 0
        self.scan = 100
        if not self.image is None:
            self.scan = int(get_surf_len(self.image) / 2) + 2

        self.show_hitbox = False
        self.show = True
        self.doprocess = True

        keys = list(kwargs.keys())
        if "location" in keys:
            self.location = Vector2(*kwargs["location"])
        if "destination" in keys:
            self.location = Vector2(*kwargs["destination"])
        if "speed" in keys:
            self.speed = kwargs["speed"]
        if "hitbox" in keys:
            self.show_hitbox = bool(kwargs["hitbox"])
        if "scan" in keys:
            self.scan = int(kwargs["scan"])
        if "show" in keys:
            self.show = bool(kwargs["show"])

        self.brain = StateMachine()

        self.id = 0

    def __repr__(self) -> str:
        return f"<{self.name.title()} GameEntity>"

    def __str__(self) -> str:
        return f"<{self.name.title()} GameEntity>"

    def render(self, surface: pygame.surface.Surface) -> None:
        "Render an entity and it's hitbox if show_hitbox is True, and blit it to the surface"
        x, y = self.location
        try:
            x, y = float(x), float(y)
        except TypeError as ex:
            raise TypeError(
                f"Could not convert location {self.location} to floats!"
            ) from ex
        w, h = self.image.get_size()
        if self.show:
            surface.blit(self.image, (x - w / 2, y - h / 2))
        if self.show_hitbox:
            pygame.draw.rect(surface, [0] * 3, self.get_col_rect(), 1)
            if self.scan:
                pygame.draw.circle(
                    surface, [0, 0, 60], to_int([x, y]), self.scan, 1
                )

    def process(self, time_passed: float) -> None:
        "Process brain and move according to time passed if speed > 0 and not at destination"
        if self.doprocess:
            self.brain.think()

            if self.speed > 0 and self.location != self.destination:
                # vec_to_dest = self.destination - self.location
                # distance_to_dest = vec_to_dest.get_length()
                vec_to_dest = Vector2.from_points(
                    self.location, self.destination
                )
                distance_to_dest = self.location.get_distance_to(
                    self.destination
                )
                heading = vec_to_dest.get_normalized()
                # prevent going back and forward really fast once it make it close to destination
                travel_distance = min(
                    distance_to_dest, (time_passed * self.speed)
                )
                self.location += heading * round(travel_distance)

    def get_xywh(self) -> tuple[int, int, int, int]:
        "Return x and y position and width and height of self.image for collision"
        # Return x pos, y pos, width, and height for collision
        x, y = self.location
        w, h = (0, 0)
        if self.image is not None:
            w, h = self.image.get_size()
        x -= w / 2
        y -= h / 2
        return x, y, w, h

    def get_col_rect(self) -> pygame.rect.Rect:
        "Return a rect for collision"
        return pygame.rect.Rect(*self.get_xywh())

    def is_over(self, point: tuple[int, int] | Vector2) -> bool:
        "Return True if point is over self.image"
        # Return True if a point is over image
        point_x, point_y = point
        x, y, w, h = self.get_xywh()

        in_x = point_x >= x and point_x < x + w
        in_y = point_y >= y and point_y < y + h

        return in_x and in_y

    def collision(self, sprite: GameEntity) -> bool:
        "Return True if a sprite's image is over self.image"
        # Return True if a sprite's image is over our image
        rect_self = self.get_col_rect()  # rect self
        rect_other = sprite.get_col_rect()  # rect other

        return bool(rect_self.colliderect(rect_other))

    def collide(
        self, entityname: str, action: Callable[[GameEntity, GameEntity], None]
    ) -> None:
        "For every entity with the name of entityname, call action(self, entity)"
        for entity in self.world.get_type(entityname):
            if entity is not None:
                if self.collision(entity):
                    action(self, entity)


##    def relative_side(self, entity):
##        "Return what side of an entity we are on, to be used with collision"
##        # THIS IS VERY BROKEN PLZ FIX
##        wall = hasattr(entity, 'side')
##        # pylint: C0301: Line too long (122/100)
##        sides = ['top', 'right', 'bottom', 'left']# 45:'top right', 135:'bottom right', 225:'bottom left', 315:'top left'}
##        sloc = self.location
##        eloc = entity.location
##        rect = entity.get_col_rect()
##        vec = Vector2.from_points(sloc, eloc)
##        # pylint: R1705: Unnecessary "elif" after "return"
##        if not wall:
##        # pylint: W0612: Unused variable 'final'
##            final = [i*90 for i in range(4)]
##            # pylint: W0612: Unused variable 'first'
##            first = [i*45 for i in range(8)]
##            rsides = [rect.midtop, rect.midright, rect.midbottom, rect.midleft]
##            #rsides = [Vector2(x, y) for x, y in rsides]
##            #side_deg = [atan2(v.y, v.x) for v in rsides]
##            # pylint: C0301: Line too long (154/100)
##            side_deg = [round((heading_to_degrees( Vector2.from_points(entity.location, Vector2(x, y)).get_normalized()) + 360) % 360) for x, y in rsides]
##            deg = 360 - round((heading_to_degrees(vec.get_normalized())) % 360)
##            if deg <= 45:
##                deg = 0
##            sdeg = closest(round(deg), side_deg)
##            num = side_deg.index(sdeg)
##
##            return sides[num]
##        elif wall:
##            return entity.side
##        return None
##
##class BaseWall(GameEntity):
##    "Wall to stop entities from going to invalid places"
##    def __init__(self, world, location, wh, side='left', **kwargs):
##        GameEntity.__init__(self, world, 'wall', None, **kwargs)
##        # pylint: I1101: Module 'pygame.surface' has no 'Surface' member, but source is unavailable. Consider adding this module to extension-pkg-allow-list if you want to perform analysis based on run-time introspection of living objects.
##        self.image = pygame.surface.Surface(to_int(wh)).convert()
##        self.location = Vector2(*to_int(location))
##        self.side = side
##        self.scan = 0
##
##    def render(self, surface):
##        "Renders hitbox to screen if self.show_hitbox = True, otherwise nothing."
##        self.show = False
##        GameEntity.render(self, surface)


class BaseButton(GameEntity):
    "Base button, if entity self.trigger is over image and mouse down, call self.action(self)"

    def __init__(
        self,
        world: "WorldBase",
        anim: Collection[pygame.surface.Surface],
        trigger: str,
        action: Callable[[BaseButton], Any],
        states: int = 0,
        **kwargs: Any,
    ) -> None:
        # types: index error: Value of type "Collection[Surface]" is not indexable
        GameEntity.__init__(self, world, "button", anim[0], **kwargs)
        self.trigger = trigger
        self.action = action
        self.value = 0
        self.max_value = int(states)
        self.anim = anim
        self.press_time = 1
        self.last_press: int | float = 0
        self.scan = int(max(get_surf_lens(self.anim)) / 2) + 2

        keys = list(kwargs.keys())
        if "time" in keys:
            # types: assignment error: Incompatible types in assignment (expression has type "float", variable has type "int")
            self.press_time = float(kwargs["time"])

    def process(self, time_passed: float) -> None:
        "Call self.action(self) if any self.trigger entity is over self"
        # Do regular processing
        GameEntity.process(self, time_passed)

        # If not recently pressed,
        self.last_press -= time_passed
        self.last_press = max(self.last_press, 0)
        if (
            pygame.mouse.get_pressed()[0] and not self.last_press
        ):  # get_pressed returns (left, middle, right)
            self.last_press = self.press_time
            # Test if pressed, and if so call self.action(self)
            trigger = self.world.get_closest_entity(
                # types: arg-type error: Argument 2 to "get_closest_entity" of "WorldBase" has incompatible type "Vector2"; expected "Tuple[int, int]"
                self.trigger,
                self.location,
                self.scan,
            )
            if trigger is not None:
                if self.is_over(trigger.location):
                    self.value = (self.value + 1) % self.max_value
                    self.action(self)

        # Update animation
        # types: index error: Value of type "Collection[Surface]" is not indexable
        self.image = self.anim[self.value % len(self.anim)]


# types:    ^^^^^^^^^^^^^^^^^^^^


class WorldBase:
    "Base class of world objects"

    def __init__(self) -> None:
        self.entities: dict[str, GameEntity] = {}  # Store all the entities
        self.entity_id = 0  # Last entity id assigned
        self.background = None

    def __repr__(self) -> str:
        return "<World Object>"

    def add_entity(self, entity: Any) -> None:
        "Stores the entity then advances the current id"
        # stores the entity then advances the current id
        # types: index error: Invalid index type "int" for "Dict[str, GameEntity]"; expected type "str"
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1

    def add_entities(self, entities: Iterable[GameEntity]) -> None:
        "Add multiple entities from a list"
        for entity in entities:
            self.add_entity(entity)

    def remove_entity(self, entity: GameEntity) -> None:
        "Remove an entity from the world"
        # types: arg-type error: Argument 1 to "__delitem__" of "dict" has incompatible type "int"; expected "str"
        del self.entities[entity.id]

    def remove_entities(self, entities: Iterable[GameEntity]) -> None:
        "Remove multiple entities from a list"
        for entity in entities:
            self.remove_entity(entity)

    def get(self, entity_id: int) -> GameEntity | None:
        "Find an entity, given it's id, and return None if it's not found"
        # find the entity, given it's id, (or None if it's not found)
        # types: comparison-overlap error: Non-overlapping container check (element type: "int", container item type: "str")
        if (not entity_id is None) and (entity_id in self.entities):
            # types:                       ^^^^^^^^
            # types: index error: Invalid index type "int" for "Dict[str, GameEntity]"; expected type "str"
            return self.entities[entity_id]
        return None

    def get_type(self, entityname: str) -> list[GameEntity]:
        "Returns all entities by the name of entityname in the world"
        matches = []
        for entity in self.entities.values():
            if entity.name == entityname:
                matches.append(entity)
        return matches

    def process(self, time_passed: float) -> None:
        "Process every entity stored the world"
        # process every entity in the world
        time_passed_secconds = time_passed / 1000
        for entity in list(self.entities.values()):
            entity.process(time_passed_secconds)

    # types: no-untyped-def error: Function is missing a type annotation
    def render(self, surface):
        "Draw the background and render all entities"
        # draw the background and all it's entites
        surface.unlock()
        if not self.background is None:
            # types: unreachable error: Statement is unreachable
            surface.blit(self.background, (0, 0))
        # types: ^^^^^^^^^^^^^^^
        for entity in self.entities.values():
            entity.render(surface)
        surface.lock()

    def get_close_entity(
        self, name: str, location: tuple[int, int], rnge: int = 100
    ) -> GameEntity | None:
        "Find an entity with name within range of location"
        # find an entity within range of location
        # types: no-untyped-call error: Call to untyped function "Vector2" in typed context
        # types: assignment error: Incompatible types in assignment (expression has type "Vector2", variable has type "Tuple[int, int]")
        location = Vector2(*location)

        for entity in self.entities.values():
            if entity.name == name:
                # types: attr-defined error: "Tuple[int, int]" has no attribute "get_distance_to"
                distance = location.get_distance_to(entity.location)
                if distance < rnge:
                    return entity
        return None

    def get_closest_entity(
        self, name: str, location: tuple[int, int], rnge: int = 100
    ) -> GameEntity | None:
        "Find the closest entity with name within range of location"
        # find the closest entity within range of location
        # types: no-untyped-call error: Call to untyped function "Vector2" in typed context
        # types: assignment error: Incompatible types in assignment (expression has type "Vector2", variable has type "Tuple[int, int]")
        location = Vector2(*location)

        matches = {}
        for entity in self.entities.values():
            if entity.name == name:
                # types: attr-defined error: "Tuple[int, int]" has no attribute "get_distance_to"
                distance = location.get_distance_to(entity.location)
                if distance < rnge:
                    matches[distance] = entity

        if matches:
            return matches[min(matches.keys())]
        return None


BLACK = (0, 0, 0)
BLUE = (15, 15, 255)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
RED = (255, 0, 0)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
