# Tests for M-B / M-6: Vector2d arithmetic operators.

from util.vector2d import Vector2d


def test_add_returns_new_vector_and_does_not_mutate():
    a = Vector2d(1, 2)
    b = Vector2d(3, 4)
    c = a + b
    assert c == Vector2d(4, 6)
    assert c is not a and c is not b
    # operands untouched
    assert a == Vector2d(1, 2)
    assert b == Vector2d(3, 4)


def test_sub_returns_new_vector():
    a = Vector2d(5, 7)
    b = Vector2d(2, 3)
    assert a - b == Vector2d(3, 4)


def test_mul_scalar_and_rmul():
    v = Vector2d(2, -3)
    assert v * 4 == Vector2d(8, -12)
    assert 4 * v == Vector2d(8, -12)
    # original untouched
    assert v == Vector2d(2, -3)


def test_mul_with_float_scalar():
    v = Vector2d(1, 2)
    assert v * 0.5 == Vector2d(0.5, 1.0)


def test_eq_and_ne():
    assert Vector2d(1, 2) == Vector2d(1, 2)
    assert Vector2d(1, 2) != Vector2d(1, 3)
    assert Vector2d(0, 0) == Vector2d(0.0, 0.0)  # numeric equality
    # equality must not be claimed against unrelated types
    assert (Vector2d(1, 2) == (1, 2)) is False
    assert (Vector2d(1, 2) == "vector") is False


def test_repr():
    assert repr(Vector2d(1, 2)) == "Vector2d(x=1, y=2)"


def test_magnitude():
    assert Vector2d(3, 4).magnitude() == 5
    assert Vector2d(0, 0).magnitude() == 0
    assert Vector2d(-3, 4).magnitude() == 5
    assert Vector2d(1, 1).magnitude() == 2 ** 0.5


def test_game_ship_heading_operators(game):
    # The game's own Vector2d instances must support the new operators
    # end-to-end (position/heading are Vector2d objects).
    ship = game.ship
    p0 = Vector2d(ship.position.x, ship.position.y)
    p1 = ship.position + Vector2d(10, 0)
    assert p1.x == p0.x + 10 and p1.y == p0.y
    # ship position itself is untouched by the operator
    assert ship.position == p0
