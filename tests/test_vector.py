"""Test vector module."""

from __future__ import annotations

import math

import pytest

from checkers.vector import (
    Vector2,
    Vector3,
    Vector4,
    get_angle_between_vectors,
    project_v_onto_w,
)


def test_str() -> None:
    assert str(Vector2(3, 6)) == "Vector2(x=3, y=6)"


def test_repr() -> None:
    assert repr(Vector2(3, 6)) == "Vector2(x=3, y=6)"


def test_eq_vec() -> None:
    assert Vector2(3, 6) == Vector2(3, 6)


def test_eq_tuple() -> None:
    assert Vector2(3, 6) == (3, 6)  # type: ignore[comparison-overlap]


def test_from_points() -> None:
    assert Vector2.from_points((0, 3), (2, 5)) == Vector2(2, 2)


def test_from_degrees() -> None:
    assert round(Vector2.from_degrees(-90, 10), 9) == Vector2(0, -10)


def test_get_magnitude() -> None:
    assert Vector2(3, 4).magnitude() == 5


def test_get_distance_to() -> None:
    assert Vector2(3, 4).get_distance_to((6, 8)) == 5


def test_normalized() -> None:
    assert Vector2(3, 4).normalized() == Vector2(3 / 5, 4 / 5)


def test_add() -> None:
    assert Vector2(3, 4) + Vector2(5, 6) == Vector2(8, 10)


def test_sub() -> None:
    assert Vector2(3, 4) - Vector2(5, 6) == Vector2(-2, -2)


def test_neg() -> None:
    assert -Vector2(3, 4) == Vector2(-3, -4)


def test_mul() -> None:
    assert Vector2(5, 10) * 3 == Vector2(15, 30)


def test_rmul() -> None:
    assert 3 * Vector2(5, 10) == Vector2(15, 30)


def test_truediv() -> None:
    assert Vector2(10, 5) / 2 == Vector2(5, 2.5)


def test_truediv_zero() -> None:
    with pytest.raises(ZeroDivisionError):
        Vector2(10, 5) / 0


def test_len() -> None:
    assert len(Vector2(5, 20)) == 2


def test_getitem() -> None:
    vec = Vector2(7, 28)
    assert vec[0] == 7
    assert vec[1] == 28


def test_heading() -> None:
    assert Vector2(2, 2).heading() == 45
    assert Vector2(-2, 2).heading() == 135
    assert Vector2(-2, -2).heading() == -135  # 225
    assert Vector2(2, -2).heading() == -45  # 315


def test_rotate() -> None:
    assert round(Vector2(12, 3).rotate(90)) == Vector2(-3, 12)


def test_floordiv() -> None:
    assert Vector2(7, 28) // 3 == Vector2(2, 9)


def test_round() -> None:
    assert round(Vector2(3.145, 2.162), 2) == Vector2(3.15, 2.16)


def test_abs() -> None:
    assert abs(Vector2(4, -5)) == Vector2(4, 5)


def test_mod() -> None:
    assert Vector2(4, 5) % 3 == Vector2(1, 2)


def test_divmod() -> None:
    div, mod = divmod(Vector2(7, 28), 4)
    assert div == Vector2(7 // 4, 28 // 4)
    assert mod == Vector2(7 % 4, 28 % 4)


def test_matmul() -> None:
    assert Vector2(9, 7) @ Vector2(2, 3) == (9 * 2) + (7 * 3)
    assert Vector2(21, 75).dot(Vector2(5, 28)) == (21 * 5) + (75 * 28)


def test_reflect() -> None:
    assert Vector2(9, 7).reflect((1, 0)) == Vector2(-9, 7)
    assert Vector2(9, 7).reflect((0, 1)) == Vector2(9, -7)
    assert Vector2(9, 7).reflect((-1, 0)) == Vector2(-9, 7)
    assert round(Vector2(9, 7).reflect(Vector2(1, 1).normalized())) == Vector2(
        -7,
        -9,
    )


def test_lerp() -> None:
    assert Vector2(9, 7).lerp((0, 0), 0) == Vector2(9, 7)
    assert Vector2(9, 7).lerp((0, 0), 1) == Vector2(0, 0)
    assert Vector2(9, 7).lerp((0, 0), 0.5) == Vector2(x=4.5, y=3.5)


def test_clamp() -> None:
    assert Vector2(9, 7).clamp(0, 7) == Vector2(7, 7)
    assert Vector2(9, -7).clamp(0, 7) == Vector2(7, 0)


def test_get_angle_between_vectors() -> None:
    assert (
        math.degrees(get_angle_between_vectors(Vector2(0, 3), Vector2(3, 0)))
        == 90
    )
    assert (
        math.degrees(get_angle_between_vectors(Vector2(3, 0), Vector2(0, -3)))
        == 90
    )
    assert (
        math.degrees(get_angle_between_vectors(Vector2(0, -3), Vector2(-3, 0)))
        == 90
    )
    assert (
        math.degrees(get_angle_between_vectors(Vector2(-3, 0), Vector2(0, 3)))
        == 90
    )


def test_project_v_onto_w() -> None:
    assert round(
        project_v_onto_w(Vector2(4, 16), Vector2(2, -6)),
        4,
    ) == Vector2(x=-4.4, y=13.2)


def test_cross() -> None:
    assert Vector3(1, 2, 3).cross((4, 5, 6)) == Vector3(-3, 6, -3)


def test_slerp_v3() -> None:
    assert (
        Vector3(1, 2, 3).slerp((4, 5, 6), 0) == Vector3(1, 2, 3).normalized()
    )
    assert (
        Vector3(1, 2, 3).slerp((4, 5, 6), 1) == Vector3(4, 5, 6).normalized()
    )
    assert Vector3(1, 2, 3).slerp((4, 5, 6), 0.5) == Vector3(
        x=0.3638667954886597,
        y=0.5556981892812023,
        z=0.747529583073745,
    )


def test_slerp_v4() -> None:
    assert Vector4(1, 2, 3, 4).slerp((5, 6, 7, 8), 0) == Vector4(
        x=0.18257418583505539,
        y=0.36514837167011077,
        z=0.5477225575051662,
        w=0.7302967433402215,
    )
    assert Vector4(1, 2, 3, 4).slerp((5, 6, 7, 8), 1) == Vector4(
        x=0.3790490217894517,
        y=0.454858826147342,
        z=0.5306686305052324,
        w=0.6064784348631227,
    )
    assert Vector4(1, 2, 3, 4).slerp((5, 6, 7, 8), 0.5) == Vector4(
        x=0.28302330376727836,
        y=0.41323282779013937,
        z=0.5434423518130005,
        w=0.6736518758358615,
    )
