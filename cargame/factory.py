"""Abstract Factory for car creation."""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .constants import ENEMY_ARTS, ENEMY_COLORS, PLAYER_ART, CP_YELLOW


@dataclass
class CarSpec:
    art: list[str]   # list of strings, one per row
    color: int       # curses color pair ID
    car_type: str    # "player" | "enemy"


class CarFactory(ABC):
    @abstractmethod
    def create(self) -> CarSpec:
        """Return a CarSpec for the car type this factory produces."""


class PlayerCarFactory(CarFactory):
    def __init__(self, color: int = CP_YELLOW):
        self._color = color

    def create(self) -> CarSpec:
        return CarSpec(art=PLAYER_ART, color=self._color, car_type="player")


class EnemyCarFactory(CarFactory):
    def create(self) -> CarSpec:
        return CarSpec(
            art=random.choice(ENEMY_ARTS),
            color=random.choice(ENEMY_COLORS),
            car_type="enemy",
        )
