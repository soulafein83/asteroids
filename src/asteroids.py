#!/usr/bin/env python3
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

# TODO
# safe area on new life
# sounds thump

# Notes:
# random.randrange returns an int
# random.uniform returns a float
# p for pause
# j for toggle showing FPS
# o for frame advance whilst paused

import pygame
import sys
import random
from pygame.locals import *
from util.vectorsprites import *
from ship import *
from stage import *
from enemies import *
from shooter import *
from item import *
from soundManager import *
from util import FONT_PATH


class Asteroids():

    explodingTtl = 180
    # Power-up spawning (P-2): a destroyed rock drops a power-up with a
    # small chance, capped at three on screen at once.  Q-1 adds B (bomb)
    # to the pool: uniform 1/4 spawn chance.
    maxPowerUps = 3
    powerUpChance = 0.1
    powerUpLetters = "ERBS"

    def __init__(self):
        self.stage = Stage('Atari Asteroids', (1024, 768))
        # M-1: build fonts and static text surfaces ONCE (they used to
        # be re-rendered on every frame); display methods blit these.
        self.fonts = {
            15: pygame.font.Font(FONT_PATH, 15),
            20: pygame.font.Font(FONT_PATH, 20),
            30: pygame.font.Font(FONT_PATH, 30),
            50: pygame.font.Font(FONT_PATH, 50),
        }
        self.titleSurface = self.fonts[50].render(
            'Asteroids', True, (180, 180, 180))
        self.copyrightSurface = self.fonts[20].render(
            '(C) 1979 Atari INC.', True, (255, 255, 255))
        self.instructionSurface = self.fonts[30].render(
            'Press start to Play', True, (200, 200, 200))
        self.pausedSurface = self.fonts[30].render(
            "Paused", True, (255, 255, 255))
        # P-5: HUD surfaces for the power-up letters, pre-rendered once
        # (M-1): bright while the effect is active, dim otherwise.
        self.powerUpSurfaces = {}
        for letter in self.powerUpLetters:
            self.powerUpSurfaces[letter] = (
                self.fonts[20].render(letter, True, (255, 255, 255)),
                self.fonts[20].render(letter, True, (80, 80, 80)))
        # Q-1: HUD flash for the bomb letter B — armed by the bomb pickup
        # (Q-2), read by displayPowerUps() from Q-1.
        self.bombFlashTimer = 0
        self.paused = False
        self.showingFPS = False
        self.frameAdvance = False
        self.gameState = "attract_mode"
        self.rockList = []
        self.powerUpList = []
        self.createRocks(3)
        self.saucer = None
        self.secondsCount = 1
        self.score = 0
        self.ship = None
        self.lives = 0

    def initialiseGame(self):
        self.gameState = 'playing'
        [self.stage.removeSprite(sprite)
         for sprite in self.rockList]  # clear old rocks
        [self.stage.removeSprite(sprite)
         for sprite in self.powerUpList]  # clear old power-ups
        if self.saucer is not None:
            self.killSaucer()
        # Reset the life counter so a new game always starts from a clean
        # state (extra lives from a previous run must not leak in).
        self.lives = 0
        self.startLives = 5
        self.createNewShip()
        self.createLivesList()
        self.score = 0
        self.rockList = []
        self.powerUpList = []
        self.bombFlashTimer = 0
        self.numRocks = 3
        self.nextLife = 10000

        self.createRocks(self.numRocks)
        self.secondsCount = 1

    def createNewShip(self):
        if self.ship:
            [self.stage.spriteList.remove(debris)
             for debris in self.ship.shipDebrisList]
        self.ship = Ship(self.stage)
        # M-5: make the jet's ship binding explicit so a jet can never
        # keep pointing at a stale ship (guards against jet reuse).
        self.ship.thrustJet.ship = self.ship
        self.stage.addSprite(self.ship.thrustJet)
        self.stage.addSprite(self.ship)

    def createLivesList(self):
        self.lives += 1
        self.livesList = []
        for i in range(1, self.startLives):
            self.addLife(i)

    def addLife(self, lifeNumber):
        self.lives += 1
        ship = Ship(self.stage)
        self.stage.addSprite(ship)
        # Wrap the slot index so a large number of lives never pushes the
        # displayed ships off the left edge of the screen.
        slots = max(1, self.stage.width // ship.boundingRect.width)
        slot = lifeNumber % slots
        ship.position.x = self.stage.width - \
            (slot * ship.boundingRect.width) - 10
        ship.position.y = 0 + ship.boundingRect.height
        self.livesList.append(ship)

    def createRocks(self, numRocks):
        for _ in range(0, numRocks):
            position = Vector2d(random.randrange(-10, 10),
                                random.randrange(-10, 10))

            newRock = Rock(self.stage, position, Rock.largeRockType)
            self.stage.addSprite(newRock)
            self.rockList.append(newRock)

    def maybeSpawnPowerUp(self, position):
        # A destroyed rock drops a power-up with a small chance.  The
        # roll is made before the cap check so losing rolls never
        # consume a slot; the cap keeps at most three on screen.
        if random.uniform(0, 1) >= self.powerUpChance:
            return
        if len(self.powerUpList) >= self.maxPowerUps:
            return
        letter = random.choice(self.powerUpLetters)
        powerUp = PowerUp(self.stage, position, letter)
        self.stage.addSprite(powerUp)
        self.powerUpList.append(powerUp)

    def playGame(self):

        clock = pygame.time.Clock()

        frameCount = 0
        timePassed = 0.0
        self.fps = 0.0
        # Main loop
        while True:

            # calculate fps
            timePassed += clock.tick(60)
            frameCount += 1
            if frameCount % 10 == 0:  # every 10 frames
                # nearest integer
                self.fps = round((frameCount / (timePassed / 1000.0)))
                # reset counter
                timePassed = 0
                frameCount = 0

            self.secondsCount += 1

            self.input(pygame.event.get())

            # pause
            if self.paused and not self.frameAdvance:
                self.displayPaused()
                continue

            self.stage.screen.fill((10, 10, 10))
            self.stage.moveSprites()
            self.stage.drawSprites()
            self.doSaucerLogic()
            self.displayScore()
            # P-5: HUD of the active power-ups.  Only in the playing
            # state — in attract mode there is no ship to show them for.
            if self.gameState == 'playing':
                self.displayPowerUps()
            if self.showingFPS:
                self.displayFps()  # for debug
            self.checkScore()

            # Process keys
            if self.gameState == 'playing':
                self.playing()
            elif self.gameState == 'exploding':
                self.exploding()
            else:
                self.displayText()

            # Double buffer draw
            pygame.display.flip()

    def playing(self):
        if self.lives == 0:
            self.gameState = 'attract_mode'
        else:
            self.processKeys()
            self.checkCollisions()
            if len(self.rockList) == 0:
                self.levelUp()

    def doSaucerLogic(self):
        if self.saucer is not None:
            if self.saucer.laps >= 2:
                self.killSaucer()

        # Create a saucer
        if self.secondsCount % 2000 == 0 and self.saucer is None:
            randVal = random.randrange(0, 10)
            if randVal <= 3:
                self.saucer = Saucer(
                    self.stage, Saucer.smallSaucerType, self.ship)
            else:
                self.saucer = Saucer(
                    self.stage, Saucer.largeSaucerType, self.ship)
            self.stage.addSprite(self.saucer)

    def exploding(self):
        self.explodingCount += 1
        if self.explodingCount > self.explodingTtl:
            self.gameState = 'playing'
            [self.stage.spriteList.remove(debris)
             for debris in self.ship.shipDebrisList]
            self.ship.shipDebrisList = []

            if self.lives == 0:
                self.ship.visible = False
            else:
                self.createNewShip()

    def levelUp(self):
        self.numRocks += 1
        self.createRocks(self.numRocks)

    # move this hack somewhere else!
    def displayText(self):
        # M-1: static texts are pre-rendered surfaces, blitted per frame.
        titleTextRect = self.titleSurface.get_rect(centerx=self.stage.width/2)
        titleTextRect.y = self.stage.height/2 - titleTextRect.height*2
        self.stage.screen.blit(self.titleSurface, titleTextRect)

        keysTextRect = self.copyrightSurface.get_rect(centerx=self.stage.width/2)
        keysTextRect.y = self.stage.height - keysTextRect.height - 20
        self.stage.screen.blit(self.copyrightSurface, keysTextRect)

        instructionTextRect = self.instructionSurface.get_rect(
            centerx=self.stage.width/2)
        instructionTextRect.y = self.stage.height/2 - instructionTextRect.height
        self.stage.screen.blit(self.instructionSurface, instructionTextRect)

    def displayScore(self):
        # M-1: reuse the cached 30pt font (the text itself changes).
        # The arcade wrapped the score at 100 000; keep the display 5 digits.
        scoreStr = "%04d" % min(self.score, 99999)
        scoreText = self.fonts[30].render(scoreStr, True, (200, 200, 200))
        scoreTextRect = scoreText.get_rect(centerx=100, centery=45)
        self.stage.screen.blit(scoreText, scoreTextRect)

    def displayPowerUps(self):
        # P-5: a row of E/R/S letters in the top-right corner, S closest
        # to the edge.  A letter is bright while its effect is active,
        # dim otherwise; the surfaces are pre-rendered in __init__ (M-1).
        timers = {
            "E": self.ship.extraBulletsTimer,
            "R": self.ship.rapidFireTimer,
            "S": self.ship.shieldTimer,
            # Q-1: B is bright while the bomb flash runs (armed in Q-2).
            "B": self.bombFlashTimer,
        }
        gap = 8
        x = self.stage.width - 12  # right edge of the rightmost letter
        for letter in reversed(self.powerUpLetters):
            if timers[letter] > 0:
                surface = self.powerUpSurfaces[letter][0]
            else:
                surface = self.powerUpSurfaces[letter][1]
            rect = surface.get_rect(topright=(x, 12))
            self.stage.screen.blit(surface, rect)
            x -= surface.get_width() + gap

    def displayPaused(self):
        if self.paused:
            # M-1: the "Paused" text is a pre-rendered surface.
            textRect = self.pausedSurface.get_rect(
                centerx=self.stage.width/2, centery=self.stage.height/2)
            self.stage.screen.blit(self.pausedSurface, textRect)
            pygame.display.update()

    # Should move the ship controls into the ship class
    def input(self, events):
        self.frameAdvance = False
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if self.gameState == 'playing':
                    if event.key == K_SPACE:
                        self.ship.fireBullet()
                    elif event.key == K_b:
                        self.ship.fireBullet()
                    elif event.key == K_h:
                        self.ship.enterHyperSpace()
                elif self.gameState == 'attract_mode':
                    # Start a new game
                    if event.key == K_RETURN:
                        self.initialiseGame()

                if event.key == K_p:
                    if self.paused:  # (is True)
                        self.paused = False
                    else:
                        self.paused = True

                if event.key == K_j:
                    if self.showingFPS:  # (is True)
                        self.showingFPS = False
                    else:
                        self.showingFPS = True

                if event.key == K_f:
                    pygame.display.toggle_fullscreen()

                # if event.key == K_k:
                    # self.killShip()
            elif event.type == KEYUP:
                if event.key == K_o:
                    self.frameAdvance = True

    def processKeys(self):
        key = pygame.key.get_pressed()

        if key[K_LEFT] or key[K_z]:
            self.ship.rotateLeft()
        elif key[K_RIGHT] or key[K_x]:
            self.ship.rotateRight()

        if key[K_UP] or key[K_n]:
            self.ship.increaseThrust()
            self.ship.thrustJet.accelerating = True
        else:
            self.ship.thrustJet.accelerating = False

    # Check for ship hitting the rocks etc.

    def checkCollisions(self):

        # Ship bullet hit rock?
        newRocks = []
        shipHit, saucerHit = False, False

        # Safe area: a freshly respawned ship is invulnerable while the
        # respawn timer is running, and a shielded ship (P-3) is
        # invulnerable while the shield timer is running.
        safe = self.ship.respawnTimer > 0 or self.ship.shieldTimer > 0

        # Rocks
        for rock in self.rockList:
            rockHit = False

            if not safe and not self.ship.inHyperSpace and rock.collidesWith(self.ship):
                p = rock.checkPolygonCollision(self.ship)
                if p is not None:
                    shipHit = True
                    rockHit = True

            if self.saucer is not None:
                if rock.collidesWith(self.saucer):
                    saucerHit = True
                    rockHit = True

                if self.saucer.bulletCollision(rock):
                    rockHit = True

            if self.ship.bulletCollision(rock):
                rockHit = True

            if rockHit:
                self.rockList.remove(rock)
                self.stage.spriteList.remove(rock)

                if rock.rockType == Rock.largeRockType:
                    playSound("explode1")
                    newRockType = Rock.mediumRockType
                    self.score += 50
                elif rock.rockType == Rock.mediumRockType:
                    playSound("explode2")
                    newRockType = Rock.smallRockType
                    self.score += 100
                else:
                    playSound("explode3")
                    self.score += 200

                if rock.rockType != Rock.smallRockType:
                    # new rocks
                    for _ in range(0, 2):
                        position = Vector2d(rock.position.x, rock.position.y)
                        newRock = Rock(self.stage, position, newRockType)
                        self.stage.addSprite(newRock)
                        self.rockList.append(newRock)

                self.maybeSpawnPowerUp(
                    Vector2d(rock.position.x, rock.position.y))

                self.createDebris(rock)

        # Power-ups (P-3): contact picks one up.  Iterate a copy of the
        # list — the pickup removes the item from both this list and the
        # stage while we are looping.
        for powerUp in list(self.powerUpList):
            if powerUp.collidesWith(self.ship):
                self.ship.applyPowerUp(powerUp.letter)
                self.powerUpList.remove(powerUp)
                self.stage.removeSprite(powerUp)

        # Saucer (evaluated once per frame, outside the rock loop)
        if self.saucer is not None:
            if self.ship.bulletCollision(self.saucer):
                saucerHit = True
                self.score += self.saucer.scoreValue

            if not safe and not self.ship.inHyperSpace:
                if self.saucer.bulletCollision(self.ship):
                    shipHit = True

                if self.saucer.collidesWith(self.ship):
                    shipHit = True
                    saucerHit = True

            if saucerHit:
                self.createDebris(self.saucer)
                self.killSaucer()

        if shipHit:
            self.killShip()

            # comment in to pause on collision
            #self.paused = True

    def killShip(self):
        stopSound("thrust")
        playSound("explode2")
        self.explodingCount = 0
        self.lives -= 1
        if (self.livesList):
            ship = self.livesList.pop()
            self.stage.removeSprite(ship)

        self.stage.removeSprite(self.ship)
        self.stage.removeSprite(self.ship.thrustJet)
        self.gameState = 'exploding'
        self.ship.explode()

    def killSaucer(self):
        stopSound("lsaucer")
        stopSound("ssaucer")
        playSound("explode2")
        self.stage.removeSprite(self.saucer)
        self.saucer = None

    def createDebris(self, sprite):
        for _ in range(0, 25):
            position = Vector2d(sprite.position.x, sprite.position.y)
            debris = Debris(position, self.stage)
            self.stage.addSprite(debris)

    def displayFps(self):
        # M-1: reuse the cached 15pt font (the value changes).
        fpsStr = str(self.fps)+(' FPS')
        scoreText = self.fonts[15].render(fpsStr, True, (255, 255, 255))
        scoreTextRect = scoreText.get_rect(
            centerx=(self.stage.width/2), centery=15)
        self.stage.screen.blit(scoreText, scoreTextRect)

    def checkScore(self):
        if self.score > 0 and self.score > self.nextLife:
            playSound("extralife")
            self.nextLife += 10000
            self.addLife(self.lives)


# Script to run the game
if __name__ == "__main__":
    if not pygame.font:
        print('Warning, fonts disabled')
    if not pygame.mixer:
        print('Warning, sound disabled')

    initSoundManager()
    game = Asteroids()  # create object game from class Asteroids
    game.playGame()

####
