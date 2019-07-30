import os
import sys
from math import cos, sin, radians

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

    def __init__(self, game, identifier, team, x, y, angle):
        """
        create a player, mainly online one

        :param game: the game which the player plays
        :type game: graphics.pg.gtypes.Engine
        :param identifier: a unique number to identify the specific player
        :type identifier: int
        :param team: a single character representing the team of the player
        :type team: str
        :param x: the starting x-position of the player on the map
        :type x: int
        :param y: the starting y-position of the player on the map
        :type y: int
        :param angle: a number representing the rotation of the player
        :type angle: float
        """
        self._game = game
        self.team = self.origin = team
        self.identifier = identifier
        groups = self._game.all_sprites, self._game.players
        pygame.sprite.Sprite.__init__(self, groups)
        self._image = self._game.tile_set[18 + (team.lower() == 'b')].copy()
        self._image.set_colorkey(COLOR_KEY)
        self.angle = angle
        self.pos = Vec(x, y)
        self.image = pygame.transform.rotate(self._image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.hit_rect = self.rect.inflate(PLAYER_RADIUS - self.rect.width, PLAYER_RADIUS - self.rect.height)

    def update(self, data=None):
        """
        wrapper for the actual update function
        this is made because of the need in a 2-steps update function for this kind of player

        :param data: the data received by the game from the server
        :type data: None or list[tuple[int, str, int, int, float]]
        """
        try:
            self.upgen.next()
        except (AttributeError, StopIteration):
            if data:
                relevant_data = filter(lambda x: x[0] == self.identifier, data)
                [data.remove(value) for value in relevant_data[:-1]]
                self.upgen = self.update_internal(relevant_data[-1])
                self.upgen.next()

    def update_internal(self, data):
        """
        the actual update function
        because of the need in a 2-steps call, a yield expression is used
        because of the yield expression, this function is interpreted as generator

        :param data: the data received by the game from the server
        :type data: tuple[int, str, int, int, float]
        """
        i, t, x, y, a = data
        self.team = t
        self.pos = Vec(x, y)
        self.angle = a
        yield 'called'
        self.image = pygame.transform.rotate(self._image, self.angle)
        self.rect = self.image.get_rect()
        self.hit_rect.centerx = self.pos.x
        self.hit_rect.centery = self.pos.y
        self.rect.center = self.hit_rect.center
        yield 'done'


class LocalPlayer(Player):
    """representation of Local Player in the current game."""

    def __init__(self, game, identifier, team, x, y, angle):
        """
        create a local player, for the user of the computer in which the game run on

        :param game: the game which the player plays
        :type game: graphics.pg.gtypes.Engine
        :param identifier: a unique number to identify the specific player
        :type identifier: int
        :param team: a single character representing the team of the player
        :type team: str
        :param x: the starting x-position of the player on the map
        :type x: int
        :param y: the starting y-position of the player on the map
        :type y: int
        """
        Player.__init__(self, game, identifier, team, x, y, angle)
        self.remove(self._game.players)
        self.vel = Vec(0, 0)
        self.last_shot = 0
        self.ammo = 100

    def apply_input(self):
        """
        a function to handle the input relevant to the player
        this is preferred over the event driven handling
        because it's faster and more efficient
        """
        self.vel.x, self.vel.y = 0, 0
        pressed = pygame.key.get_pressed()
        if pressed[K_s]:
            self.vel.y += PLAYER_SPEED
        if pressed[K_w]:
            self.vel.y -= PLAYER_SPEED
        if pressed[K_d]:
            self.vel.x += PLAYER_SPEED
        if pressed[K_a]:
            self.vel.x -= PLAYER_SPEED
        if self.vel.x and self.vel.y:
            self.vel *= 0.7071

        clicks = pygame.mouse.get_pressed()
        now = pygame.time.get_ticks() / 1000.0
        if clicks[0] and now - self.last_shot >= SHOOT_WAIT and self.ammo > 0:
            shoot_from = ((self.pos.x + (PLAYER_RADIUS + PLAYER_CANON) * cos(radians(self.angle))
                           + BULLET_RADIUS * cos(radians(self.angle))),
                          (self.pos.y + (PLAYER_RADIUS + PLAYER_CANON) * sin(radians(self.angle))
                           + BULLET_RADIUS * sin(radians(self.angle))))
            Bullet(self._game, self.identifier, shoot_from[0], shoot_from[1], self.angle, now)
            self.last_shot = now
            self.ammo -= 10

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


class Bullet(pygame.sprite.Sprite):
    """representation of every Bullet in the game."""

    def __init__(self, game, origin, x, y, angle, st=None):
        """
        create a bullet shot in the game

        :param game: the game object which the bullet is in
        :type game: gtypes.Engine
        :param origin: the identifier of the shooting player
        :type origin: int
        :param x: the starting x-position of the player on the map
        :type x: int
        :param y: the starting y-position of the player on the map
        :type y: int
        :param angle: the angle at which the bullet is fired
        :type angle: float
        :param st: optional, if presented, specifies the time of creation of the bullet
        :type st: float or None
        """
        self._game = game
        self.origin = origin
        players = game.players.sprites()
        players.append(game._local_player)
        players.sort(key=lambda x: x.identifier)
        if origin == game._local_player.identifier:
            self.sent = False
        groups = game.all_sprites, game.bullets
        super(Bullet, self).__init__(groups)
        self.pos = Vec(x, y)
        self.vel = Vec(BULLET_SPEED, 0).rotate(-angle)
        self.image = pygame.Surface((BULLET_RADIUS, BULLET_RADIUS))
        self.image.fill(COLOR_KEY)
        self.image.set_colorkey(COLOR_KEY)
        self.rect = self.image.get_rect()
        if players[origin - 1].team == 'r':
            pygame.draw.circle(self.image, RED, (self.rect.width / 2, self.rect.height / 2), BULLET_RADIUS)
        elif players[origin - 1].team == 'b':
            pygame.draw.circle(self.image, BLUE, (self.rect.width / 2, self.rect.height / 2), BULLET_RADIUS)
        self.spawn_time = st if st else pygame.time.get_ticks() / 1000.0

    def update(self):
        """
        update the location of the bullet
        """
        if (pygame.time.get_ticks() / 1000.0) - self.spawn_time >= BULLET_TTL:
            self.kill()
            return
        self.pos += self.vel * self._game.dt
        self.rect.centerx = self.pos.x
        self.rect.centery = self.pos.y


class Mob(pygame.sprite.Sprite):
    """representation of every Mob in the game."""

    def __init__(self, game, difficulty, x, y):
        """
        create a mob to chase the players

        :param game: the game object in which the mob is in
        :type game: gtypes.Engine
        :param difficulty: the level of the mob. effecting both health of the mob and reward for killing the mob.
        :type difficulty: int
        :param x: the starting x-position of the player on the map
        :type x: int
        :param y: the starting y-position of the player on the map
        :type y: int
        """
        self._game = game
        self.health = HEALTH_FACTOR * difficulty
        self.reward = REFILL_FACTOR * (difficulty + 1)
        groups = game.all_sprites, game.mobs
        super(Mob, self).__init__(groups)
        self.pos = Vec(x, y)
        font = pygame.font.Font('assets/Fraktur.otf', 50)
        font.set_bold(True)
        self.image = font.render('M', True, MOB_COLOR, COLOR_KEY)
        self.image.set_colorkey(COLOR_KEY)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.vel = None

    def update(self):
        """
        update the direction and location of the mob
        """
        players = self._game.players.sprites()
        players.append(self._game._local_player)
        target = min(players, key=lambda x: self.pos.distance_to(x.pos))
        self.vel = Vec(MOB_SPEED, 0).rotate(-((target.pos - self.pos).angle_to(Vec(1, 0))))
        self.pos += self.vel * self._game.dt
        self.rect.centerx = self.pos.x
        self.rect.centery = self.pos.y


def collide_hit_rect(one, two):
    """
    simple replace to collide check function
    inserts a case were there is a defined hit box
    to one or both of the sprites

    :param one: the first sprite
    :type one: pygame.sprite.Sprite
    :param two: the second sprite
    :type two: pygame.sprite.Sprite
    :return: whether the two sprites collide or not
    :rtype: bool
    """
    if hasattr(one, "hit_rect"):
        onerect = one.hit_rect
    else:
        onerect = one.rect
    if hasattr(two, "hit_rect"):
        tworect = two.hit_rect
    else:
        tworect = two.rect
    return onerect.colliderect(tworect)
