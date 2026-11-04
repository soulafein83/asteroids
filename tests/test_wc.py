"""Tests for the W-C patch: per-instance rock shapes (W-4), debris clamp (W-9), saucer flight (W-6)."""
import math
import random

from enemies import Rock, Debris, Saucer
from ship import Ship
from util.vectorsprites import Vector2d


def test_rock_shapes_are_per_instance(game, monkeypatch):
    # W-4: no shared class-level rockShape; each rock picks its own shape.
    assert not hasattr(Rock, "rockShape"), \
        "class-level rockShape must be gone (state moved to instances)"
    assert isinstance(Rock.rockShapes, tuple) and len(Rock.rockShapes) == 4

    stage = game.stage
    # Deterministic coverage: the first four rocks are forced to draw shapes
    # 1..4 in order, so the test cannot depend on luck (20 random draws miss
    # a bucket ~1% of the time). Once the forced draws are exhausted, fall
    # back to the real random number generator for the remaining rocks.
    orig_randint = random.randint
    draws = iter([1, 2, 3, 4])

    def forced(a, b):
        try:
            return next(draws)
        except StopIteration:
            return orig_randint(a, b)

    monkeypatch.setattr(random, "randint", forced)
    rocks = [Rock(stage, Vector2d(50, 50), Rock.largeRockType) for _ in range(4)]
    for expected, r in zip(range(1, 5), rocks):
        assert r.rockShape == expected, \
            "forced draw %d produced rockShape %r" % (expected, r.rockShape)
        assert r.createPointList() == Rock.rockShapes[r.rockShape - 1]
    # ... and free (unpatched) random draws always stay within 1..4
    rocks = [Rock(stage, Vector2d(50, 50), Rock.largeRockType) for _ in range(20)]
    for r in rocks:
        assert 1 <= r.rockShape <= 4, "bad rockShape %r" % r.rockShape
        assert r.createPointList() == Rock.rockShapes[r.rockShape - 1]

    # clamping: out-of-range shapes resolve instead of crashing
    probe = rocks[0]
    probe.rockShape = 5
    assert probe.createPointList() == Rock.rockShapes[3]
    probe.rockShape = 0
    assert probe.createPointList() == Rock.rockShapes[0]
    probe.rockShape = 2
    assert probe.createPointList() == Rock.rockShapes[1]


def test_debris_fade_clamps_at_black(game):
    # W-9: the fade can never drive a color channel negative.
    stage = game.stage
    d = Debris(Vector2d(100, 100), stage)
    d.color = (10, 5, 0)
    for _ in range(3):
        d.move()
        assert all(c >= 0 for c in d.color), "negative color: %r" % (d.color,)
    assert d.color == (0, 0, 0), "fade must clamp at black, got %r" % (d.color,)
    for _ in range(5):
        d.move()
    assert d.color == (0, 0, 0)


def test_saucer_flies_flat_and_respects_safe_zone(game):
    # W-6: flat trajectory; during the ship's safe zone the saucer never fires.
    stage = game.stage
    ship = Ship(stage)  # fresh ship: respawnTimer == 180
    assert ship.respawnTimer == 180

    saucer = Saucer(stage, Saucer.largeSaucerType, ship)
    saucer.position.x = 100.0
    saucer.position.y = 100.0
    start_x = saucer.position.x

    # 60 frames: the timer must tick, but the ship is in its safe zone.
    for _ in range(60):
        saucer.move()
    assert len(saucer.bullets) == 0, \
        "saucer must not fire during the safe zone, fired %d" % len(saucer.bullets)
    assert 0 < saucer.shootTimer <= 60, \
        "shootTimer must be ticking in (0, 60], got %d" % saucer.shootTimer
    # and it flew flat the whole way
    assert abs(saucer.position.y - 100.0) < 1e-6, \
        "saucer must fly flat, y drifted to %r" % saucer.position.y
    assert saucer.position.x > start_x + 60 * 1.0, \
        "saucer must keep moving right"


def test_saucer_due_shot_is_aimed(game):
    # W-6: once the ship is vulnerable, a due timer fires exactly once,
    # aimed at the ship from the saucer's post-move position.
    stage = game.stage
    ship = Ship(stage)
    ship.respawnTimer = 0

    saucer = Saucer(stage, Saucer.largeSaucerType, ship)
    saucer.shootTimer = 1
    saucer.move()
    assert len(saucer.bullets) == 1, "due shot must fire"
    assert 30 <= saucer.shootTimer <= 60, "timer must re-arm to 30-60"

    sx, sy = saucer.position.x, saucer.position.y
    b = saucer.bullets[0]
    dx = ship.position.x - sx
    dy = ship.position.y - sy
    mag = math.hypot(dx, dy)
    assert abs(b.heading.x - Saucer.bulletVelocity * dx / mag) < 1e-3
    assert abs(b.heading.y - Saucer.bulletVelocity * dy / mag) < 1e-3


def test_saucer_respects_max_bullets(game):
    # W-6: maxBullets == 1 — a second due move must not add a second bullet.
    stage = game.stage
    ship = Ship(stage)
    ship.respawnTimer = 0

    saucer = Saucer(stage, Saucer.largeSaucerType, ship)
    saucer.shootTimer = 1
    saucer.move()
    assert len(saucer.bullets) == 1
    saucer.shootTimer = 1
    saucer.move()
    assert len(saucer.bullets) == 1
