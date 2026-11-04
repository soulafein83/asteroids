"""Tests for the W-A patch: score display (W-1), lives handling (W-2, W-8)."""
import pygame

import asteroids
from asteroids import Asteroids


def test_import_does_not_start_game_loop():
    # Importing the module must not start the main loop; the ctor leaves
    # the game in an uninitialised state (W-8: lives start at 0).
    game = Asteroids()
    assert game.lives == 0


def test_lives_reset_on_new_game(game):
    # W-8: a new game must reset lives even if leftover state exists.
    game.lives = 7  # simulate leftover state
    game.initialiseGame()
    assert game.lives == 5, "lives after new game must be exactly 5"
    assert len(game.livesList) == 4  # 1 (start) + 4 (addLife) => 5 lives


def test_extra_lives_stay_on_screen(game):
    # W-2: the life-indicator row wraps; even 200 extra lives stay on screen.
    for i in range(1, 200):
        game.addLife(i)
    w = game.stage.width
    xs = [s.position.x for s in game.livesList]
    bad = [x for x in xs if x < -10 or x > w - 10]
    assert not bad, "off-screen life ships: %s" % bad[:5]


def test_score_display_padding(game, monkeypatch):
    # W-1: the score is zero-padded to 4 digits and capped at 99999.
    # Font is an immutable C type, so wrap the factory instead of the class.
    captured = []
    orig_Font = pygame.font.Font

    class SpyFont:
        def __init__(self, path, size):
            self._f = orig_Font(path, size)

        def render(self, text, *a, **k):
            captured.append(text)
            return self._f.render(text, *a, **k)

        def __getattr__(self, name):
            return getattr(self._f, name)

    monkeypatch.setattr(pygame.font, "Font", SpyFont)

    for score in (0, 7, 123, 4200, 99999, 250000):
        game.score = score
        captured.clear()
        game.displayScore()
        got = [t for t in captured if t.isdigit()]
        assert got, "displayScore rendered no numeric text"
        exp = "%04d" % min(score, 99999)
        assert got[0] == exp, "score %d -> %r, expected %r" % (score, got[0], exp)
