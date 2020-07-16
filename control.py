import pygame
from pygame.locals import *

from utils import *
from game import *


def blitCentering(dest, image, pos):
    x, y = pos
    x = x - image.get_width()/2
    y = y - image.get_height()/2
    dest.blit(image, (x, y))


class UserEvent():
    PRINTER = pygame.USEREVENT + 1


class GameController():

    class PlayerData(ParticleOwnerBase):
        def __init__(self, identity, manager, owner,
                     color, loc, mapMove, mapAttack):

            super(GameController.PlayerData, self).__init__(identity+"data")

            self.friction = 0.4

            self.identity = identity
            self.mapMove = mapMove      # dict{key, force}
            self.mapAttack = mapAttack  # dict{key, direction}
            self.owner = owner

            self.force = (0, 0)
            self.keyDown = None
            self.attDown = None

            self.player = Player(
                identity=self.identity,
                manager=manager,
                owner=self,
                color=color,
                loc=loc
            )

        def spawnParticles(self):
            particles = ParticleGroup()
            particles.append(ParticleState(
                owner=self.player,
                pos=self.player.core.pos
            ))
            self.player.manager.addParticlesToBuffer(particles)

        def getForce(self, particle):
            ''' override '''
            return Vec2d(self.force)-particle.vel*self.friction

        def parseEvent(self, event):
            res = 0  # succeed
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                if event.key in self.mapMove.keys():
                    if event.type == pygame.KEYDOWN:
                        self.keyDown = event.key
                        self.force = self.mapMove[event.key]
                        print("PLAYER {0} received DOWN event, response: {1}".format(
                            self.identity, self.force))
                    else:  # KEYUP
                        if self.keyDown == event.key:
                            self.keyDown = None
                            self.force = (0, 0)
                        print("PLAYER {0} received UP event, response: {1}".format(
                            self.identity, self.force))
                elif event.key in self.mapAttack.keys():
                    if event.type == pygame.KEYDOWN and self.attDown == None:
                        self.attDown = event.key
                        res = self.player.command(self.mapAttack[event.key])
                    else:  # KEYUP
                        if self.keyDown == event.key:
                            self.keyDown = None
            elif event.type == UserEvent.PRINTER:
                self.player.detailPrinter()
            return res

    def __init__(self, screen):
        self.screen = screen

        self.resources = {}
        self.resources["player"] = pygame.image.load(
            "resources/PLAYER.png")
        self.FPS = 40
        self.worldRect = (640, 480)
        self.interval = (2, 2)

        self.manager = ParticleManager(self.worldRect, self.interval)
        self.renderer = ParticleRenderer(self.manager)

        self.AID = "playerA"
        self.BID = "playerB"

        self.players = {}
        self.players[self.AID] = self.PlayerData(
            manager=self.manager,
            owner=self,
            identity=self.AID,
            color=(255, 0, 0),
            loc=(50, 50),
            mapMove={
                pygame.K_RIGHT: (1, 0),
                pygame.K_LEFT:  (-1, 0),
                pygame.K_UP:    (0, -1),
                pygame.K_DOWN:  (0, 1)
            },
            mapAttack={
                pygame.K_BACKSLASH: 1
            }
        )

        self.players[self.BID] = self.PlayerData(
            manager=self.manager,
            owner=self,
            identity=self.BID,
            color=(0, 0, 255),
            loc=(self.worldRect[0]-50, self.worldRect[1]-50),
            mapMove={
                pygame.K_d:  (1, 0),
                pygame.K_a:  (-1, 0),
                pygame.K_w:  (0, -1),
                pygame.K_s:  (0, 1)
            },
            mapAttack={
                pygame.K_SPACE: 1
            }
        )

        # TODO: generate some particles for these players
        for data in self.players.values():
            data.spawnParticles()
        self.manager.commitParticles()

    def dispatchEvent(self, event):
        ''' dispatch pygame event '''
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            for data in self.players.values():
                data.parseEvent(event)
        elif event.type == UserEvent.PRINTER:
            print("=== time interrupt ===")
            self.manager.simplePrinter()
            for data in self.players.values():
                data.parseEvent(event)

    def renderPlayer(self, data):
        pos = data.player.core.pos.toTuple()
        blitCentering(self.screen, self.resources["player"], pos)

    def update(self):
        ''' called from pygame cycle '''
        for data in self.players.values():
            data.player.step()
        self.manager.step()

        self.screen.fill((255, 255, 255))  # WHITE BACKGROUND
        surface = self.renderer.render()
        self.screen.blit(surface, (0, 0))
        for data in self.players.values():
            self.renderPlayer(data)