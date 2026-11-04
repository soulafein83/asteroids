"""Tests for the W-D patch: hyperspace TTL logic moved from Ship.draw() to Ship.move() (W-5)."""
from ship import Ship


def _enter_hyperspace(ship):
    # The first draw initialises transformedPointlist, exactly as in the
    # game loop (draw is called every frame).
    ship.draw()
    ship.enterHyperSpace()
    assert ship.inHyperSpace
    assert ship.hyperSpaceTtl == 100


def test_move_without_hyperspace_does_not_touch_ttl(game):
    ship = Ship(game.stage)
    assert not ship.inHyperSpace
    assert not hasattr(ship, "hyperSpaceTtl"), \
        "ttl must only exist during hyperspace"
    ship.move()
    assert not hasattr(ship, "hyperSpaceTtl")


def test_draw_is_pure(game):
    # W-5: draw() must not decrement the TTL — game logic lives in move().
    ship = Ship(game.stage)
    _enter_hyperspace(ship)
    for _ in range(50):
        ship.draw()
    assert ship.hyperSpaceTtl == 100, \
        "draw() must not decrement ttl, got %d" % ship.hyperSpaceTtl
    assert ship.inHyperSpace


def test_teleport_after_exactly_100_moves(game):
    # W-5: the countdown and re-entry teleport happen in move(), without
    # any draw() call in between.
    ship = Ship(game.stage)
    _enter_hyperspace(ship)
    for _ in range(99):
        ship.move()
    assert ship.inHyperSpace
    assert ship.hyperSpaceTtl == 1
    ship.move()  # 100th move: teleport happens here, without draw()
    assert not ship.inHyperSpace
    assert ship.color == (255, 255, 255), \
        "ship must reset to white, got %r" % (ship.color,)
    assert ship.thrustJet.color == (255, 255, 255)
    w, h = game.stage.width, game.stage.height
    assert 0 <= ship.position.x < w
    assert 0 <= ship.position.y < h
    assert ship.thrustJet.position.x == ship.position.x
    assert ship.thrustJet.position.y == ship.position.y


def test_draw_after_teleport_renders_ship(game):
    ship = Ship(game.stage)
    _enter_hyperspace(ship)
    for _ in range(100):
        ship.move()
    result = ship.draw()
    assert result is not None and len(result) == 5


def test_second_hyperspace_cycle(game):
    # The entry guard is idempotent and a full second cycle works.
    ship = Ship(game.stage)
    _enter_hyperspace(ship)
    for _ in range(100):
        ship.move()
    assert not ship.inHyperSpace

    _enter_hyperspace(ship)
    ship.enterHyperSpace()  # second call must be a no-op
    assert ship.hyperSpaceTtl == 100
    for _ in range(100):
        ship.move()
    assert not ship.inHyperSpace
