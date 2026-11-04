"""Shared pytest setup: headless SDL, src/ on sys.path, one fresh game per test."""
import os
import sys
from pathlib import Path

# Must be set before pygame is imported anywhere.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# The game runs from src/; make it importable from the test suite.
_SRC = str(Path(__file__).resolve().parent.parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pytest  # noqa: E402
import pygame  # noqa: E402

import asteroids  # noqa: E402
from soundManager import initSoundManager  # noqa: E402

initSoundManager()  # once per session, before any game is created


@pytest.fixture()
def game():
    """A fresh game, as if the player had just started a new one."""
    g = asteroids.Asteroids()
    g.initialiseGame()
    return g
