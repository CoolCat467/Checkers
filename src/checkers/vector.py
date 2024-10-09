"""Vector - Vector module for various applications."""

# Programmed by CoolCat467

from __future__ import annotations

# Vector - Vector module for various applications.
# Copyright (C) 2024  CoolCat467
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

__title__ = "Vector Module"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"
__version__ = "2.0.0"

import math
import sys
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    TypeVar,
    cast,
)

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator

    from typing_extensions import Self

    NamedTupleMeta = type
else:
    from typing import NamedTupleMeta

T = TypeVar("T")


class BaseVector:
    """Base functionality for all vectors."""

    __slots__ = ()

    if TYPE_CHECKING:

        # D105 is 'Missing docstring in magic method', but this is to handle
        # typing issues
        def __iter__(self) -> Iterator[float]: ...  # noqa: D105
        def __getitem__(self, value: int) -> float: ...  # noqa: D105

    @classmethod
    def from_iter(cls: type[Self], iterable: Iterable[float]) -> Self:
        """Return new vector from iterable."""
        return cls(*iter(iterable))

    @classmethod
    def from_points(
        cls: type[Self],
        from_point: Iterable[float],
        to_point: Iterable[float],
    ) -> Self:
        """Return a vector with the direction of frompoint to topoint."""
        return cls.from_iter(to_point) - from_point

    def magnitude(self: Self) -> float:
        """Return the magnitude (length) of self."""
        return math.hypot(*self)

    def get_distance_to(self: Self, point: Iterable[float]) -> float:
        """Return the magnitude (distance) to a given point."""
        # return self.from_points(point, self).magnitude()
        return math.dist(point, self)

    def normalized(self: Self) -> Self:
        """Return a normalized (unit) vector."""
        return self / self.magnitude()

    # rhs is Right Hand Side
    def __add__(
        self: Self,
        rhs: Iterable[float],
    ) -> Self:
        """Return result of adding self components to rhs components."""
        return self.from_iter(a + b for a, b in zip(self, rhs, strict=True))

    def __sub__(
        self: Self,
        rhs: Iterable[float],
    ) -> Self:
        """Return result of subtracting self components from rhs components."""
        return self.from_iter(a - b for a, b in zip(self, rhs, strict=True))

    def __neg__(self: Self) -> Self:
        """Return result of negating self components."""
        return self.from_iter(-c for c in self)

    def __mul__(
        self: Self,
        scalar: float,
    ) -> Self:
        """Return result of multiplying self components by rhs scalar."""
        return self.from_iter(c * scalar for c in self)

    def __truediv__(
        self: Self,
        scalar: float,
    ) -> Self:
        """Return result of dividing self components by rhs scalar."""
        return self.from_iter(c / scalar for c in self)

    def __floordiv__(
        self: Self,
        scalar: float,
    ) -> Self:
        """Return result of floor division of self components by rhs scalar."""
        return self.from_iter(c // scalar for c in self)

    def __round__(
        self: Self,
        ndigits: int | None = None,
    ) -> Self:
        """Return result of rounding self components to given number of digits."""
        return self.from_iter(round(c, ndigits) for c in self)

    def __abs__(
        self: Self,
    ) -> Self:
        """Return result of absolute value of self components."""
        return self.from_iter(abs(c) for c in self)

    def __mod__(self: Self, scalar: float) -> Self:
        """Return result of modulus of self components by rhs scalar."""
        return self.from_iter(c % scalar for c in self)

    def __divmod__(self: Self, rhs: float) -> tuple[Self, Self]:
        """Return tuple of (self // rhs, self % rhs)."""
        mods: list[int | float] = []

        def calculate() -> Generator[float, None, None]:
            nonlocal mods
            for value in self:
                div, mod = divmod(value, rhs)
                yield div
                mods.append(mod)

        return self.from_iter(calculate()), self.from_iter(mods)

    def __matmul__(self, vec: Iterable[float]) -> float:
        """Return the dot product of this vector and another."""
        if sys.version_info >= (3, 12):
            # math.sumprod is new in python 3.12
            return math.sumprod(self, vec)
        # ignore is for `unreachable` if >= 3.12, or `unused-ignore` if < 3.12
        return sum(a * b for a, b in zip(self, vec, strict=True))  # type: ignore  # pragma: nocover

    def dot(self, vec: Iterable[float]) -> float:
        """Return the dot product of this vector and another (same as @)."""
        return self @ vec

    def reflect(self: Self, normal: Iterable[float]) -> Self:
        """Return the reflection of this vector across a normal vector."""
        normal_vec = self.from_iter(normal)
        return self - (normal_vec * (2 * (self @ normal_vec)))

    def lerp(self: Self, other: Iterable[float], t: float) -> Self:
        """Return linearly interpolated point between this vector and another vector."""
        vec = self.from_iter(other)
        return self + (vec - self) * t

    def clamp(self: Self, min_value: float, max_value: float) -> Self:
        """Return components of the vector clamped to the specified range."""
        return self.from_iter(max(min(c, max_value), min_value) for c in self)


_REAL_BASE = BaseVector


class VectorMeta(NamedTupleMeta):
    """Metaclass for Vectors.

    This is a bit of a hack to allow classes to be a subclass of both
    BaseVector and NamedTuple at the same time.
    """

    __slots__ = ()

    def __new__(
        cls: type[VectorMeta],
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
    ) -> type:
        """Inject BaseVector's methods into given class."""
        real_named_tuple = NamedTuple.__mro_entries__((NamedTuple,))[0]  # type: ignore[attr-defined]

        bases = tuple(
            real_named_tuple if base is BaseVector else base
            for base in bases
            if base is not real_named_tuple
        )

        nm_tpl = super().__new__(cls, name, bases, attrs)

        # Inject BaseVector's methods into given class
        ignore = ("__module__", "__slots__", "__doc__", "__dict__")
        for name, attribute in _REAL_BASE.__dict__.items():
            if name in ignore:
                continue
            setattr(nm_tpl, name, attribute)

        return nm_tpl


# Override BaseVector with object that uses VectorMeta metaclass.
# This tricks type checker into believing that Vector classes are truly
# instances of BaseVector.
BaseVector = cast(type[BaseVector], type.__new__(VectorMeta, "BaseVector", (), {}))  # type: ignore[misc]


class Vector2(BaseVector):
    """Vector2 Object. Takes an x and a y coordinate."""

    x: float
    y: float

    if TYPE_CHECKING:
        # Because type checking does not recognize that BaseVector is
        # really NamedTupleMeta with extra strings attached, type checkers
        # do not realize __init__ method is already set up.
        def __init__(self, x: float, y: float) -> None: ...

    @classmethod
    def from_radians(
        cls,
        radians: float,
        distance: float = 1,
    ) -> Self:
        """Return vector from angle in radians."""
        return cls(math.cos(radians), math.sin(radians)) * distance

    @classmethod
    def from_degrees(
        cls,
        degrees: float,
        distance: float = 1,
    ) -> Self:
        """Return vector from angle in degrees.

        Angle is measured from the positive X axis counterclockwise.
        """
        return cls.from_radians(math.radians(degrees), distance)

    def heading_radians(self) -> float:
        """Return the arc tangent (measured in radians) of self.y/self.x."""
        return math.atan2(self.y, self.x)

    def heading(self) -> float:
        """Return the arc tangent (measured in degrees) of self.y/self.x.

        Angle is measured from the positive X axis counterclockwise.
        """
        return math.degrees(self.heading_radians())

    def rotate_radians(self, radians: float) -> Self:
        """Return a new vector by rotating self around (0, 0) by radians."""
        new_heading = self.heading_radians() + radians
        return self.from_radians(new_heading, self.magnitude())

    def rotate(self, degrees: float) -> Self:
        """Return a new vector by rotating self around (0, 0) by degrees.

        Angle is measured from the positive X axis counterclockwise.
        """
        return self.rotate_radians(math.radians(degrees))


def get_angle_between_vectors(vec_a: Vector2, vec_b: Vector2) -> float:
    """Return the angle between two vectors (measured in radians)."""
    return math.acos((vec_a @ vec_b) / (vec_a.magnitude() * vec_b.magnitude()))


def project_v_onto_w(vec_v: Vector2, vec_w: Vector2) -> Vector2:
    """Return the projection of v onto w."""
    # vector @ vector == vector.magnitude() ** 2 but with higher precision
    scalar: float = (vec_v @ vec_w) / (vec_w @ vec_w)
    return vec_w * scalar


class Vector3(BaseVector):
    """Vector3 Object. Takes an x, y, and z coordinate."""

    x: float
    y: float
    z: float

    if TYPE_CHECKING:

        def __init__(self, x: float, y: float, z: float) -> None: ...

    def cross(
        self: Self,
        other: tuple[float, float, float],
    ) -> Self:
        """Return the cross product of this vector and another."""
        x, y, z = other
        return self.__class__(
            self.y * z - y * self.z,
            self.z * x - z * self.x,
            self.x * y - x * self.y,
        )

    def slerp(self: Self, other: Iterable[float], t: float) -> Self:
        """Return spherical linear interpolation between this vector and another vector."""
        # Created by GPT-4o
        # Normalize both vectors
        v1 = self.normalized()
        v2 = self.from_iter(other).normalized()

        # Calculate the dot product
        dot = v1.dot(v2)

        # Clamp the dot product to avoid numerical issues
        dot = max(-1.0, min(1.0, dot))

        # Calculate the angle between the vectors
        theta = math.acos(dot)  # angle in radians

        # If the angle is very small, return a linear interpolation
        if theta < 1e-6:
            return v1.lerp(v2, t)

        # Calculate the sin of the angle
        sin_theta = math.sin(theta)

        # Calculate the weights for the interpolation
        a = math.sin((1 - t) * theta) / sin_theta
        b = math.sin(t * theta) / sin_theta

        # Return the interpolated vector
        return (v1 * a + v2 * b).normalized()


class Vector4(BaseVector):
    """Vector4, Aka quaternion. Takes an x, y, z, and w coordinate."""

    x: float
    y: float
    z: float
    w: float

    if TYPE_CHECKING:

        def __init__(self, x: float, y: float, z: float, w: float) -> None: ...

    def slerp(self: Self, other: Iterable[float], t: float) -> Self:
        """Return spherical linear interpolation between this quaternion and another quaternion."""
        # Created by GPT-4o
        # Normalize both quaternions
        q1 = self.normalized()
        q2 = self.from_iter(other).normalized()

        # Calculate the dot product
        dot = q1.dot(q2)

        # If the dot product is negative, negate one quaternion to take the shortest path
        if dot < 0.0:
            q2 = -q2
            dot = -dot

        # Clamp the dot product to avoid numerical issues
        dot = max(-1.0, min(1.0, dot))

        # Calculate the angle between the quaternions
        theta = math.acos(dot)  # angle in radians

        # If the angle is very small, return a linear interpolation
        if theta < 1e-6:
            return q1.lerp(q2, t)

        # Calculate the sin of the angle
        sin_theta = math.sin(theta)

        # Calculate the weights for the interpolation
        a = math.sin((1 - t) * theta) / sin_theta
        b = math.sin(t * theta) / sin_theta

        # Return the interpolated quaternion
        return (q1 * a + q2 * b).normalized()


if __name__ == "__main__":  # pragma: nocover
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    print(f"{Vector2(3, 4) = }")
