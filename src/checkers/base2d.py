"""Two-Dimensional Game Base Module."""

# Programmed by CoolCat467

from __future__ import annotations

# Copyright (C) 2023  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "2d Game Base Module"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "0.0.1"


import math
from typing import TYPE_CHECKING, Any, TypeVar, cast

import pygame

from checkers.statemachine import StateMachine
from checkers.vector import Vector2

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


def amol(
    lst: Iterable[float],
    **kwargs: float,
) -> tuple[float, ...]:
    """All Math On List; a=Add, s=Subtract, m=Multiply, d=Divide, p=To the power of."""
    # Math Operator acting upon All values of a List
    data = list(lst)
    rng = range(len(data))
    for op, operand in kwargs.items():
        if op == "a":  # add
            for i in rng:
                data[i] += operand
        elif op == "s":  # subtract
            for i in rng:
                data[i] -= operand
        elif op == "m":  # multiply
            for i in rng:
                data[i] *= operand
        elif op == "d":  # divide
            for i in rng:
                data[i] /= operand
        elif op == "p":  # power
            for i in rng:
                data[i] **= operand
    return tuple(data)


def part_quotes(text: str, which: int, quotes: str = "'") -> str:
    """Return part which of text within quotes."""
    return text.split(quotes)[which * 2 + 1]


def to_int(lst: Iterable[float]) -> list[int]:
    """Return all values of a list into integers."""
    return [int(i) for i in lst]


def to_flt(lst: Iterable[float]) -> list[float]:
    """Return all values of a list into floats."""
    return [float(i) for i in lst]


def to_str(lst: Iterable[float]) -> list[str]:
    """Return all values of a list into strings."""
    return [str(i) for i in lst]


def round_all(lst: Iterable[float]) -> list[int]:
    """Round all values of a list."""
    return [round(i) for i in lst]


def abs_all(lst: Iterable[float]) -> list[float]:
    """Return all values of a list into the absolute value of that number."""
    return [abs(i) for i in lst]


def to_chr(lst: Iterable[int]) -> list[str]:
    """Convert every value of a list into a character."""
    return [chr(i) for i in lst]


def scale_surf(
    surface: pygame.surface.Surface,
    scalar: float,
) -> pygame.surface.Surface:
    """Scale surfaces by a scalar."""
    size = surface.get_size()
    return pygame.transform.scale(surface, [int(s * scalar) for s in size])


def scale_surfs(
    surfaces: Iterable[pygame.surface.Surface],
    scalar: float,
) -> list[pygame.surface.Surface]:
    """Scale multiple surfaces by a scalar."""
    return [scale_surf(surface, scalar) for surface in surfaces]


def set_surf_size(
    surface: pygame.surface.Surface,
    wh: tuple[float, float],
) -> pygame.surface.Surface:
    """Set the size of a surface."""
    return pygame.transform.scale(surface, to_int(wh))


def get_surf_len(surface: pygame.surface.Surface) -> float:
    """Return the length of a surface."""
    return math.hypot(*surface.get_size())


def get_surf_lens(surfaces: Iterable[pygame.surface.Surface]) -> list[float]:
    """Return the lengths of multiple surfaces."""
    return [get_surf_len(surf) for surf in surfaces]


def get_colors(
    surface: pygame.surface.Surface,
) -> set[tuple[int, int, int]]:
    """Return a set of all different colors in a surface."""
    surface = surface.copy()
    width, height = surface.get_size()
    colors = set()
    for x in range(width):
        for y in range(height):
            color = cast("tuple[int, int, int]", surface.get_at((x, y))[:3])
            if color not in colors:
                colors.add(color)
    return colors


def replace_with_color(
    surface: pygame.surface.Surface,
    color: tuple[int, int, int],
) -> pygame.surface.Surface:
    """Fill all pixels of the surface with color, preserve transparency."""
    surface = surface.copy().convert_alpha()
    width, height = surface.get_size()
    r, g, b = color
    surface.lock()
    for x in range(width):
        for y in range(height):
            a = surface.get_at((x, y))[3]
            surface.set_at((x, y), pygame.Color(r, g, b, a))
    surface.unlock()
    return surface


def replace_color(
    surface: pygame.surface.Surface,
    targetcolor: tuple[int, int, int],
    replace_color: Any,
) -> pygame.surface.Surface:
    """Fill all pixels of the surface of a color with color, preserve transparency."""
    surface = surface.copy().convert_alpha()
    w, h = surface.get_size()
    r, g, b = replace_color
    surface.lock()
    for x in range(w):
        for y in range(h):
            data = cast("tuple[int, int, int, int]", surface.get_at((x, y)))
            if data[:3] == targetcolor:
                a = data[3]
                surface.set_at((x, y), pygame.Color(r, g, b, a))
    surface.unlock()
    return surface


def get_deltas(
    number: float,
    lst: Iterable[float],
) -> list[float]:
    """Return a list of the change from a number each value of a list is."""
    return [abs(i - number) for i in lst]


L = TypeVar("L", bound=float)


def closest(number: float, lst: list[L]) -> L:
    """Return the closest value of lst a number is."""
    delta = get_deltas(number, lst)
    return lst[delta.index(min(delta))]


def farthest(number: float, lst: list[L]) -> L:
    """Return the farthest value of lst a number is."""
    delta = get_deltas(number, lst)
    return lst[delta.index(max(delta))]


class GameEntity:
    """Base Class for all entities."""

    def __init__(
        self,
        name: str,
        world: WorldBase,
        image: pygame.surface.Surface | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize game entity."""
        self.name = name
        self.world = world
        self.image = image

        self.location = Vector2(0, 0)
        self.destination = Vector2(0, 0)
        self.speed = 0

        self.scan = 100
        if self.image is not None:
            self.visible = True
            self.scan = int(get_surf_len(self.image)) // 2 + 2

        self.show_hitbox = False
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
        if "visible" in keys:
            self.visible = bool(kwargs["visible"])

        self.brain = StateMachine()

        self.id = 0

    @property
    def rect(self) -> pygame.rect.Rect:
        """Rect."""
        if self.image is None:
            return pygame.rect.Rect(0, 0, 0, 0)
        rect = pygame.rect.Rect((0, 0), self.image.get_size())
        x, y = self.location
        rect.center = (int(x), int(y))
        return rect

    def render(self, surface: pygame.surface.Surface) -> None:
        """Render an entity and it's hitbox if show_hitbox is True, and blit it to the surface."""
        x, y = self.location
        try:
            x, y = float(x), float(y)
        except TypeError as ex:
            raise TypeError(
                f"Could not convert location {self.location} to floats!",
            ) from ex
        if self.visible:
            if self.image is None:
                raise ValueError("self.image is None")
            w, h = self.image.get_size()
            surface.blit(self.image, (x - w // 2, y - h // 2))
        if self.show_hitbox:
            pygame.draw.rect(surface, (0, 0, 0), self.rect, 1)
            if self.scan:
                pygame.draw.circle(
                    surface,
                    (0, 0, 60),
                    to_int([x, y]),
                    self.scan,
                    1,
                )

    def process(self, time_passed: float) -> None:
        """Process brain and move according to time passed if speed > 0 and not at destination."""
        if self.doprocess:
            self.brain.think()

        if self.speed > 0 and self.location != self.destination:
            # vec_to_dest = self.destination - self.location
            # distance_to_dest = vec_to_dest.get_length()
            vec_to_dest = Vector2.from_points(self.location, self.destination)
            distance_to_dest = self.location.get_distance_to(self.destination)
            heading = vec_to_dest.normalized()
            # prevent going back and forward really fast once it make it close to destination
            travel_distance = min(distance_to_dest, (time_passed * self.speed))
            self.location += heading * round(travel_distance)

    def is_over(self, point: tuple[int, int] | Vector2) -> bool:
        """Return True if point is over self.image."""
        # Return True if a point is over image
        return self.rect.collidepoint(tuple(point))

    def collision(self, sprite: GameEntity) -> bool:
        """Return True if a sprite's image is over self.image."""
        # Return True if a sprite's image is over our image
        return self.rect.colliderect(sprite.rect)

    def collide(
        self,
        entityname: str,
        action: Callable[[GameEntity, GameEntity], None],
    ) -> None:
        """For every entity with the name of entityname, call action(self, entity)."""
        for entity in self.world.get_type(entityname):
            if entity is not None and self.collision(entity):
                action(self, entity)


class BaseButton(GameEntity):
    """Base button, if entity self.trigger is over image and mouse down, call self.action(self)."""

    def __init__(
        self,
        world: WorldBase,
        anim: Sequence[pygame.surface.Surface],
        trigger: str,
        action: Callable[[BaseButton], Any],
        states: int = 0,
        **kwargs: Any,
    ) -> None:
        """Initialize button."""
        super().__init__("button", world, anim[0], **kwargs)
        self.trigger = trigger
        self.action = action
        self.value = 0
        self.max_value = int(states)
        self.anim = anim
        self.press_time: float = 1.0
        self.last_press: float = 0.0
        self.scan = int(max(get_surf_lens(self.anim)) / 2) + 2

        keys = list(kwargs.keys())
        if "time" in keys:
            self.press_time = float(kwargs["time"])

    def process(self, time_passed: float) -> None:
        """Call self.action(self) if any self.trigger entity is over self."""
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
                self.trigger,
                self.location,
                self.scan,
            )
            if trigger is not None and self.is_over(trigger.location):
                self.value = (self.value + 1) % self.max_value
                self.action(self)

        # Update animation
        self.image = self.anim[self.value % len(self.anim)]


class WorldBase:
    """Base class of world objects."""

    def __init__(self) -> None:
        """Initialize world."""
        self.entities: dict[int, GameEntity] = {}  # Store all the entities
        self.entity_id = 0  # Last entity id assigned
        self.background: pygame.surface.Surface | None = None

    def __repr__(self) -> str:
        """Return representation of self."""
        return "<World Object>"

    def add_entity(self, entity: Any) -> None:
        """Store the entity then advances the current id."""
        # stores the entity then advances the current id
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1

    def add_entities(self, entities: Iterable[GameEntity]) -> None:
        """Add multiple entities from a list."""
        for entity in entities:
            self.add_entity(entity)

    def remove_entity(self, entity: GameEntity) -> None:
        """Remove an entity from the world."""
        del self.entities[entity.id]

    def remove_entities(self, entities: Iterable[GameEntity]) -> None:
        """Remove multiple entities from a list."""
        for entity in entities:
            self.remove_entity(entity)

    def get(self, entity_id: int) -> GameEntity | None:
        """Find an entity, given it's id, and return None if it's not found."""
        # find the entity, given it's id, (or None if it's not found)
        if (entity_id is not None) and (entity_id in self.entities):
            return self.entities[entity_id]
        return None

    def get_type(self, entityname: str) -> list[GameEntity]:
        """Return all entities by the name of entityname in the world."""
        matches = []
        for entity in self.entities.values():
            if entity.name == entityname:
                matches.append(entity)
        return matches

    def process(self, time_passed: float) -> None:
        """Process every entity stored the world."""
        # process every entity in the world
        time_passed_seconds = time_passed / 1000
        for entity in list(self.entities.values()):
            entity.process(time_passed_seconds)

    def render(self, surface: pygame.surface.Surface) -> None:
        """Draw the background and render all entities."""
        # draw the background and all it's entities
        surface.unlock()
        if self.background is not None:
            surface.blit(self.background, (0, 0))
        for entity in self.entities.values():
            entity.render(surface)
        surface.lock()

    def get_close_entity(
        self,
        name: str,
        location: tuple[int, int] | Vector2,
        rnge: int = 100,
    ) -> GameEntity | None:
        """Find an entity with name within range of location."""
        # find an entity within range of location
        vec_location = Vector2(*location)

        for entity in self.entities.values():
            if entity.name == name:
                distance = vec_location.get_distance_to(entity.location)
                if distance < rnge:
                    return entity
        return None

    def get_closest_entity(
        self,
        name: str,
        location: tuple[int, int] | Vector2,
        rnge: int = 100,
    ) -> GameEntity | None:
        """Find the closest entity with name within range of location."""
        # find the closest entity within range of location
        vec_location = Vector2(*location)

        matches = {}
        for entity in self.entities.values():
            if entity.name == name:
                distance = vec_location.get_distance_to(entity.location)
                if distance < rnge:
                    matches[distance] = entity

        if matches:
            return matches[min(matches.keys())]
        return None
