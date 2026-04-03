import random

from .constants import ENEMY_ARTS, ENEMY_COLORS, lane_x


class Enemy:
    __slots__ = ("lane", "y", "art", "color", "passed")

    def __init__(self, lane: int):
        self.lane   = lane
        self.y      = 1.0
        self.art    = random.choice(ENEMY_ARTS)
        self.color  = random.choice(ENEMY_COLORS)
        self.passed = False

    @property
    def x(self) -> int:
        return lane_x(self.lane)
