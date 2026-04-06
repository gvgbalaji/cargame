from __future__ import annotations

import os
import random

import pygame

from .constants import lane_center_x, CAR_W, CAR_H, LANE_WIDTH

# ── Vehicle sprite pool (loaded once) ───────────────────────────
_vehicle_pool: list[pygame.Surface] | None = None
_tanker_surface: pygame.Surface | None = None
_bomb_surface: pygame.Surface | None = None
_powerup_fire_surface: pygame.Surface | None = None
_powerup_boost_surface: pygame.Surface | None = None

_ASSET_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_VEHICLES   = os.path.join(_ASSET_DIR, "vehicles")

# Target sizes — cars are smaller, trucks/buses are bigger
_SMALL_W, _SMALL_H = 90, 90     # cars
_LARGE_W, _LARGE_H = 100, 120   # trucks, buses, semis

# Names of the "large" vehicles (taller aspect ratio)
_LARGE_NAMES = {"school_bus", "green_semi", "blue_truck"}

# Special enemies handled separately — excluded from random pool
_SPECIAL_ENEMIES = {"tanker"}


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
        stem = os.path.splitext(fname)[0]
        if stem in _SPECIAL_ENEMIES:
            continue  # handled as special enemy type
        path = os.path.join(_VEHICLES, fname)
        try:
            raw = pygame.image.load(path).convert_alpha()
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


def _load_tanker() -> pygame.Surface | None:
    """Load and scale the tanker vehicle image (same size as school_bus)."""
    global _tanker_surface
    if _tanker_surface is not None:
        return _tanker_surface
    path = os.path.join(_VEHICLES, "tanker.png")
    try:
        raw = pygame.image.load(path).convert_alpha()
        # Keep original landscape orientation; fit within 115×75
        tw, th = 115, 75
        ow, oh = raw.get_size()
        scale = min(tw / ow, th / oh)
        nw = max(1, int(ow * scale))
        nh = max(1, int(oh * scale))
        _tanker_surface = pygame.transform.smoothscale(raw, (nw, nh))
    except Exception:
        _tanker_surface = None
    return _tanker_surface


def _load_bomb() -> pygame.Surface | None:
    """Load and scale the bomb projectile image."""
    global _bomb_surface
    if _bomb_surface is not None:
        return _bomb_surface
    path = os.path.join(_ASSET_DIR, "bomb.png")
    try:
        raw = pygame.image.load(path).convert_alpha()
        # Scale to 48px tall — large enough to dodge
        ow, oh = raw.get_size()
        scale = min(44 / ow, 48 / oh)
        nw = max(1, int(ow * scale))
        nh = max(1, int(oh * scale))
        _bomb_surface = pygame.transform.smoothscale(raw, (nw, nh))
    except Exception:
        _bomb_surface = None
    return _bomb_surface


def _load_powerup_surfaces() -> tuple["pygame.Surface | None", "pygame.Surface | None"]:
    """Load fire and boost power-up icons (36×36) for road pickups."""
    global _powerup_fire_surface, _powerup_boost_surface
    if _powerup_fire_surface is not None:
        return _powerup_fire_surface, _powerup_boost_surface

    size = 36

    # Fire power-up — firepower.png
    fire_path = os.path.join(_ASSET_DIR, "firepower.png")
    try:
        raw = pygame.image.load(fire_path).convert_alpha()
        _powerup_fire_surface = pygame.transform.smoothscale(raw, (size, size))
    except Exception:
        _powerup_fire_surface = None

    # Boost power-up — booster.png
    boost_path = os.path.join(_ASSET_DIR, "booster.png")
    try:
        raw = pygame.image.load(boost_path).convert_alpha()
        _powerup_boost_surface = pygame.transform.smoothscale(raw, (size, size))
    except Exception:
        _powerup_boost_surface = None

    return _powerup_fire_surface, _powerup_boost_surface


class PowerUp:
    """A collectible power-up (fire or boost) that scrolls down the road.

    Timer starts once the icon enters the visible screen (y >= 0).
    Disappears after LIFETIME seconds if not collected.
    """
    # width and height removed from __slots__ — always equal to SIZE (class constant)
    __slots__ = ("lane", "y", "kind", "surface", "timer", "timer_started", "collected")
    LIFETIME = 2.0   # seconds visible before disappearing
    SIZE     = 36    # icon size in pixels

    def __init__(self, lane: int, kind: str):
        self.lane          = lane
        self.kind          = kind   # "fire" or "boost"
        self.timer         = self.LIFETIME
        self.timer_started = False
        self.collected     = False

        fire_surf, boost_surf = _load_powerup_surfaces()
        if kind == "fire":
            self.surface = fire_surf
        else:
            self.surface = boost_surf

        self.y = float(-self.SIZE)   # start just above screen

    @property
    def width(self) -> int:
        """Always SIZE — no per-instance storage needed."""
        return self.SIZE

    @property
    def height(self) -> int:
        """Always SIZE — no per-instance storage needed."""
        return self.SIZE

    @property
    def x(self) -> float:
        return lane_center_x(self.lane) - self.SIZE / 2

    def tick(self, dt: float) -> bool:
        """Update timer. Returns True while still alive."""
        if self.collected:
            return False
        if self.y >= 0 and not self.timer_started:
            self.timer_started = True
        if self.timer_started:
            self.timer -= dt
        return self.timer > 0 and not self.collected


class Enemy:
    # width and height removed from __slots__ — derived from surface via properties
    __slots__ = ("lane", "y", "surface", "passed")

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

        self.y = float(-self.surface.get_height())  # start above screen

    @property
    def width(self) -> int:
        """Derived from surface — no redundant per-instance storage."""
        return self.surface.get_width()

    @property
    def height(self) -> int:
        """Derived from surface — no redundant per-instance storage."""
        return self.surface.get_height()

    @property
    def x(self) -> float:
        """Left x-pixel to center this enemy in its lane."""
        return lane_center_x(self.lane) - self.width / 2


class Tanker:
    """Special enemy that fires bomb projectiles after level 5."""
    # width and height removed from __slots__ — derived from surface via properties
    __slots__ = ("lane", "y", "surface", "passed",
                 "fire_timer", "fire_interval", "burst_remaining", "burst_delay")

    def __init__(self, lane: int):
        self.lane   = lane
        self.passed = False

        surf = _load_tanker()
        if surf is None:
            # Fallback to a regular vehicle
            pool = _load_vehicles()
            surf = random.choice(pool) if pool else pygame.Surface((100, 80))
        self.surface = surf
        self.y       = float(-self.surface.get_height())

        self.fire_timer      = 0.0                       # fire on first visible frame
        self.fire_interval   = random.uniform(1.2, 2.2) # seconds between shots
        self.burst_remaining = 0      # extra shots in current burst
        self.burst_delay     = 0.0    # countdown for next burst shot

    @property
    def width(self) -> int:
        """Derived from surface — no redundant per-instance storage."""
        return self.surface.get_width()

    @property
    def height(self) -> int:
        """Derived from surface — no redundant per-instance storage."""
        return self.surface.get_height()

    @property
    def x(self) -> float:
        return lane_center_x(self.lane) - self.width / 2

    def tick(self, dt: float) -> int:
        """
        Returns number of bombs to fire this frame.
        Handles single shots and occasional 2-bomb bursts.
        """
        shots = 0

        # Burst follow-up shot
        if self.burst_remaining > 0:
            self.burst_delay -= dt
            if self.burst_delay <= 0:
                shots += 1
                self.burst_remaining -= 1
                self.burst_delay = 0.35

        # Main fire timer
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = self.fire_interval
            shots += 1
            # 40% chance of a quick second shot
            if random.random() < 0.40 and self.burst_remaining == 0:
                self.burst_remaining = 1
                self.burst_delay = 0.35

        return shots


class Bomb:
    """Projectile fired by a Tanker toward the player."""
    # width and height removed from __slots__ — derived from surface via properties
    __slots__ = ("x", "y", "surface", "passed", "speed_bonus")

    def __init__(self, x: float, y: float):
        surf = _load_bomb()
        if surf is None:
            # Fallback: orange-red circle bomb
            size = 44
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 60, 0), (size // 2, size // 2), size // 2)
            pygame.draw.circle(surf, (255, 160, 40), (size // 2 - 5, size // 2 - 5), size // 5)
        self.surface    = surf
        self.x          = x - surf.get_width() / 2   # center on given x
        self.y          = float(y)
        self.passed     = False
        self.speed_bonus = random.uniform(2.5, 4.5)  # extra px/frame above scroll

    @property
    def width(self) -> int:
        """Derived from surface — no redundant per-instance storage."""
        return self.surface.get_width()

    @property
    def height(self) -> int:
        """Derived from surface — no redundant per-instance storage."""
        return self.surface.get_height()


class Bullet:
    """Player-fired projectile that travels upward toward enemies."""
    __slots__ = ("x", "y", "active")
    W      = 8
    H      = 24
    SPEED  = 16   # pixels per frame upward

    def __init__(self, cx: float, bottom_y: float):
        self.x      = cx - self.W / 2
        self.y      = float(bottom_y - self.H)
        self.active = True
