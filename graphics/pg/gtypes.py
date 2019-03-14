import ConfigParser
from ast import literal_eval
import os
import sys

import sprites
import maps
from graphics.constants import *

with open(os.devnull, 'w') as f:
    # disable stdout
    old_stdout = sys.stdout
    sys.stdout = f

    # imports with unwanted prints here
    import pygame
    from pygame.locals import *

    # enable stdout
    sys.stdout = old_stdout


if not os.getcwd() == sys.path[0]:
    os.chdir(sys.path[0])


class Engine(object):
    def __init__(self, data_stream, out_stream):
        # Simple Fields
        self._data_stream = data_stream
        self._out_stream = out_stream
        self._running = False
        self.tile_set = None
        # Map Construction
        self._map = maps.Map_Cache(DEFAULT_MAP)
        # Graphics Initialization
        pygame.init()
        self._background = pygame.Surface((self._map.width, self._map.height))
        self.camera = maps.Camera(self._map.width, self._map.height)
        self._screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.load_tileset()
        self._local_player = sprites.LocalPlayer(self, *literal_eval(self._data_stream.pop(0)))
        # self._players.add(self._local_player)
        self.clock = pygame.time.Clock()
        pygame.key.set_repeat(500, 100)
        self.dt = 0

    def render(self):
        for x, row in enumerate(self._map.data):
            for y, tile in enumerate(row):
                self._background.blit(self.tile_set[int(tile)], (y * TILE_SIZE, x * TILE_SIZE))
        self._screen.blit(self._background, self.camera.apply_surf(self._background))
        for sprite in self.all_sprites:
            self._screen.blit(sprite.image, self.camera.apply(sprite))
        self._screen.blit(self._local_player.image, self.camera.apply(self._local_player))
        pygame.display.update()

    def events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self._running = False
                self._out_stream.append((-1, None, 'exit', 0))

    def update(self):
        while len(self._data_stream) > len(self.players) - 1:
            sprites.Player(self, *literal_eval(self._data_stream.pop()))
        self.players.update(self._data_stream)
        self.all_sprites.update()
        self.camera.update(self._local_player)
        self._out_stream.append((self._local_player.identifier, (self._local_player.pos.x, self._local_player.pos.y),
                                self._local_player.team, self._local_player.angle))

    def run(self):
        self._running = True
        while self._running:
            self.dt = self.clock.tick(FPS) / 1000.0
            pygame.display.set_caption('{:.2f}'.format(self.clock.get_fps()))
            self.events()
            self.update()
            self.render()
        pygame.quit()

    def load_tileset(self):
        source = pygame.image.load(os.path.join('assets', TILE_SET_FILE)).convert()
        tswidth, tsheight = source.get_size()
        self.tile_set = {}
        for tile_x in xrange(tswidth / TILE_SIZE):
            for tile_y in xrange(tsheight / TILE_SIZE):
                rect = (tile_x * TILE_SIZE, tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.tile_set[len(self.tile_set)] = source.subsurface(rect)


def graphic_thread(instream, outstream):
    game = Engine(instream, outstream)
    game.run()
    # print 'done'


def toggle_fullscreen(surface, width, height, flags=0):
    """
    toggles fullscreen without scaling

    :param surface: the surface you want to become all over the screen
    :param width: the number of pixels in the horizontal axis of the screen
    :type width: int
    :param height: the number of pixels in the vertical axis of the screen
    :type height: int
    :param flags: flags that should be add to the surface during the conversion
    :return: the surface which displayed on the screen
    """

    # gets the flags of 'surface' and add to the given flags
    flags |= surface.get_flags()

    # surface needs conversion before "set_mode"
    surface = surface.convert()

    # make the new fullscreen or windowed surface
    if not flags & FULLSCREEN:
        flags |= FULLSCREEN
        screen = pygame.display.set_mode((width, height), flags)
    else:
        flags ^= FULLSCREEN
        screen = pygame.display.set_mode((width, height), flags)

    # transferring the graphics from surface to screen
    screen.blit(surface, (0, 0))
    pygame.display.update()

    # returns the new screen
    return screen


def toggle_scaled_fullscreen(surface, width, height, flags=0):
    """
    toggles fullscreen with scaling

    :param surface: the surface you want to become all over the screen
    :param width: the number of pixels in the horizontal axis of the screen
    :type width: int
    :param height: the number of pixels in the vertical axis of the screen
    :type height: int
    :param flags: flags that should be add to the surface during the conversion
    :return: the surface which displayed on the screen
    """

    # gets the flags of 'surface' and add to the given flags
    flags |= surface.get_flags()

    # surface needs conversion before "set_mode"
    surface = surface.convert()

    # make the new fullscreen or windowed surface
    if not flags & FULLSCREEN:
        flags |= FULLSCREEN
        screen = pygame.display.set_mode((width, height), flags)
    else:
        flags ^= FULLSCREEN
        screen = pygame.display.set_mode((width, height), flags)

    # scaling and transferring the graphics from surface to screen
    screen.blit(pygame.transform.scale(surface, screen.get_size()), (0, 0))
    pygame.display.update()

    # returns the new screen
    return screen
