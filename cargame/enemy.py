from __future__ import annotations

import os
import random

import pygame

from .constants import lane_center_x, CAR_W, CAR_H, LANE_WIDTH

# ── Vehicle sprite pool (loaded once) ───────────────────────────
_vehicle_pool: list[pygame.Surface] | None = None

_ASSET_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_VEHICLES   = os.path.join(_ASSET_DIR, "vehicles")

# Target sizes — cars are smaller, trucks/buses are bigger
_SMALL_W, _SMALL_H = 90, 90     # cars
_LARGE_W, _LARGE_H = 100, 120   # trucks, buses, semis

# Names of the "large" vehicles (taller aspect ratio)
_LARGE_NAMES = {"school_bus", "green_semi", "blue_truck"}


def _load_vehicles() -> list[pygame.Surface]:
    """Load all vehicle PNGs from assets/vehicles/, scaled to fit lanes."""
    global _vehicle_pool
    if _vehicle_pool is not None:
        return _vehicle_pool

    _vehicle_pool = []
    if not os.path.isdir(_VEHICLES):
        return _vehicle_pool

    for fname in sorted(os.listdir(_VEHICLES)):
        if not fname.endswith(".png"):
            continue
        path = os.path.join(_VEHICLES, fname)
        try:
            raw = pygame.image.load(path).convert_alpha()
            stem = os.path.splitext(fname)[0]
            if stem in _LARGE_NAMES:
                tw, th = _LARGE_W, _LARGE_H
            else:
                tw, th = _SMALL_W, _SMALL_H

            # Scale preserving aspect ratio, fit within (tw, th)
            ow, oh = raw.get_size()
            scale = min(tw / ow, th / oh)
            nw = max(1, int(ow * scale))
            nh = max(1, int(oh * scale))
            scaled = pygame.transform.smoothscale(raw, (nw, nh))
            _vehicle_pool.append(scaled)
        except Exception:
            continue

    return _vehicle_pool


class Enemy:
    __slots__ = ("lane", "y", "surface", "width", "height", "passed")

    def __init__(self, lane: int):
        self.lane   = lane
        self.passed = False

        pool = _load_vehicles()
        if pool:
            self.surface = random.choice(pool)
        else:
            # Ultimate fallback — plain rectangle
            from .cars import make_car_surface
            from .factory import EnemyCarFactory
            spec = EnemyCarFactory().create()
            self.surface = make_car_surface(spec.color, is_player=False)

        self.width  = self.surface.get_width()
        self.height = self.surface.get_height()
        self.y      = float(-self.height)  # start above screen

    @property
    def x(self) -> float:
        """Left x-pixel to center this enemy in its lane."""
        return lane_center_x(self.lane) - self.width / 2
