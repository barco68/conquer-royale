from ConfigParser import ConfigParser
import os
import pygame
from pygame.math import Vector2 as Vec

from graphics.constants import *

class Map_Cache(object):
    """docstring for Map_Cache."""
    def __init__(self, mapfile):
        game_folder = os.path.dirname(__file__)
        self.map_file = os.path.join('assets', mapfile)
        self.parser = ConfigParser()
        self.parser.read(self.map_file)
        self.data = self.parser.get('level', 'map').splitlines()
        self.width = len(self.data[0]) * TILE_SIZE
        self.height = len(self.data) * TILE_SIZE



class Camera(object):
    def __init__(self, width, height):
        self.rel_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.rel_rect.topleft)

    def apply_surf(self, surface):
        return surface.get_rect().move(self.rel_rect.topleft)

    def apply_pos(self, pos):
        return Vec(pos) - Vec(self.rel_rect.topleft)

    def update(self, target):
        x = -target.hit_rect.x + WIDTH/2
        y = -target.hit_rect.y + HEIGHT/2

        x = min(0, x)
        y = min(0, y)

        x = max(-(self.width - WIDTH), x)
        y = max(-(self.height - HEIGHT), y)

        self.rel_rect = pygame.Rect(x, y, self.width, self.height)
