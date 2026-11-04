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

import math
import random

import pygame

from util.vector2d import Vector2d
from util.vectorsprites import Point, VectorSprite
from util import FONT_PATH


class PowerUp(Point):

    # Class attributes
    ttlFrames = 900   # ~15 s at 60 fps
    blinkTtl = 120    # start blinking (every other frame) at this TTL
    fontSize = 20

    def __init__(self, stage, position, letter):
        # Slow random drift so the letter floats instead of sitting still.
        speed = random.uniform(0.5, 1.5)
        direction = random.uniform(0, 2 * math.pi)
        heading = Vector2d(speed * math.cos(direction),
                          speed * math.sin(direction))
        Point.__init__(self, position, heading, stage)
        self.letter = letter
        self.ttl = self.ttlFrames
        self.font = pygame.font.Font(FONT_PATH, self.fontSize)

    def move(self):
        self.ttl -= 1
        if self.ttl <= 0:
            # Guard against an already-removed sprite (mirrors Bullet):
            # a stale frame must never raise ValueError.
            if self in self.stage.spriteList:
                self.stage.removeSprite(self)
            return

        # VectorSprite.move (not Point.move, which would decrement the
        # TTL a second time).
        VectorSprite.move(self)

    def draw(self):
        # Render the letter centred on the position.  During the last
        # blinkTtl frames it alternates every other frame (arcade blink).
        visible = self.ttl > self.blinkTtl or self.ttl % 2 != 0
        if visible:
            text = self.font.render(self.letter, True, self.color)
            textRect = text.get_rect(
                center=(int(self.position.x), int(self.position.y)))
            self.stage.screen.blit(text, textRect)

        # The inherited 1x1 pointlist keeps the collision rect tiny and
        # gives Stage.drawSprites() a valid pointlist to aalines.
        return Point.draw(self)
