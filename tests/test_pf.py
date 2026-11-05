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
from enemies import Rock, Saucer
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


# ---------------------------------------------------------------------
# P-3: power-up pickup + shield (S)
# ---------------------------------------------------------------------

def _place_rock_crossing_ship(rock, ship, stage):
    # checkPolygonCollision is line-segment intersection, so the ship must
    # not sit fully inside the rock. Scan small offsets until the rock's
    # outline actually crosses the ship's.
    for dx in range(-20, 21):
        for dy in range(-20, 21):
            rock.position.x = ship.position.x + dx
            rock.position.y = ship.position.y + dy
            stage.drawSprites()
            if rock.collidesWith(ship) and \
                    rock.checkPolygonCollision(ship) is not None:
                return
    raise AssertionError("no crossing offset found")


def test_ship_starts_without_power_ups(game):
    ship = game.ship
    assert ship.shieldTimer == 0
    assert ship.extraBulletsTimer == 0
    assert ship.rapidFireTimer == 0
    assert ship.cooldownTimer == 0


def test_power_up_timers_decrement_and_clamp(game):
    ship = game.ship
    ship.shieldTimer = 600
    ship.extraBulletsTimer = 600
    ship.rapidFireTimer = 600
    ship.cooldownTimer = 5
    ship.move()
    assert ship.shieldTimer == 599
    assert ship.extraBulletsTimer == 599
    assert ship.rapidFireTimer == 599
    assert ship.cooldownTimer == 4

    # A zero timer must clamp, not go negative.
    for attr in ("shieldTimer", "extraBulletsTimer",
                 "rapidFireTimer", "cooldownTimer"):
        setattr(ship, attr, 0)
    ship.move()
    assert ship.shieldTimer == 0
    assert ship.extraBulletsTimer == 0
    assert ship.rapidFireTimer == 0
    assert ship.cooldownTimer == 0


def test_pickup_sets_shield_and_removes_power_up(game):
    ship = game.ship
    ship.respawnTimer = 0
    pu = PowerUp(game.stage,
                 Vector2d(ship.position.x, ship.position.y), "S")
    game.stage.addSprite(pu)
    game.powerUpList.append(pu)

    game.stage.drawSprites()
    game.checkCollisions()

    assert ship.shieldTimer == 600
    assert game.powerUpList == []
    assert pu not in game.stage.spriteList


def test_pickup_refreshes_shield_timer(game):
    # Picking up S again before expiry refreshes the timer to a full 600.
    ship = game.ship
    ship.shieldTimer = 100
    pu = PowerUp(game.stage,
                 Vector2d(ship.position.x, ship.position.y), "S")
    game.stage.addSprite(pu)
    game.powerUpList.append(pu)

    game.stage.drawSprites()
    game.checkCollisions()

    assert ship.shieldTimer == 600


def test_shield_protects_from_rock(game):
    ship = game.ship
    ship.respawnTimer = 0
    ship.shieldTimer = 600

    rock = Rock(game.stage,
                Vector2d(ship.position.x, ship.position.y),
                Rock.largeRockType)
    game.stage.addSprite(rock)
    game.rockList.append(rock)
    _place_rock_crossing_ship(rock, ship, game.stage)
    game.checkCollisions()

    assert game.gameState == 'playing', \
        "shielded ship must survive the rock, state=%s" % game.gameState
    assert game.lives == 5, "lives must stay 5, got %d" % game.lives
    assert rock in game.rockList


def test_shield_expires_and_ship_becomes_mortal(game):
    ship = game.ship
    ship.respawnTimer = 0
    ship.shieldTimer = 600

    rock = Rock(game.stage,
                Vector2d(ship.position.x, ship.position.y),
                Rock.largeRockType)
    game.stage.addSprite(rock)
    game.rockList.append(rock)
    _place_rock_crossing_ship(rock, ship, game.stage)

    # 599 moves: one frame of shield left -> still safe.
    for _ in range(599):
        ship.move()
    assert ship.shieldTimer == 1
    game.stage.drawSprites()
    game.checkCollisions()
    assert game.gameState == 'playing'

    # 600th move: shield gone -> the same rock now kills.
    ship.move()
    assert ship.shieldTimer == 0
    game.stage.drawSprites()
    game.checkCollisions()
    assert game.gameState == 'exploding'


def test_shield_protects_from_saucer(game):
    ship = game.ship
    ship.respawnTimer = 0
    ship.shieldTimer = 600

    saucer = Saucer(game.stage, Saucer.largeSaucerType, ship)
    saucer.position.x = ship.position.x
    saucer.position.y = ship.position.y
    game.stage.addSprite(saucer)
    game.saucer = saucer

    game.stage.drawSprites()
    game.checkCollisions()

    assert game.gameState == 'playing'
    assert game.saucer is saucer, \
        "a shielded ship must not destroy the saucer on contact"


def test_bullets_do_not_destroy_power_ups(game):
    # Classic: bullets pass through power-ups; only contact picks them up.
    ship = game.ship
    ship.position.x = 100
    ship.position.y = 100
    ship.angle = -90  # fires straight right

    pu = PowerUp(game.stage, Vector2d(150, 100), "E")
    game.stage.addSprite(pu)
    game.powerUpList.append(pu)

    ship.fireBullet()
    b = ship.bullets[-1]
    for _ in range(4):  # 4 * 13 = 52 -> bullet at x=152
        b.move()
    game.stage.drawSprites()
    game.checkCollisions()

    assert pu in game.powerUpList
    assert pu in game.stage.spriteList


def test_shield_draw_does_not_crash(game):
    ship = game.ship
    ship.shieldTimer = 600
    game.stage.screen.fill((10, 10, 10))
    ship.draw()


# ---------------------------------------------------------------------
# P-4: extra bullets (E) + rapid fire (R) + baseline fire cooldown
# ---------------------------------------------------------------------

def test_ship_baseline_max_bullets_and_cooldown(game):
    ship = game.ship
    assert ship.maxBullets == 4
    assert ship.fireCooldown == 10


def test_successful_shot_sets_cooldown_timer(game):
    ship = game.ship
    assert ship.cooldownTimer == 0

    ship.fireBullet()

    assert len(ship.bullets) == 1
    assert ship.cooldownTimer == 10  # baseFireCooldown


def test_cannot_fire_during_cooldown(game):
    ship = game.ship
    ship.cooldownTimer = 5

    ship.fireBullet()

    assert len(ship.bullets) == 0


def test_cooldown_counts_down_and_allows_next_shot(game):
    ship = game.ship
    ship.fireBullet()

    for _ in range(10):
        ship.move()

    assert ship.cooldownTimer == 0
    ship.fireBullet()
    assert len(ship.bullets) == 2


def test_pickup_E_and_R_arm_their_timers(game):
    ship = game.ship
    for letter in "ER":
        pu = PowerUp(game.stage,
                     Vector2d(ship.position.x, ship.position.y), letter)
        game.stage.addSprite(pu)
        game.powerUpList.append(pu)

        game.stage.drawSprites()
        game.checkCollisions()

    assert ship.extraBulletsTimer == 600
    assert ship.rapidFireTimer == 600
    assert game.powerUpList == []


def test_extra_bullets_doubles_max_bullets_for_600_frames(game):
    ship = game.ship
    ship.extraBulletsTimer = 600
    assert ship.maxBullets == 8

    for _ in range(600):
        ship.move()

    assert ship.extraBulletsTimer == 0
    assert ship.maxBullets == 4


def test_rapid_fire_shrinks_cooldown_for_600_frames(game):
    ship = game.ship
    ship.rapidFireTimer = 600
    assert ship.fireCooldown == 3

    ship.fireBullet()
    assert ship.cooldownTimer == 3

    for _ in range(600):
        ship.move()

    assert ship.rapidFireTimer == 0
    assert ship.fireCooldown == 10


def test_ship_respects_max_bullets_while_E_active(game):
    # Shooter.fireBullet must honour the live (property) maxBullets:
    # with E active the cap is 8, and it must still refuse beyond that.
    ship = game.ship
    ship.extraBulletsTimer = 600

    for _ in range(10):
        ship.cooldownTimer = 0
        ship.fireBullet()

    assert len(ship.bullets) == 8


# ---------------------------------------------------------------------
# P-5: HUD of active power-ups
# ---------------------------------------------------------------------

def _pixels(surface):
    # Pixel list of a surface (the test suite has no numpy).
    return [surface.get_at((x, y))
            for x in range(surface.get_width())
            for y in range(surface.get_height())]


def test_hud_surfaces_are_cached_in_init(game):
    # M-1: the E/R/S/B letter surfaces are pre-rendered once in __init__ —
    # a bright variant (effect active) and a dim one (inactive).
    assert set(game.powerUpSurfaces) == set("ERBS")
    for letter in "ERBS":
        bright, dim = game.powerUpSurfaces[letter]
        assert isinstance(bright, pygame.Surface)
        assert isinstance(dim, pygame.Surface)
        assert _pixels(bright) != _pixels(dim)


def test_display_power_ups_does_not_crash_in_any_timer_state(game):
    ship = game.ship
    for e, r, s in ((0, 0, 0), (600, 0, 0), (0, 600, 0), (0, 0, 600),
                    (1, 1, 1), (600, 600, 600)):
        ship.extraBulletsTimer = e
        ship.rapidFireTimer = r
        ship.shieldTimer = s
        game.stage.screen.fill((10, 10, 10))
        game.displayPowerUps()


def test_hud_letters_are_bright_only_while_active(game):
    # With no effects the top-right corner holds only dim letters (the
    # font blits with per-pixel alpha, so the dim 80,80,80 colour blends
    # down); with all effects active the same corner reaches the bright
    # 255,255,255 colour.  A HUD that ignores the timers renders the
    # same image in both states and fails here.
    stage = game.stage
    ship = game.ship

    def top_right_max_brightness():
        stage.screen.fill((10, 10, 10))
        game.displayPowerUps()
        region = stage.screen.subsurface(
            (stage.width - 100, 0, 100, 40))
        return max(p.r for x in range(region.get_width())
                   for y in range(region.get_height())
                   for p in [region.get_at((x, y))])

    ship.extraBulletsTimer = 0
    ship.rapidFireTimer = 0
    ship.shieldTimer = 0
    dim = top_right_max_brightness()
    assert dim < 100

    ship.extraBulletsTimer = 600
    ship.rapidFireTimer = 600
    ship.shieldTimer = 600
    bright = top_right_max_brightness()
    assert bright > 120


def test_display_power_ups_only_blits_cached_surfaces(game):
    # The M-1 contract: displayPowerUps blits only the surfaces
    # pre-rendered in __init__ (identity-checked) — no font rendering
    # per frame.
    cached = [s for pair in game.powerUpSurfaces.values() for s in pair]
    real_screen = game.stage.screen

    class _RecordingScreen:
        def __init__(self):
            self.blitted = []

        def blit(self, surface, rect):
            self.blitted.append(surface)
            return rect

    recording = _RecordingScreen()
    game.stage.screen = recording
    try:
        for _ in range(3):
            game.displayPowerUps()
    finally:
        game.stage.screen = real_screen

    assert len(recording.blitted) == 12  # 4 letters x 3 frames
    for surface in recording.blitted:
        assert any(surface is c for c in cached)


def test_display_power_ups_is_called_in_game_loop(game):
    # The main loop must draw the HUD every frame in the playing state.
    # playGame() runs synchronously here and is stopped from inside by an
    # input() guard after a few frames (a QUIT event would sys.exit and
    # tear down the shared pygame state of the test session).
    calls = []
    game.displayPowerUps = lambda: calls.append(1)

    class _StopLoop(Exception):
        pass

    real_input = game.input
    frames = {"n": 0}

    def limited_input(events):
        frames["n"] += 1
        if frames["n"] > 30:
            raise _StopLoop
        return real_input(events)

    game.input = limited_input
    try:
        game.playGame()
        raise AssertionError("playGame should have been stopped")
    except _StopLoop:
        pass

    assert frames["n"] > 30
    assert len(calls) == 30


# ---------------------------------------------------------------------
# Q-1: the B (bomb) letter in the power-up pool and the HUD
# ---------------------------------------------------------------------

def test_B_is_in_pool_and_has_cached_surfaces(game):
    # B joins the pool (uniform 1/4 spawn chance) and gets a cached
    # bright/dim HUD surface pair like E/R/S.
    assert "B" in game.powerUpLetters
    assert set(game.powerUpSurfaces) == set("ERBS")
    bright, dim = game.powerUpSurfaces["B"]
    assert _pixels(bright) != _pixels(dim)


def test_spawn_can_produce_B(game, monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.0)
    monkeypatch.setattr(random, "choice", lambda seq: "B")
    game.maybeSpawnPowerUp(Vector2d(100, 100))
    assert len(game.powerUpList) == 1
    assert game.powerUpList[0].letter == "B"


def test_pickup_B_is_removed_without_ship_effect(game):
    # Q-1: B is picked up and removed from the stage; no ship timer
    # changes (the bomb effect itself arrives in Q-2).  The flash
    # timer exists from Q-1 and stays at 0.
    for r in list(game.rockList):
        game.stage.removeSprite(r)
    game.rockList.clear()

    ship = game.ship
    pu = PowerUp(game.stage,
                 Vector2d(ship.position.x, ship.position.y), "B")
    game.stage.addSprite(pu)
    game.powerUpList.append(pu)

    game.checkCollisions()

    assert pu not in game.powerUpList
    assert pu not in game.stage.spriteList
    assert ship.extraBulletsTimer == 0
    assert ship.rapidFireTimer == 0
    assert ship.shieldTimer == 0
    assert game.bombFlashTimer == 0
