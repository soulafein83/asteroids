# Tests for the P-1 slice (src/item.py: PowerUp power-up sprites).
#
# A PowerUp is a drifting letter (E/R/S) dropped by destroyed rocks.
# It lives for 900 frames, blinks during the last 120, and removes
# itself from the stage when it expires.  Screen wraparound comes from
# the stage, like every other sprite.

import math
import random

import pygame

from util.vector2d import Vector2d
from enemies import Rock
from item import PowerUp


class _FakeFont:
    # Deterministic stand-in for the Hyperspace font: counts render
    # calls and returns a tiny surface (blink logic is what's tested).
    def __init__(self):
        self.render_calls = 0

    def render(self, text, antialias, color):
        self.render_calls += 1
        return pygame.Surface((2, 2))


def test_powerup_creation(game):
    pu = PowerUp(game.stage, Vector2d(100, 100), "E")
    assert pu.letter == "E"
    assert pu.ttl == 900
    assert pu.position.x == 100
    assert pu.position.y == 100
    speed = math.hypot(pu.heading.x, pu.heading.y)
    # slow drift: clearly slower than a ship under thrust
    assert 0 < speed <= 1.5


def test_powerup_move_decrements_ttl(game):
    pu = PowerUp(game.stage, Vector2d(100, 100), "S")
    game.stage.addSprite(pu)
    pu.move()
    assert pu.ttl == 899


def test_powerup_removes_itself_when_expired(game):
    pu = PowerUp(game.stage, Vector2d(100, 100), "R")
    game.stage.addSprite(pu)
    pu.ttl = 1
    pu.move()
    assert pu.ttl == 0
    assert pu not in game.stage.spriteList


def test_expired_powerup_move_does_not_raise(game):
    # Double expiry must be a no-op (mirrors the Bullet guard): a stale
    # frame must never raise ValueError from removeSprite.
    pu = PowerUp(game.stage, Vector2d(100, 100), "S")
    game.stage.addSprite(pu)
    pu.ttl = 0
    pu.move()
    pu.move()
    assert pu not in game.stage.spriteList


def test_powerup_wraps_with_stage(game):
    pu = PowerUp(game.stage, Vector2d(game.stage.width - 2, 50), "E")
    pu.heading = Vector2d(5, 0)  # deterministic override
    game.stage.addSprite(pu)
    game.stage.moveSprites()
    assert pu.position.x == 0


def test_powerup_has_small_bounding_rect(game):
    # The letter is rendered as text; the collision rect stays tiny
    # (pickup is "ship covers the item", like bullets work today).
    pu = PowerUp(game.stage, Vector2d(100, 100), "E")
    game.stage.addSprite(pu)
    assert pu.boundingRect.width <= 2
    assert pu.boundingRect.height <= 2


def test_powerup_draw_blinks_when_about_to_expire(game):
    pu = PowerUp(game.stage, Vector2d(100, 100), "E")
    game.stage.addSprite(pu)
    game.stage.screen.fill((10, 10, 10))
    pu.font = _FakeFont()

    pu.ttl = 900
    pu.draw()
    assert pu.font.render_calls == 1  # fully visible

    pu.ttl = 119
    pu.draw()
    assert pu.font.render_calls == 2  # odd TTL inside blink window: shown

    pu.ttl = 118
    pu.draw()
    assert pu.font.render_calls == 2  # even TTL: hidden (blink off)


# ---------------------------------------------------------------------
# P-2: power-up spawning from destroyed rocks
# ---------------------------------------------------------------------

def _force_spawn_roll(monkeypatch):
    # Win the 10% roll and deterministically pick the letter "S".
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.05)
    monkeypatch.setattr(random, "choice", lambda seq: "S")


def test_initialise_game_starts_with_empty_power_up_list(game):
    assert game.powerUpList == []


def test_initialise_game_clears_power_ups(game):
    pu = PowerUp(game.stage, Vector2d(100, 100), "S")
    game.stage.addSprite(pu)
    game.powerUpList.append(pu)

    game.initialiseGame()

    assert game.powerUpList == []
    assert pu not in game.stage.spriteList


def test_maybe_spawn_power_up_on_win(game, monkeypatch):
    _force_spawn_roll(monkeypatch)
    game.maybeSpawnPowerUp(Vector2d(50, 50))
    assert len(game.powerUpList) == 1
    pu = game.powerUpList[0]
    assert pu.letter == "S"
    assert pu in game.stage.spriteList


def test_maybe_spawn_power_up_on_loss(game, monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.99)
    game.maybeSpawnPowerUp(Vector2d(50, 50))
    assert game.powerUpList == []


def test_spawn_is_capped_at_three(game, monkeypatch):
    for letter in "ERS":
        pu = PowerUp(game.stage, Vector2d(100, 100), letter)
        game.stage.addSprite(pu)
        game.powerUpList.append(pu)

    _force_spawn_roll(monkeypatch)
    game.maybeSpawnPowerUp(Vector2d(200, 200))

    assert len(game.powerUpList) == 3


def test_destroyed_rock_can_spawn_power_up(game, monkeypatch):
    # Deterministic setup: clear the fixture's random rocks and place a
    # single large rock in the ship's firing line.
    for r in list(game.rockList):
        game.stage.removeSprite(r)
    game.rockList.clear()

    ship = game.ship
    ship.position.x = 100
    ship.position.y = 100
    ship.angle = -90  # fires straight right: heading (13, 0)

    rock = Rock(game.stage, Vector2d(200, 100), Rock.largeRockType)
    game.stage.addSprite(rock)
    game.rockList.append(rock)

    ship.fireBullet()
    b = ship.bullets[-1]
    for _ in range(6):  # 6 * 13 = 78 -> bullet at x=178, inside the rock
        b.move()
    game.stage.drawSprites()

    _force_spawn_roll(monkeypatch)
    game.checkCollisions()

    assert rock not in game.rockList
    assert len(game.powerUpList) == 1
    assert game.powerUpList[0] in game.stage.spriteList
