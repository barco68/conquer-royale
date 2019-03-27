from ConfigParser import ConfigParser
import os
import pygame
from pygame.math import Vector2 as Vec

from graphics.constants import *


class MapCache(object):
    """object for storing Map."""

    def __init__(self, mapfile):
        """
        create the object to hold the data of the map

        :param mapfile: the file representing the map structure
        :type mapfile: str
        """
        self.map_file = os.path.join('assets', mapfile)
        self.parser = ConfigParser()
        self.parser.read(self.map_file)
        self.data = self.parser.get('level', 'map').splitlines()
        self.width = len(self.data[0]) * TILE_SIZE
        self.height = len(self.data) * TILE_SIZE


class Camera(object):
    """object for calculation of point of view."""

    def __init__(self, width, height):
        """
        create the object for the calculation of the point of view

        :param width: the length of the map horizontally
        :type width: int
        :param height: the length of the map vertically
        :type height: int
        """
        super(Camera, self).__init__()
        self.rel_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """
        calculate the area of an object relative to the point of view

        :param entity: the object to calculate the area of
        :type entity: pygame.sprite.Sprite
        :return: the area of the object
        :rtype: pygame.Rect
        """
        return entity.rect.move(self.rel_rect.topleft)

    def apply_surf(self, surface):
        """
        calculate the area of a surface relative to the point of view

        :param surface: the surface to calculate the area of
        :type surface: pygame.Surface
        :return: the area of the surface
        :rtype: pygame.Rect
        """
        return surface.get_rect().move(self.rel_rect.topleft)

    def apply_pos(self, pos):
        """
        calculate the position of the given coordinates relative to the point of view
        :param pos: coordinates to calculate the relative position
        :type pos: tuple[float, float] or pygame.math.Vector2
        :return: the relative position
        :rtype: pygame.math.Vector2
        """
        return Vec(pos) - Vec(self.rel_rect.topleft)

    def update(self, target):
        """
        update the point of view to a player point of view

        :param target: the player to move the point of view of the game to his point of view
        :type target: graphics.pg.sprites.Player
        """
        x = -target.hit_rect.x + WIDTH / 2
        y = -target.hit_rect.y + HEIGHT / 2

        x = min(0, x)
        y = min(0, y)

        x = max(-(self.width - WIDTH), x)
        y = max(-(self.height - HEIGHT), y)

        self.rel_rect = pygame.Rect(x, y, self.width, self.height)
