# Tests for the M-C slice (M-4: instance maxBullets, M-5: fresh
# thrustJet.ship binding on respawn).

from shooter import Shooter
from badies import Saucer


def test_saucer_max_bullets_is_instance_attribute(game):
    # M-4: no shared mutable class state on Saucer.
    assert not hasattr(Saucer, "maxBullets")

    saucer = Saucer(game.stage, Saucer.smallSaucerType, game.ship)
    assert saucer.maxBullets == 1
    # per-instance value — changing one saucer must not touch others
    other = Saucer(game.stage, Saucer.largeSaucerType, game.ship)
    other.maxBullets = 2
    assert saucer.maxBullets == 1


def test_saucer_respects_max_bullets(game):
    # Behavioural regression: with maxBullets == 1 a second shot is
    # refused until the first bullet expires (W-6 behaviour kept).
    saucer = Saucer(game.stage, Saucer.smallSaucerType, game.ship)
    heading = saucer.heading
    assert Shooter.fireBullet(saucer, heading, 60, 5) is True
    assert len(saucer.bullets) == 1
    assert Shooter.fireBullet(saucer, heading, 60, 5) is None
    assert len(saucer.bullets) == 1


def test_new_ship_thrustjet_bound_to_new_ship(game):
    # M-5: after createNewShip the active thrust jet must reference the
    # NEW ship, never a stale one.
    old = game.ship
    game.createNewShip()
    assert game.ship is not old
    assert game.ship.thrustJet.ship is game.ship


def test_thrustjet_follows_new_ship_after_explosion_flow(game):
    # Simulate the respawn path (killShip removes old sprites, then
    # exploding() -> createNewShip). The new jet is bound to the new
    # ship and the old jet is no longer on the stage.
    old = game.ship
    old_jet = old.thrustJet
    game.stage.removeSprite(old)
    game.stage.removeSprite(old_jet)
    game.createNewShip()
    assert game.ship is not old
    assert game.ship.thrustJet is not old_jet
    assert game.ship.thrustJet.ship is game.ship
    assert old_jet not in game.stage.spriteList
