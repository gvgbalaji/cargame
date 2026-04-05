"""All Pygame drawing lives here. No game logic."""

import math
import random

import pygame

from .constants import (
    WIDTH, HEIGHT, NUM_LANES, LANE_WIDTH,
    ROAD_LEFT, ROAD_RIGHT, ROAD_WIDTH, ROAD_CENTER,
    COL_ASPHALT, COL_ASPHALT_L, COL_SHOULDER, COL_LANE_MARK,
    COL_EDGE_MARK, COL_GRASS, COL_GRASS_DARK, COL_GRASS_LIGHT,
    COL_SKY_TOP, COL_SKY_BOT,
)


class Renderer:
    """Handles all visual drawing to the Pygame display surface."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w = WIDTH
        self.h = HEIGHT
        self._build_background()
        self._build_tree_surface()

    # ── pre-rendered assets ─────────────────────────────────────

    def _build_background(self):
        """Pre-render the static background (sky + grass)."""
        self.bg = pygame.Surface((self.w, self.h))

        # Sky gradient
        for y in range(self.h):
            t = y / self.h
            r = int(COL_SKY_TOP[0] + (COL_SKY_BOT[0] - COL_SKY_TOP[0]) * t)
            g = int(COL_SKY_TOP[1] + (COL_SKY_BOT[1] - COL_SKY_TOP[1]) * t)
            b = int(COL_SKY_TOP[2] + (COL_SKY_BOT[2] - COL_SKY_TOP[2]) * t)
            pygame.draw.line(self.bg, (r, g, b), (0, y), (self.w, y))

        # Grass areas
        grass_left = pygame.Rect(0, 0, ROAD_LEFT - 8, self.h)
        grass_right = pygame.Rect(ROAD_RIGHT + 8, 0, self.w - ROAD_RIGHT - 8, self.h)
        pygame.draw.rect(self.bg, COL_GRASS, grass_left)
        pygame.draw.rect(self.bg, COL_GRASS, grass_right)

        # Grass stripes for texture
        for y in range(0, self.h, 12):
            c = COL_GRASS_DARK if (y // 12) % 2 == 0 else COL_GRASS_LIGHT
            pygame.draw.line(self.bg, c, (0, y), (ROAD_LEFT - 8, y), 2)
            pygame.draw.line(self.bg, c, (ROAD_RIGHT + 8, y), (self.w, y), 2)

        # Road surface
        road_rect = pygame.Rect(ROAD_LEFT - 8, 0, ROAD_WIDTH + 16, self.h)
        pygame.draw.rect(self.bg, COL_ASPHALT, road_rect)

        # Road shoulders
        pygame.draw.rect(self.bg, COL_SHOULDER, (ROAD_LEFT - 8, 0, 8, self.h))
        pygame.draw.rect(self.bg, COL_SHOULDER, (ROAD_RIGHT, 0, 8, self.h))

        # Edge lines (solid white)
        pygame.draw.rect(self.bg, COL_EDGE_MARK, (ROAD_LEFT - 2, 0, 3, self.h))
        pygame.draw.rect(self.bg, COL_EDGE_MARK, (ROAD_RIGHT - 1, 0, 3, self.h))

    def _build_tree_surface(self):
        """Pre-render a tree sprite."""
        self.tree_surf = pygame.Surface((40, 60), pygame.SRCALPHA)
        # Trunk
        pygame.draw.rect(self.tree_surf, (100, 70, 40), (15, 35, 10, 25))
        # Canopy layers
        pygame.draw.circle(self.tree_surf, (20, 100, 20), (20, 28), 18)
        pygame.draw.circle(self.tree_surf, (30, 130, 30), (20, 22), 15)
        pygame.draw.circle(self.tree_surf, (45, 155, 45), (20, 18), 10)

    # ── per-frame drawing ───────────────────────────────────────

    def draw_background(self):
        self.screen.blit(self.bg, (0, 0))

    def draw_lane_markings(self, scroll: float):
        """Draw dashed lane dividers that scroll."""
        dash_len = 40
        gap_len = 30
        cycle = dash_len + gap_len
        offset = scroll % cycle

        for lane in range(1, NUM_LANES):
            x = ROAD_LEFT + lane * LANE_WIDTH
            y = -offset
            while y < self.h:
                if y + dash_len > 0:
                    top = max(0, int(y))
                    bot = min(self.h, int(y + dash_len))
                    pygame.draw.rect(self.screen, COL_LANE_MARK,
                                     (x - 2, top, 4, bot - top))
                y += cycle

    def draw_road_grime(self, scroll: float):
        """Subtle road texture lines to break up flat asphalt."""
        rng = random.Random(42)
        for i in range(20):
            rx = rng.randint(ROAD_LEFT + 5, ROAD_RIGHT - 5)
            ry = (rng.randint(0, self.h) + int(scroll * 0.3)) % self.h
            pygame.draw.line(self.screen, COL_ASPHALT_L,
                             (rx, ry), (rx + rng.randint(-5, 5), ry + rng.randint(2, 8)), 1)

    def draw_trees(self, scroll: float):
        """Draw scrolling trees on both sides of the road."""
        spacing = 120
        offset = scroll % spacing

        for y_base in range(-60, self.h + 60, spacing):
            y = y_base + offset
            # Left side trees
            self.screen.blit(self.tree_surf, (ROAD_LEFT - 70, int(y)))
            self.screen.blit(self.tree_surf, (ROAD_LEFT - 130, int(y) + 50))
            # Right side trees
            self.screen.blit(self.tree_surf, (ROAD_RIGHT + 30, int(y) + 30))
            self.screen.blit(self.tree_surf, (ROAD_RIGHT + 90, int(y)))

    def draw_car(self, surf: pygame.Surface, x: float, y: float):
        """Draw a car surface at the given position."""
        self.screen.blit(surf, (int(x), int(y)))

    def draw_speed_lines(self, player_x: float, player_y: float, level: int):
        """Draw motion blur / speed lines behind the player car."""
        if level < 2:
            return
        intensity = min(level * 15, 180)
        num_lines = min(level * 2, 12)
        rng = random.Random(int(pygame.time.get_ticks() / 50))

        from .constants import CAR_H as _CH
        for _ in range(num_lines):
            lx = player_x + rng.randint(5, 50)
            ly = player_y + _CH + rng.randint(5, 40)
            length = rng.randint(20, 50 + level * 5)
            alpha = rng.randint(min(40, intensity), max(40, intensity))
            line_surf = pygame.Surface((2, length), pygame.SRCALPHA)
            line_surf.fill((200, 220, 255, alpha))
            self.screen.blit(line_surf, (int(lx), int(ly)))

    def draw_road_particles(self, scroll: float, level: int):
        """Small white dots zipping along the road at high speeds."""
        if level < 3:
            return
        count = min(level * 3, 25)
        rng = random.Random(int(scroll * 10) % 999)
        for _ in range(count):
            px = rng.randint(ROAD_LEFT + 5, ROAD_RIGHT - 5)
            py = rng.randint(0, self.h)
            alpha = rng.randint(30, 120)
            dot = pygame.Surface((3, 3), pygame.SRCALPHA)
            dot.fill((255, 255, 255, alpha))
            self.screen.blit(dot, (px, py))

    def draw_crash_flash(self):
        """Full-screen red flash overlay."""
        flash = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        flash.fill((255, 30, 30, 120))
        self.screen.blit(flash, (0, 0))
