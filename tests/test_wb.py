"""Tests for the W-B patch: collision safety zone (W-3, W-7), bullet removal (W-10)."""
from enemies import Rock, Saucer
from ship import Ship
from util.vectorsprites import Vector2d


def _find_crossing_offset(rock, ship, stage):
    # checkPolygonCollision is line-segment intersection, so the ship must
    # not sit fully inside the rock (then it returns None). Scan small
    # offsets until the rock's outline actually crosses the ship's.
    for dx in range(-20, 21):
        for dy in range(-20, 21):
            rock.position.x = ship.position.x + dx
            rock.position.y = ship.position.y + dy
            stage.drawSprites()
            if rock.collidesWith(ship) and \
                    rock.checkPolygonCollision(ship) is not None:
                return dx, dy
    raise AssertionError("no crossing offset found")


def test_fresh_ship_starts_in_safe_zone(game):
    # W-7: a freshly created ship is invulnerable for 180 frames.
    assert game.ship is not None
    assert game.ship.respawnTimer == 180, \
        "fresh ship must start with respawnTimer == 180"


def test_safe_zone_shields_then_expiry_explodes(game):
    # (a) W-3/W-7: a rock whose edge crosses the ship must not kill it
    # while the respawn safe zone is active...
    rock = Rock(game.stage,
                Vector2d(game.ship.position.x, game.ship.position.y),
                Rock.largeRockType)
    game.stage.addSprite(rock)
    game.rockList.append(rock)
    _find_crossing_offset(rock, game.ship, game.stage)
    game.checkCollisions()
    assert game.gameState == 'playing', \
        "ship must survive rock while respawnTimer > 0, state=%s" % game.gameState
    assert game.lives == 5, "lives must stay 5 in safe zone"

    # ... but once the timer runs out, the same rock must kill the ship.
    game.ship.respawnTimer = 0
    game.stage.drawSprites()
    game.checkCollisions()
    assert game.gameState == 'exploding', \
        "timer expired -> ship must explode, state=%s" % game.gameState
    assert game.lives == 4, "lives must drop 5 -> 4"
    game.createNewShip()
    assert game.ship.respawnTimer == 180


def test_saucer_scored_exactly_once(game):
    # W-3: the saucer block runs once per frame, outside the rock loop, and
    # the score is credited exactly once.
    # Deterministic setup: clear the random rocks from the fixture.
    for r in list(game.rockList):
        game.stage.removeSprite(r)
    game.rockList.clear()

    ship = game.ship
    ship.position.x = 300
    ship.position.y = 400
    ship.angle = -90  # fires straight right: heading (13, 0)

    saucer = Saucer(game.stage, Saucer.largeSaucerType, game.ship)
    saucer.position.x = 400
    saucer.position.y = 400
    game.stage.addSprite(saucer)
    game.saucer = saucer

    ship.fireBullet()
    b = ship.bullets[-1]
    for _ in range(8):  # 8 * 13 = 104 px -> crosses the saucer at x=400
        b.move()
    game.stage.drawSprites()
    game.checkCollisions()
    assert game.saucer is None, "saucer must be destroyed"
    assert game.score == 500, "score must be exactly 500, got %d" % game.score


def test_bullet_remove_guard(game):
    # W-10: an expired bullet no longer in shooter.bullets must not raise
    # ValueError when it tries to remove itself.
    sh = Ship(game.stage)
    sh.fireBullet()
    assert len(sh.bullets) == 1
    b1 = sh.bullets[-1]
    b1.ttl = 0
    sh.bullets.remove(b1)  # already gone (e.g. removed by a hit handler)
    b1.move()  # must not raise ValueError
    assert b1 not in sh.bullets

    # ... and an expired bullet still in the list gets removed cleanly.
    sh.cooldownTimer = 0  # P-4: baseline fire cooldown; this test checks
    # the removal guard, not the fire rate
    sh.fireBullet()
    assert len(sh.bullets) == 1
    b2 = sh.bullets[-1]
    b2.ttl = 0
    n_before = len(sh.bullets)
    b2.move()
    assert b2 not in sh.bullets and len(sh.bullets) == n_before - 1


def test_respawn_timer_decrements_and_clamps(game):
    # W-7: the timer counts down over move() calls and clamps at zero.
    sh = Ship(game.stage)
    assert sh.respawnTimer == 180
    for _ in range(180):
        sh.move()
    assert sh.respawnTimer == 0, \
        "timer should reach 0 after 180 moves, got %d" % sh.respawnTimer
    sh.move()
    assert sh.respawnTimer == 0, "timer must not go negative"
