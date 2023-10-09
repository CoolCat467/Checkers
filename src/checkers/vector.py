#!/usr/bin/env python3
# Vector2 Class for games

"Vector2 Class for games"

# Original version by Will McGugan, modified extensively by CoolCat467
# Programmed by CoolCat467

__title__ = "Vector2 Module"
__author__ = "CoolCat467"
__version__ = "1.0.7"
__ver_major__ = 1
__ver_minor__ = 0
__ver_patch__ = 7

import math
from collections.abc import Iterable
from typing import NamedTuple, Self


class Vector2(NamedTuple):
    "Vector2 Object. Takes an x an a y choordinate."
    x: int | float
    y: int | float

    @classmethod
    def from_iter(cls, iterable: Iterable[int | float]) -> Self:
        "Return new vector from iterable"
        return cls(*iter(iterable))

    @classmethod
    def from_points(
        cls, from_point: Iterable[int | float], to_point: Iterable[int | float]
    ) -> Self:
        "Return a vector with the direction of frompoint to topoint."
        return cls.from_iter(to_point) - from_point

    @classmethod
    def from_radians(
        cls, radians: int | float, distance: int | float = 1
    ) -> Self:
        """Return vector from angle in radians"""
        return cls(math.cos(radians), math.sin(radians)) * distance

    def magnitude(self) -> float:
        "Return the magnitude (length) of self."
        return math.hypot(*self)

    def get_distance_to(self, point: Iterable[int | float]) -> float:
        "Return the magnitude (distance) to a given point."
        return self.from_points(point, self).magnitude()

    def normalized(self) -> Self:
        """Return a normalized (unit) vector"""
        return self / self.magnitude()

    def heading_radians(self) -> float:
        "Returns the arc tangent (mesured in radians) of self.y/self.x."
        return math.atan2(self.y, self.x)

    def heading(self) -> float:
        """Returns the arc tangent (mesured in degrees) of self.y/self.x.

        Angle is measured from the positive X axis counterclockwise"""
        return math.degrees(self.heading_radians())

    def rotate_radians(self, radians: int | float) -> Self:
        "Returns a new vector by rotating self around (0, 0) by radians."
        new_heading = self.heading_radians() + radians
        return self.from_radians(new_heading, self.magnitude())

    def rotate(self, degrees: int | float) -> Self:
        """Returns a new vector by rotating self around (0, 0) by degrees

        Angle is measured from the positive X axis counterclockwise"""
        return self.rotate_radians(math.radians(degrees))

    # rhs is Right Hand Side
    def __add__(  # type: ignore[override]
        self, rhs: Iterable[int | float]
    ) -> Self:
        return self.from_iter(a + b for a, b in zip(self, rhs, strict=True))

    def __sub__(self, rhs: Iterable[int | float]) -> Self:
        return self.from_iter(a - b for a, b in zip(self, rhs, strict=True))

    def __neg__(self) -> Self:
        return self.from_iter(-c for c in self)

    def __mul__(self, scalar: int | float) -> Self:  # type: ignore[override]
        return self.from_iter(c * scalar for c in self)

    def __truediv__(self, scalar: int | float) -> Self:
        return self.from_iter(c / scalar for c in self)

    def __floordiv__(self, scalar: int | float) -> Self:
        return self.from_iter(c // scalar for c in self)

    def __round__(self, ndigits: int | None = None) -> Self:
        return self.from_iter(round(c, ndigits) for c in self)

    def __abs__(self) -> Self:
        return self.from_iter(abs(c) for c in self)

    def __mod__(self, scalar: int | float) -> Self:
        return self.from_iter(c % scalar for c in self)

    def __divmod__(self, rhs: int | float) -> tuple[Self, Self]:
        "Return tuple of (self // rhs, self % rhs)"
        return self // rhs, self % rhs

    def dot(self, vec: Iterable[int | float]) -> int | float:
        """Return the dot product of this vector and another"""
        return sum(a * b for a, b in zip(self, vec, strict=True))

    def __matmul__(self, vec: Iterable[int | float]) -> int | float:
        """Return the dot product of this vector and another"""
        return self.dot(vec)
