from __future__ import annotations

import os
import pygame

from .constants import lane_center_x, CAR_W, CAR_H, LANE_WIDTH

# ── Load bus image once at import time ──────────────────────────
_bus_surface: pygame.Surface | None = None
BUS_W = 80   # display width  (fits within a lane)
BUS_H = 90   # display height

_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_BUS_PATH  = os.path.join(_ASSET_DIR, "school_bus.png")


def _load_bus() -> pygame.Surface | None:
    global _bus_surface
    if _bus_surface is not None:
        return _bus_surface
    try:
        raw = pygame.image.load(_BUS_PATH).convert_alpha()
        _bus_surface = pygame.transform.smoothscale(raw, (BUS_W, BUS_H))
        return _bus_surface
    except Exception:
        return None


class Enemy:
    __slots__ = ("lane", "y", "surface", "width", "height", "passed")

    def __init__(self, lane: int):
        self.lane   = lane
        self.y      = -BUS_H  # start above screen
        self.passed = False

        bus = _load_bus()
        if bus is not None:
            self.surface = bus
            self.width   = BUS_W
            self.height  = BUS_H
        else:
            # Fallback: coloured rectangle
            from .cars import make_car_surface
            from .factory import EnemyCarFactory
            spec = EnemyCarFactory().create()
            self.surface = make_car_surface(spec.color, is_player=False)
            self.width   = CAR_W
            self.height  = CAR_H

    @property
    def x(self) -> float:
        """Left x-pixel to center this enemy in its lane."""
        return lane_center_x(self.lane) - self.width / 2
