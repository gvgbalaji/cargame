"""Abstract Factory for car creation (Pygame version)."""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .constants import COL_PLAYER_COLORS, COL_ENEMY_COLORS


@dataclass
class CarSpec:
    color: tuple       # (r, g, b)
    car_type: str      # "player" | "enemy"


class CarFactory(ABC):
    @abstractmethod
    def create(self) -> CarSpec:
        """Return a CarSpec for the car type this factory produces."""


class PlayerCarFactory(CarFactory):
    def __init__(self, color: tuple = (30, 120, 255)):
        self._color = color

    def create(self) -> CarSpec:
        return CarSpec(color=self._color, car_type="player")


class EnemyCarFactory(CarFactory):
    def create(self) -> CarSpec:
        return CarSpec(
            color=random.choice(COL_ENEMY_COLORS),
            car_type="enemy",
        )
