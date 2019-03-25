import os
import sys

from graphics.constants import *

with open(os.devnull, 'w') as f:
    # disable stdout
    old_stdout = sys.stdout
    sys.stdout = f

    # imports with unwanted prints here
    import pygame
    from pygame.locals import *
    from pygame.math import Vector2 as Vec

    # enable stdout
    sys.stdout = old_stdout


class Tile(pygame.sprite.Sprite):
    pass


class Player(pygame.sprite.Sprite):
    """docstring for Player."""

    def __init__(self, game, identifier, team, pos, angle=0):
        self._game = game
        self.team = self.origin = team
        self.identifier = identifier
        groups = self._game.all_sprites, self._game.players
        pygame.sprite.Sprite.__init__(self, groups)
        self._image = self._game.tile_set[18 + (team.lower() == 'b')]
        self._image.set_colorkey(COLOR_KEY)
        self.angle = angle
        self.pos = Vec(pos)
        self.image = pygame.transform.rotate(self._image, self.angle)
        self.rect = self._image.get_rect()
        self.rect.center = pos
        self.hit_rect = pygame.Rect(self.rect.left, self.rect.top, self.rect.width, self.rect.height)

    # noinspection PyAttributeOutsideInit
    def update(self, *args):
        try:
            ret = self.upgen.next()
        except (AttributeError, StopIteration):
            if args:
                self.upgen = self.update_internal(args[0])  # TODO: make a transform from generator to function
            ret = self.upgen.next()
        print ret

    def update_internal(self, data):
        relevant_data = filter(lambda x: x[0] == self.identifier, data)
        if relevant_data:
            i, t, p, a = relevant_data[-1]
            self.team = t
            self.pos = Vec(p)
            self.angle = a
            [data.remove(value) for value in relevant_data]
        yield 'called'
        self.image = pygame.transform.rotate(self._image, self.angle)
        self.rect = self.image.get_rect()
        self.hit_rect.centerx = self.pos.x
        self.hit_rect.centery = self.pos.y
        self.rect.center = self.hit_rect.center
        yield ' done'



class LocalPlayer(Player):
    """docstring for LocalPlayer."""

    def __init__(self, game, identifier, team, pos):
        Player.__init__(self, game, identifier, team, pos)
        self.remove(self._game.players)
        self.vel = Vec(0, 0)

    def apply_keys(self):
        self.vel.x, self.vel.y = 0, 0
        pressed = pygame.key.get_pressed()
        if pressed[K_s]:
            self.vel.y += BASE_SPEED
        if pressed[K_w]:
            self.vel.y -= BASE_SPEED
        if pressed[K_d]:
            self.vel.x += BASE_SPEED
        if pressed[K_a]:
            self.vel.x -= BASE_SPEED
        if self.vel.x and self.vel.y:
            self.vel *= 0.7071

    def update(self):
        self.apply_keys()
        self.angle = (self._game.camera.apply_pos(pygame.mouse.get_pos()) - self.pos).angle_to(Vec(1, 0))
        self.image = pygame.transform.rotate(self._image, self.angle)
        self.rect = self.image.get_rect()
        self.vel *= self._game.dt
        # self.vel = self.vel.rotate(-self.angle)
        self.pos += self.vel
        self.hit_rect.centerx = self.pos.x
        self.hit_rect.centery = self.pos.y
        self.rect.center = self.hit_rect.center
