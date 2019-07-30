import os
import sys
from math import pi

import sprites
import maps
from graphics.constants import *

with open(os.devnull, 'w') as f:
    # disable printing
    old_stdout = sys.stdout
    sys.stdout = f

    # imports with unwanted prints here
    import pygame
    from pygame.locals import *
    from pygame.math import Vector2 as Vec

    # enable printing
    sys.stdout = old_stdout

# make sure the working directory is the game directory
if not os.getcwd() == sys.path[0]:
    os.chdir(sys.path[0])


class Engine(object):
    def __init__(self, data_stream, out_stream):
        """
        build the game object

        :param data_stream: object to collect data from the server
        :type data_stream: list
        :param out_stream: object to transfer data to the server
        :type out_stream: list
        """
        # Simple Fields
        self._data_stream = data_stream
        self._out_stream = out_stream
        self._running = False
        self.tile_set = None
        # pre run Graphics Initialization
        self.camera = None
        self._background = None
        self._screen = None
        self.all_sprites = None
        self.players = None
        self.bullets = None
        self.mobs = None
        self._local_player = None
        self.clock = None
        self.dt = 0

    def new(self):
        """
        initialize the graphics
        """
        # Graphics Initialization
        pygame.init()
        self._screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.load_tileset()
        map_cache = maps.MapCache(DEFAULT_MAP)
        self._background = pygame.Surface((map_cache.width, map_cache.height))
        for x, row in enumerate(map_cache.data):
            for y, tile in enumerate(row):
                self._background.blit(self.tile_set[int(tile)], (y * TILE_SIZE, x * TILE_SIZE))
        self.camera = maps.Camera(map_cache.width, map_cache.height)
        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        sprites.Mob(self, 1, 1500, 1250)
        self.clock = pygame.time.Clock()

    def render(self):
        """
        rendering the game
        """
        # map rendering, might need an efficiency upgrade
        self._screen.blit(self._background, self.camera.apply_surf(self._background))
        # object rendering
        for sprite in self.all_sprites.sprites():
            self._screen.blit(sprite.image, self.camera.apply(sprite))
        # player rendering, possible double rendering
        self._screen.blit(self._local_player.image, self.camera.apply(self._local_player))
        self.draw_player_ammo(10, 10)
        pygame.display.update()

    def events(self):
        """
        collecting relevant events for the game and processing them
        """
        # currently the only relevant event is exiting
        for event in pygame.event.get():
            if event.type == QUIT:
                self._running = False
                # send exit message to net thread
                self._out_stream.append((-1, 'e', 0, 0, 0))
        self._local_player.apply_input()

    def update(self):
        """
        updating the parts of the game with the events input
        """
        # send local player and fired bullets data to net thread
        try:
            self._out_stream[1:] = []
            self._out_stream[0] = (self._local_player.identifier, self._local_player.team,
                                   self._local_player.pos.x, self._local_player.pos.y, self._local_player.angle)
        except IndexError:
            self._out_stream.append((self._local_player.identifier, self._local_player.team,
                                     self._local_player.pos.x, self._local_player.pos.y, self._local_player.angle))
        for bullet in self.bullets.sprites():
            if bullet.origin == self._local_player.identifier and not bullet.sent:
                self._out_stream.append((0, chr(bullet.origin), bullet.pos.x, bullet.pos.y, -bullet.vel.as_polar()[1]))
                bullet.sent = True
        # update players
        self.players.update(self._data_stream)
        # if new players entered the game, insert them to the game
        # future: players could only enter before battle started
        players = self.players.sprites()
        players.append(self._local_player)
        players.sort(key=lambda x: x.identifier)
        for data in self._data_stream[:]:
            if not data[0]:
                if not ord(data[1]) == self._local_player.identifier:
                    sprites.Bullet(self, ord(data[1]), data[2], data[3], data[4])
                self._data_stream.remove(data)
            else:
                check = filter(lambda x: x.identifier == data[0], players)
                if not check:
                    sprites.Player(self, *data)
        # update all objects
        self.all_sprites.update()

        # update point of view
        self.camera.update(self._local_player)

        # bullets hitting anything
        hits = pygame.sprite.groupcollide(self.bullets, self.all_sprites, False, False, sprites.collide_hit_rect)
        for hit, targets in hits.items():
            if hit in targets:
                # prevent self hitting
                targets.remove(hit)
            for target in targets:
                # cross fire -> switch velocities
                if isinstance(target, sprites.Bullet):
                    hit.vel, target.vel = target.vel, hit.vel
                # hitting a mob -> reduce health
                elif isinstance(target, sprites.Mob):
                    target.health -= HEALTH_FACTOR
                    # health <= 0 -> kill mob
                    if target.health <= 0:
                        target.kill()
                        # bullet origin == local player -> refill ammo
                        if hit.origin == self._local_player.identifier:
                            self._local_player.ammo += target.reward
                # hitting player
                elif isinstance(target, sprites.Player):
                    # other team -> change team
                    if not players[hit.origin - 1].team == target.team:
                        target.team = players[hit.origin - 1].team
                    # same team -> refill ammo unless bullet origin == local player
                    else:
                        if target is self._local_player and not hit.origin == self._local_player.identifier:
                            self._local_player.ammo = 100

        # mobs hitting local player
        hits = pygame.sprite.spritecollide(self._local_player, self.mobs, False, collided=sprites.collide_hit_rect)
        # calculate knock back direction
        knock_back = Vec(0, 0)
        for hit in hits:
            knock_back += hit.vel.normalize()
            self._local_player.ammo -= REFILL_FACTOR
        # check for knock back, squared faster because no sqrt call
        if knock_back.length_squared():
            knock_back.scale_to_length(KNOCKBACK_SPEED)
        # apply knock back
        self._local_player.pos += knock_back

    def run(self):
        """
        running the game
        """
        self._running = True
        initdata = max(self._data_stream, key=lambda x: x[0])
        self._local_player = sprites.LocalPlayer(self, *initdata)
        while self._running:
            # time since last frame, used mainly in player speed calculation
            # possible change: player decide the fps
            self.dt = self.clock.tick(FPS) / 1000.0
            # temporary to  make sure no feature stuck the game
            # possible change: player decide to view or hide real time fps
            pygame.display.set_caption('{:.2f}'.format(self.clock.get_fps()))
            self.events()
            self.update()
            self.render()
        # currently no end game screen, game exit on player decision
        pygame.quit()

    def load_tileset(self):
        """
        loading the tile set
        """
        source = pygame.image.load(os.path.join('assets', TILE_SET_FILE)).convert()
        tswidth, tsheight = source.get_size()
        # tile set as dictionary is easier to access
        self.tile_set = {}
        for tile_x in xrange(tswidth / TILE_SIZE):
            for tile_y in xrange(tsheight / TILE_SIZE):
                rect = (tile_x * TILE_SIZE, tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.tile_set[len(self.tile_set)] = source.subsurface(rect)

    def draw_player_ammo(self, x, y):
        """
        HUD for the player to see his state

        :param x: left position for the HUD
        :type x: int
        :param y: top position for the HUD
        :type y: int
        """
        info_rect = pygame.Rect(x, y, 50, 50)
        if self._local_player.team == 'r':
            color = RED
        elif self._local_player.team == 'b':
            color = BLUE
        end = pi * (0.5 + self._local_player.ammo * 2 / 100.0)
        pygame.draw.arc(self._screen, color, info_rect, 0.5 * pi, end, 25)


def graphic_thread(instream, outstream):
    """
    function of the graphic thread

    :param instream: object to get data from the (demy) net thread
    :type instream: list
    :param outstream: object to transfer data to the (demy) net thread
    :type outstream: list
    """
    game = Engine(instream, outstream)
    game.new()
    game.run()
