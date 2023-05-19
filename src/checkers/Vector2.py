#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Vector2 Class for games

"Vector2 Class for games"

# Original version by Will McGugan, modified extensively by CoolCat467
# Programmed by CoolCat467

__title__ = "Vector2 Module"
__author__ = "CoolCat467"
__version__ = "1.0.6"
__ver_major__ = 1
__ver_minor__ = 0
__ver_patch__ = 6

import math


class Vector2:
    "Vector2 Object. Takes an x an a y choordinate."

    def __init__(self, x=0, y=0):
        if isinstance(x, (list, tuple)):
            x, y = x
        self.x = x
        self.y = y

    def __repr__(self):
        "Return representation of Vector2."
        return f"Vector2({self.x}, {self.y})"

    @staticmethod
    def from_points(from_point, to_point):
        "Return a vector with the direction of frompoint to topoint."
        p1, p2 = list(from_point), list(to_point)
        return Vector2(p2[0] - p1[0], p2[1] - p1[1])

    def get_magnitude(self):
        "Return the magnitude (length) of self."
        return math.sqrt(self.x**2 + self.y**2)

    def get_distance_to(self, point):
        "Return the magnitude (distance) to a given point."
        return Vector2.from_points(point, self).get_magnitude()

    def normalize(self):
        "Normalize self (make into a unit vector) **IN PLACE**"
        magnitude = self.get_magnitude()
        if not magnitude == 0:
            self.x /= magnitude
            self.y /= magnitude

    def copy(self):
        "Return a copy of self."
        return Vector2(self.x, self.y)

    def __copy__(self):
        "Return a copy of self."
        return self.copy()

    def get_normalized(self):
        "Return a normalized vector (heading)."
        vec = self.copy()
        vec.normalize()
        return vec

    def get_heading(self):
        "Returns the arc tangent (mesured in radians) of self.y/self.x."
        return math.atan2(self.y, self.x)

    def get_heading_deg(self):
        "Returns the arc tangent (mesured in degrees) of self.y/self.x."
        return math.degrees(self.get_heading())

    def rotate(self, radians):
        "Returns a new vector by rotating self around (0, 0) by radians."
        new_heading = self.get_heading() + radians
        magnitude = self.get_magnitude()
        x = math.cos(new_heading) * magnitude
        y = math.sin(new_heading) * magnitude
        # Round up to 13 digits, or we'll get wierd rounding errors, like
        # .00000000000001
        return Vector2(round(x, 13), round(y, 13))

    def rotate_deg(self, degrees):
        "Returns a new vector by rotating self around (0, 0) by degrees clockwise."
        return self.rotate(math.radians(-degrees))

    def _addv(self, vec):
        "Return the addition of self and another vector."
        return Vector2(self.x + vec.x, self.y + vec.y)

    # rhs is Right Hand Side
    def __add__(self, rhs):
        if isinstance(rhs, self.__class__):
            return self._addv(rhs)
        if hasattr(rhs, "__len__"):
            if len(rhs) == 2:
                x, y = rhs
                ##                return self._addv(self.__class__(x, y))
                return Vector2(self.x + x, self.y + y)
            raise LookupError(
                "Length of right hand sign opperator length is not equal to two!"
            )
        raise AttributeError("Length not found.")

    def _subv(self, vec):
        "Return the subtraction of self and another vector."
        ##        print(self.x, self.y, vec.x, vec.y)
        return Vector2(self.x - vec.x, self.y - vec.y)

    def __sub__(self, rhs):
        if isinstance(rhs, self.__class__):
            return self._subv(rhs)
        if hasattr(rhs, "__len__"):
            if len(rhs) == 2:
                x, y = rhs
                return Vector2(self.x - x, self.y - y)
            raise LookupError(
                "Length of right hand sign opperator length is not equal to two!"
            )
        raise AttributeError("Length not found.")

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar):
        try:
            x, y = self.x / scalar, self.y / scalar
        except ZeroDivisionError:
            x, y = self.x, self.y
        return Vector2(x, y)

    def __len__(self):
        return 2

    def __iter__(self):
        return iter((self.x, self.y))

    def __getitem__(self, x: int):
        return (self.x, self.y)[x]

    def __round__(self):
        return Vector2(round(self.x), round(self.y))

    def __abs__(self):
        return Vector2(abs(self.x), abs(self.y))
