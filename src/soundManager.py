#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Copyright (C) 2008  Nick Redshaw
#    Copyright (C) 2018  Francisco Sanchez Arroyo
#

import pygame
import sys
import os
import random
from pygame.locals import *
from util import RES_DIR

sounds = {}  # create empty dictionary of sounds
sound_available = True


def initSoundManager():
    global sound_available
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        sounds["fire"] = pygame.mixer.Sound(os.path.join(RES_DIR, "FIRE.WAV"))
        sounds["explode1"] = pygame.mixer.Sound(os.path.join(RES_DIR, "EXPLODE1.WAV"))
        sounds["explode2"] = pygame.mixer.Sound(os.path.join(RES_DIR, "EXPLODE2.WAV"))
        sounds["explode3"] = pygame.mixer.Sound(os.path.join(RES_DIR, "EXPLODE3.WAV"))
        sounds["lsaucer"] = pygame.mixer.Sound(os.path.join(RES_DIR, "LSAUCER.WAV"))
        sounds["ssaucer"] = pygame.mixer.Sound(os.path.join(RES_DIR, "SSAUCER.WAV"))
        sounds["thrust"] = pygame.mixer.Sound(os.path.join(RES_DIR, "THRUST.WAV"))
        sounds["sfire"] = pygame.mixer.Sound(os.path.join(RES_DIR, "SFIRE.WAV"))
        sounds["extralife"] = pygame.mixer.Sound(os.path.join(RES_DIR, "LIFE.WAV"))
    except (pygame.error, FileNotFoundError) as e:
        print('Warning, sound disabled:', e)
        sounds.clear()
        sound_available = False


def playSound(soundName):
    if sound_available:
        sounds[soundName].play()


def playSoundContinuous(soundName):
    if sound_available:
        sounds[soundName].play(-1)


def stopSound(soundName):
    if sound_available:
        sounds[soundName].stop()
