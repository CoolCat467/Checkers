#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from typing import Iterable, Iterator, Self


class Vector2:
    "Vector2 Object. Takes an x an a y choordinate."
    __slots__ = ("x", "y")

    def __init__(self, x: int | float = 0, y: int | float = 0):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        "Return representation of Vector2."
        return f"{self.__class__.__name__}({self.x}, {self.y})"

    @classmethod
    def from_points(
        cls, from_point: Iterable[int | float], to_point: Iterable[int | float]
    ) -> Self:
        "Return a vector with the direction of frompoint to topoint."
        p1_iter = iter(from_point)
        p1_x = next(p1_iter)
        p1_y = next(p1_iter)
        p2_iter = iter(to_point)
        p2_x = next(p2_iter)
        p2_y = next(p2_iter)
        return cls(p2_x - p1_x, p2_y - p1_y)

    def get_magnitude(self) -> float:
        "Return the magnitude (length) of self."
        return math.sqrt(self.x**2 + self.y**2)

    def get_distance_to(self, point: Iterable[int | float]) -> float:
        "Return the magnitude (distance) to a given point."
        return self.__class__.from_points(point, self).get_magnitude()

    def normalize(self) -> None:
        "Normalize self (make into a unit vector) **IN PLACE**"
        magnitude = self.get_magnitude()
        if magnitude != 0:
            self.x /= magnitude
            self.y /= magnitude

    def copy(self) -> Self:
        "Return a copy of self."
        return self.__class__(self.x, self.y)

    def __copy__(self) -> Self:
        "Return a copy of self."
        return self.copy()

    def get_normalized(self) -> Self:
        "Return a normalized vector (heading)."
        vec = self.copy()
        vec.normalize()
        return vec

    def get_heading(self) -> float:
        "Returns the arc tangent (mesured in radians) of self.y/self.x."
        return math.atan2(self.y, self.x)

    def get_heading_deg(self) -> float:
        "Returns the arc tangent (mesured in degrees) of self.y/self.x."
        return math.degrees(self.get_heading())

    def rotate(self, radians: int | float) -> Self:
        "Returns a new vector by rotating self around (0, 0) by radians."
        new_heading = self.get_heading() + radians
        magnitude = self.get_magnitude()
        x = math.cos(new_heading) * magnitude
        y = math.sin(new_heading) * magnitude
        return self.__class__(x, y)

    def rotate_deg(self, degrees: int | float) -> Self:
        """Returns a new vector by rotating self around (0, 0) by degrees

        Angle is measured from the positive X axis counterclockwise"""
        return self.rotate(math.radians(degrees))

    def _addv(self, vec: Self) -> Self:
        "Return the addition of self and another vector."
        return self.__class__(self.x + vec.x, self.y + vec.y)

    # rhs is Right Hand Side
    def __add__(self, rhs: Iterable[int | float]) -> Self:
        if isinstance(rhs, self.__class__):
            return self._addv(rhs)
        if hasattr(rhs, "__iter__"):
            iter_obj = iter(rhs)
            x, y = next(iter_obj), next(iter_obj)
            return self.__class__(self.x + x, self.y + y)
        raise AttributeError("Length not found.")

    def _subv(self, vec: Self) -> Self:
        "Return the subtraction of self and another vector."
        return self.__class__(self.x - vec.x, self.y - vec.y)

    def __sub__(self, rhs: Iterable[int | float]) -> Self:
        if isinstance(rhs, self.__class__):
            return self._subv(rhs)
        if hasattr(rhs, "__len__"):
            iter_obj = iter(rhs)
            x, y = next(iter_obj), next(iter_obj)
            return self.__class__(self.x - x, self.y - y)
        raise AttributeError("Length not found.")

    def __neg__(self) -> Self:
        return self.__class__(-self.x, -self.y)

    def __mul__(self, scalar: int | float) -> Self:
        return self.__class__(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: int | float) -> Self:
        try:
            x, y = self.x / scalar, self.y / scalar
        except ZeroDivisionError:
            x, y = self.x, self.y
        return self.__class__(x, y)

    def __len__(self) -> int:
        return 2

    def __iter__(self) -> Iterator[int | float]:
        return iter((self.x, self.y))

    def __getitem__(self, x: int) -> int | float:
        return (self.x, self.y)[x]

    def __round__(self, ndigits: int | None = None) -> Self:
        return self.__class__(round(self.x, ndigits), round(self.y, ndigits))

    def __abs__(self) -> Self:
        return self.__class__(abs(self.x), abs(self.y))

    def dot(self, vec: Iterable[int | float]) -> int | float:
        """Return the dot product of this vector and another"""
        iter_vec = iter(vec)
        v2_x = next(iter_vec)
        v2_y = next(iter_vec)
        return self.x * v2_x + self.y * v2_y

    __matmul__ = dot
