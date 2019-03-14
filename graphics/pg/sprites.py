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
    def __init__(self, game, x, y, team, identifier):
        self._game = game
        self.team = self.origin = team
        self.identifier = identifier
        groups = self._game.all_sprites, self._game.players
        super(Player, self).__init__(groups)
        self._image = self._game.tile_set[18 + (team.lower() == 'blue')]
        self._image.set_colorkey(COLOR_KEY)
        self.image = self._image
        self.rect = self.image.get_rect()
        self.hit_rect = pygame.Rect(self.rect.left, self.rect.top, self.rect.width, self.rect.height)
        self.angle = 0
        self.pos = Vec(x, y)

        def apply_net(self, data):
            for player in data:
                if player[0] == self.identifier:
                    self.pos = Vec(player[1])
                    self.team = player[2]
                    self.angle = player[3]

    def update(self, *args):
        self.apply_net(args[0])
        yield
        self.image = pygame.transform.rotate(self._image, self.angle)
        self.hit_rect.centerx = self.pos.x
        self.hit_rect.centery = self.pos.y
        self.rect.center = self.hit_rect.center


class LocalPlayer(Player):
    """docstring for LocalPlayer."""
    def __init__(self, game, pos, team, identifier):
        super(LocalPlayer, self).__init__(game, pos[0], pos[1], team, identifier)
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
