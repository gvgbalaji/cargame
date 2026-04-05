"""Load player car images from assets/players/ and provide fallback drawing."""

import os
import pygame

from .constants import CAR_W, CAR_H

_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_PLAYERS_DIR = os.path.join(_ASSET_DIR, "players")

# ── Player styles: (display_name, filename) ─────────────────────
PLAYER_STYLES = [
    ("SEDAN",  "gray_sedan.png"),
    ("SUV",    "blue_suv.png"),
    ("PICKUP", "orange_pickup.png"),
    ("SPORTS", "green_sports.png"),
]

_player_cache: dict[int, pygame.Surface] = {}


def make_player_surface(style_index: int) -> pygame.Surface:
    """Load and return a player car surface for the given style index."""
    idx = style_index % len(PLAYER_STYLES)
    if idx in _player_cache:
        return _player_cache[idx]

    _name, filename = PLAYER_STYLES[idx]
    path = os.path.join(_PLAYERS_DIR, filename)

    try:
        raw = pygame.image.load(path).convert_alpha()
        # Scale to fit CAR_W x CAR_H preserving aspect ratio
        ow, oh = raw.get_size()
        scale = min(CAR_W / ow, CAR_H / oh)
        nw = max(1, int(ow * scale))
        nh = max(1, int(oh * scale))
        scaled = pygame.transform.smoothscale(raw, (nw, nh))

        # Center on a CAR_W x CAR_H transparent surface
        surf = pygame.Surface((CAR_W, CAR_H), pygame.SRCALPHA)
        sx = (CAR_W - nw) // 2
        sy = (CAR_H - nh) // 2
        surf.blit(scaled, (sx, sy))
        _player_cache[idx] = surf
        return surf
    except Exception:
        # Fallback: simple colored rectangle
        surf = pygame.Surface((CAR_W, CAR_H), pygame.SRCALPHA)
        pygame.draw.rect(surf, (100, 100, 110), (6, 6, CAR_W - 12, CAR_H - 12),
                         border_radius=8)
        _player_cache[idx] = surf
        return surf


def make_car_surface(color: tuple, is_player: bool = False) -> pygame.Surface:
    """Fallback: draw a simple colored car (used for enemies if no images)."""
    surf = pygame.Surface((CAR_W, CAR_H), pygame.SRCALPHA)
    r, g, b = color[:3]
    dark = (max(0, r - 60), max(0, g - 60), max(0, b - 60))

    pygame.draw.rect(surf, color, (8, 6, CAR_W - 16, CAR_H - 12), border_radius=8)
    pygame.draw.rect(surf, (50, 60, 70, 200), (14, 12, CAR_W - 28, 20), border_radius=4)
    pygame.draw.rect(surf, (50, 60, 70, 200), (12, CAR_H - 38, CAR_W - 24, 20), border_radius=4)

    wc = (30, 30, 35)
    pygame.draw.rect(surf, wc, (2, 10, 8, 20), border_radius=3)
    pygame.draw.rect(surf, wc, (CAR_W - 10, 10, 8, 20), border_radius=3)
    pygame.draw.rect(surf, wc, (2, CAR_H - 30, 8, 20), border_radius=3)
    pygame.draw.rect(surf, wc, (CAR_W - 10, CAR_H - 30, 8, 20), border_radius=3)

    if is_player:
        pygame.draw.rect(surf, (255, 40, 40), (10, 6, 12, 6), border_radius=2)
        pygame.draw.rect(surf, (255, 40, 40), (CAR_W - 22, 6, 12, 6), border_radius=2)
    else:
        pygame.draw.rect(surf, (255, 255, 200), (10, 6, 12, 6), border_radius=2)
        pygame.draw.rect(surf, (255, 255, 200), (CAR_W - 22, 6, 12, 6), border_radius=2)

    return surf
