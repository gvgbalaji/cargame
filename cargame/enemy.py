from __future__ import annotations

from .constants import lane_x
from .factory import CarSpec, EnemyCarFactory


class Enemy:
    __slots__ = ("lane", "y", "art", "color", "passed")

    def __init__(self, lane: int, spec: CarSpec | None = None):
        if spec is None:
            spec = EnemyCarFactory().create()
        self.lane   = lane
        self.y      = 1.0
        self.art    = spec.art
        self.color  = spec.color
        self.passed = False

    @property
    def x(self) -> int:
        return lane_x(self.lane)
