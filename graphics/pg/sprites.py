import os
import sys

from graphics.constants import *

with open(os.devnull, 'w') as f:
    # disable prints
    old_stdout = sys.stdout
    sys.stdout = f

    # imports with unwanted prints here
    import pygame
    from pygame.locals import *
    from pygame.math import Vector2 as Vec

    # enable prints
    sys.stdout = old_stdout


class Player(pygame.sprite.Sprite):
    """representation of every Player in the current game."""

    def __init__(self, game, identifier, team, pos, angle=0):
        """
        create a player, mainly online one

        :param game: the game which the player plays
        :type game: graphics.pg.gtypes.Engine
        :param identifier: a unique number to identify the specific player
        :type identifier: int
        :param team: a single character representing the team of the player
        :type team: str
        :param pos: the position of the player on the map
        :type pos: tuple[int, int] or pygame.math.Vector2
        :param angle: a number representing the rotation of the player
        :type angle: float
        """
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

    def update(self, data=None):
        """
        wrapper for the actual update function
        this is made because of the need in a 2-steps update function for this kind of player

        :param data: the data received by the game from the server
        :type data: None or list[tuple[int, str, tuple[int, int], float]]
        """
        try:
            ret = self.upgen.next()
        except (AttributeError, StopIteration):
            if data:
                self.upgen = self.update_internal(data)
            ret = self.upgen.next()

    def update_internal(self, data):
        """
        the actual update function
        because of the need in a 2-steps call, a yield expression is used
        because of the yield expression, this function is interpreted as generator

        :param data: the data received by the game from the server
        :type data: list[tuple[int, str, tuple[int, int], float]]
        """
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
        yield 'done'


class LocalPlayer(Player):
    """representation of Local Player in the current game."""

    def __init__(self, game, identifier, team, pos):
        """
        create a local player, for the user of the computer in which the game run on

        :param game: the game which the player plays
        :type game: graphics.pg.gtypes.Engine
        :param identifier: a unique number to identify the specific player
        :type identifier: int
        :param team: a single character representing the team of the player
        :type team: str
        :param pos: the position of the player on the map
        :type pos: tuple[int, int] or pygame.math.Vector2
        """
        Player.__init__(self, game, identifier, team, pos)
        self.remove(self._game.players)
        self.vel = Vec(0, 0)

    def apply_keys(self):
        """
        a function to handle the keyboard input relevant to the player
        this is preferred over the event driven handling
        because it's faster and more efficient
        """
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
        """
        updates the player representation
        because this kind of player is not dependent on the server data
        there is no requirement for 2-steps update
        """
        self.angle = (self._game.camera.apply_pos(pygame.mouse.get_pos()) - self.pos).angle_to(Vec(1, 0))
        self.image = pygame.transform.rotate(self._image, self.angle)
        self.rect = self.image.get_rect()
        self.vel *= self._game.dt
        self.pos += self.vel
        self.hit_rect.centerx = self.pos.x
        self.hit_rect.centery = self.pos.y
        self.rect.center = self.hit_rect.center
