"""Test vector module."""
from __future__ import annotations

import pytest
from checkers.vector import Vector2


def test_str() -> None:
    assert str(Vector2(3, 6)) == "Vector2(x=3, y=6)"


def test_repr() -> None:
    assert repr(Vector2(3, 6)) == "Vector2(x=3, y=6)"


def test_eq_vec() -> None:
    assert Vector2(3, 6) == Vector2(3, 6)


def test_eq_tuple() -> None:
    assert Vector2(3, 6) == (3, 6)


def test_from_points() -> None:
    assert Vector2.from_points((0, 3), (2, 5)) == Vector2(2, 2)


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
