# Tests for the M-A cleanup slice (M-7, M-8, M-9, M-11, M-12).
#
# M-9 is the only behavioural change here: the bare `except:` in
# calculateIntersectPoint was narrowed to (TypeError, ValueError,
# OverflowError).  These tests pin that down: invalid-point errors are
# still swallowed (and logged), but unrelated exceptions must propagate.

import pytest

from util import geometry
from util.geometry import calculateIntersectPoint


def _fake_rect(exc_type):
    # Stand-in for pygame.Rect: pygame-ce's Rect is a C extension type,
    # so its methods can't be monkeypatched directly.
    class FakeRect:
        def __init__(self, *args, **kwargs):
            self.width = 10
            self.height = 10

        def normalize(self):
            pass

        def collidepoint(self, point):
            raise exc_type("simulated pygame Rect overflow")

    return FakeRect


def _crossing():
    # Two short segments that genuinely cross inside both bounding boxes.
    p1 = (0, 0)
    p2 = (10, 10)
    p3 = (0, 10)
    p4 = (10, 0)
    return p1, p2, p3, p4


def test_calculate_intersect_point_returns_crossing_point():
    p1, p2, p3, p4 = _crossing()
    assert calculateIntersectPoint(p1, p2, p3, p4) == [5, 5]


def test_invalid_point_error_is_swallowed(monkeypatch):
    # Simulate "point value too large for Rect" by making collidepoint
    # raise one of the now-handled exception types.
    monkeypatch.setattr(geometry, "Rect", _fake_rect(TypeError))

    p1, p2, p3, p4 = _crossing()
    # Must not raise: the except catches TypeError and the function
    # falls through to its "segments didn't actually meet" return.
    assert calculateIntersectPoint(p1, p2, p3, p4) is None


@pytest.mark.parametrize("exc", (TypeError, ValueError, OverflowError))
def test_each_handled_exception_is_swallowed(monkeypatch, exc):
    monkeypatch.setattr(geometry, "Rect", _fake_rect(exc))

    p1, p2, p3, p4 = _crossing()
    assert calculateIntersectPoint(p1, p2, p3, p4) is None


def test_unrelated_exception_propagates(monkeypatch):
    # The narrowed except must NOT swallow programming errors such as
    # AttributeError or RuntimeError — a bare `except:` would hide them.
    monkeypatch.setattr(geometry, "Rect", _fake_rect(RuntimeError))

    p1, p2, p3, p4 = _crossing()
    with pytest.raises(RuntimeError):
        calculateIntersectPoint(p1, p2, p3, p4)


def test_ship_deceleration_attribute_name():
    # M-12: the class attribute was misspelled `decelaration`.
    from ship import Ship
    assert hasattr(Ship, "deceleration")
    assert not hasattr(Ship, "decelaration")


def test_ship_move_applies_deceleration(game):
    # Behaviour check for M-12: the rename to `deceleration` must not
    # break move() -> decreaseThrust(), which damps the heading by
    # heading * deceleration.
    ship = game.ship
    ship.position.x = 100
    ship.position.y = 100
    ship.heading.x = 1.0
    ship.heading.y = 0.0
    ship.move()
    # heading was damped by |deceleration| (0.005) along x, y unchanged.
    assert ship.heading.x == pytest.approx(0.995)
    assert ship.heading.y == 0.0
