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
from pygame.locals import *


class Stage:

    # Set up the PyGame surface
    def __init__(self, caption, dimensions=None, fullscreen=False):
        pygame.init()

        # If no screen size is provided pick the first available mode
        if dimensions is None:
            dimensions = pygame.display.list_modes()[0]

        # Windowed by default; pass fullscreen=True (or use the F key at
        # runtime) for fullscreen.
        pygame.display.set_mode(dimensions, FULLSCREEN if fullscreen else 0)
        pygame.mouse.set_visible(not fullscreen)

        pygame.display.set_caption(caption)
        self.screen = pygame.display.get_surface()
        self.spriteList = []
        self.width = dimensions[0]
        self.height = dimensions[1]
        self.showBoundingBoxes = False

    # Add sprite to list, then build its initial bounding rect WITHOUT the
    # side effect of draw(): refresh the transform in place and take a
    # strict point AABB from the transformed pointlist (M-2).  The first
    # drawSprites() pass will render it as usual.
    def addSprite(self, sprite):
        self.spriteList.append(sprite)
        sprite.rotateAndTransform()
        xs = [p[0] for p in sprite.transformedPointlist]
        ys = [p[1] for p in sprite.transformedPointlist]
        sprite.boundingRect = pygame.Rect(
            min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def removeSprite(self, sprite):
        self.spriteList.remove(sprite)

    def drawSprites(self):
        for sprite in self.spriteList:
            sprite.boundingRect = pygame.draw.aalines(
                self.screen, sprite.color, True, sprite.draw())
            if self.showBoundingBoxes == True:
                pygame.draw.rect(self.screen, (255, 255, 255),
                                 sprite.boundingRect, 1)

    def moveSprites(self):
        for sprite in self.spriteList:
            sprite.move()

            if sprite.position.x < 0:
                sprite.position.x = self.width

            if sprite.position.x > self.width:
                sprite.position.x = 0

            if sprite.position.y < 0:
                sprite.position.y = self.height

            if sprite.position.y > self.height:
                sprite.position.y = 0
