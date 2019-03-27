import os
import sys

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
        # Map Construction
        self._map = maps.MapCache(DEFAULT_MAP)
        # Graphics Initialization
        pygame.init()
        self._background = pygame.Surface((self._map.width, self._map.height))
        self.camera = maps.Camera(self._map.width, self._map.height)
        self._screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.load_tileset()
        self._local_player = sprites.LocalPlayer(self, *self._data_stream.pop(0))
        self.clock = pygame.time.Clock()
        self.dt = 0

    def render(self):
        """
        rendering the game
        """
        # map rendering, might need an efficiency upgrade
        for x, row in enumerate(self._map.data):
            for y, tile in enumerate(row):
                self._background.blit(self.tile_set[int(tile)], (y * TILE_SIZE, x * TILE_SIZE))
        self._screen.blit(self._background, self.camera.apply_surf(self._background))
        # object rendering, try self.all_sprites.draw(self._screen)
        for sprite in self.all_sprites:
            self._screen.blit(sprite.image, self.camera.apply(sprite))
        # player rendering, possible double rendering
        self._screen.blit(self._local_player.image, self.camera.apply(self._local_player))
        pygame.display.update()

    def events(self):
        """
        collecting relevant events for the game and processing them
        """
        # currently the only relevant event is exiting
        for event in pygame.event.get():
            if event.type == QUIT:
                self._running = False
                # send exit message to (demy) net thread
                self._out_stream.append((-1, 'exit', None, 0))
        self._local_player.apply_keys()

    def update(self):
        """
        updating the parts of the game with the events input
        """
        # if new players entered the game, insert them to the game
        # future: players could only enter before battle started
        if len(self._data_stream) > len(self.players) + 1:
            players = self.players.sprites()
            players.append(self._local_player)
            backup = self._data_stream[:]
            for player_data in backup:
                check = filter(lambda x: x.identifier == player_data[0], players)
                if not check:
                    sprites.Player(self, *player_data)
                    self._data_stream.remove(player_data)
        # update players
        self.players.update(self._data_stream)
        # update all objects
        self.all_sprites.update()
        # update point of view
        self.camera.update(self._local_player)
        # send local player data to (demy) net thread
        # possible change: first send local player data, then update
        try:
            self._out_stream[0] = (self._local_player.identifier, self._local_player.team,
                                (self._local_player.pos.x, self._local_player.pos.y), self._local_player.angle)
        except IndexError:
            self._out_stream.append((self._local_player.identifier, self._local_player.team,
                                (self._local_player.pos.x, self._local_player.pos.y), self._local_player.angle))

    def run(self):
        """
        running the game
        """
        self._running = True
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


def graphic_thread(instream, outstream):
    """
    function of the graphic thread

    :param instream: object to get data from the (demy) net thread
    :type instream: list
    :param outstream: object to transfer data to the (demy) net thread
    :type outstream: list
    """
    game = Engine(instream, outstream)
    game.run()


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
