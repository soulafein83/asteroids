# Tests for the M-E slice (M-1: font and text-surface caching).
#
# Before M-E every display method built fresh Font objects and rendered
# its text on every frame.  Now static texts are surfaces rendered once
# in __init__, and the dynamic ones (score, FPS) reuse cached Font
# objects.  These tests pin that down with a Font-construction spy.

import pygame


def test_static_text_surfaces_cached(game):
    # M-1: the attract-screen and pause texts are rendered once at
    # init and stored as surfaces.
    assert game.titleSurface.get_width() > 0
    assert game.copyrightSurface.get_width() > 0
    assert game.instructionSurface.get_width() > 0
    assert game.pausedSurface.get_width() > 0


def test_cached_fonts_exist_once_per_size(game):
    # One Font per size, shared by the display methods.
    sizes = {15, 20, 30, 50}
    assert set(game.fonts.keys()) == sizes
    fonts = list(game.fonts.values())
    # each entry is a real pygame Font object
    assert all(isinstance(f, pygame.font.Font) for f in fonts)


def test_display_methods_do_not_create_fonts(game, monkeypatch):
    # No display method may construct a Font per frame: they must
    # blit the cached static surfaces and reuse the cached fonts.
    created = []
    original_font = pygame.font.Font

    def spy_font(*args, **kwargs):
        created.append(args)
        return original_font(*args, **kwargs)

    monkeypatch.setattr(pygame.font, "Font", spy_font)

    game.displayText()
    game.displayScore()
    game.paused = True
    game.displayPaused()
    game.paused = False
    # fps is normally initialised in playGame before displayFps runs.
    game.fps = 0
    game.displayFps()

    assert created == []


def test_display_methods_still_blit(game):
    # Behavioural regression: the display methods must still draw onto
    # the stage screen (dummy driver, so just exercise the paths).
    game.displayText()
    game.displayScore()
    game.paused = True
    game.displayPaused()
    game.paused = False
    # fps is normally initialised in playGame before displayFps runs.
    game.fps = 0
    game.displayFps()
