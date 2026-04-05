"""All Pygame drawing lives here. No game logic."""

import math
import os
import random

import pygame

from .constants import (
    WIDTH, HEIGHT, NUM_LANES, LANE_WIDTH,
    ROAD_LEFT, ROAD_RIGHT, ROAD_WIDTH, ROAD_CENTER,
    COL_ASPHALT, COL_ASPHALT_L, COL_SHOULDER, COL_LANE_MARK,
    COL_EDGE_MARK,
)

_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

# ── Scene moods ──────────────────────────────────────────────
SCENE_DAY    = 0
SCENE_SUNSET = 1
SCENE_NIGHT  = 2

_SCENE_COLORS = {
    SCENE_DAY: {
        "sky_top": (100, 170, 255), "sky_bot": (180, 220, 255),
        "grass": (34, 120, 34), "grass_dk": (28, 95, 28), "grass_lt": (45, 145, 45),
        "tree_trunk": (100, 70, 40),
        "tree_c1": (20, 100, 20), "tree_c2": (30, 130, 30), "tree_c3": (45, 155, 45),
    },
    SCENE_SUNSET: {
        "sky_top": (40, 20, 80), "sky_bot": (220, 110, 50),
        "grass": (50, 95, 30), "grass_dk": (40, 75, 25), "grass_lt": (60, 110, 35),
        "tree_trunk": (80, 55, 30),
        "tree_c1": (30, 75, 20), "tree_c2": (40, 95, 25), "tree_c3": (55, 115, 35),
    },
    SCENE_NIGHT: {
        "sky_top": (8, 8, 25), "sky_bot": (20, 20, 50),
        "grass": (15, 55, 20), "grass_dk": (10, 40, 15), "grass_lt": (20, 65, 25),
        "tree_trunk": (50, 35, 20),
        "tree_c1": (10, 50, 12), "tree_c2": (15, 60, 15), "tree_c3": (22, 72, 22),
    },
}


def _scene_for_level(level: int) -> int:
    if level <= 4:
        return SCENE_DAY
    elif level <= 8:
        return SCENE_SUNSET
    return SCENE_NIGHT


class _Bird:
    __slots__ = ("x", "y", "vx", "vy", "wing_phase", "wing_speed", "size")

    def __init__(self, rng: random.Random):
        self.size = rng.randint(4, 8)
        self.wing_speed = rng.uniform(4.0, 8.0)
        self.wing_phase = rng.uniform(0, math.pi * 2)
        # Fly left-to-right or right-to-left
        if rng.random() < 0.5:
            self.x = float(-20)
            self.vx = rng.uniform(0.8, 2.0)
        else:
            self.x = float(WIDTH + 20)
            self.vx = rng.uniform(-2.0, -0.8)
        self.y = float(rng.randint(20, 180))
        self.vy = rng.uniform(-0.3, 0.3)


class Renderer:
    """Handles all visual drawing to the Pygame display surface."""

    MAX_BIRDS = 8

    CURVE_AMP = 55  # max horizontal shift in pixels (sum of wave amplitudes)

    def __init__(self, screen: pygame.Surface, curvy: bool = False):
        self.screen = screen
        self.w = WIDTH
        self.h = HEIGHT
        self.curvy = curvy
        self._scene = SCENE_DAY
        self._build_background()
        self._build_tree_surface()
        self._build_mountain_surface()
        self._stars: list[tuple[int, int, int]] = []
        self._gen_stars()
        self._birds: list[_Bird] = []
        self._bird_timer = 0.0
        self._headlight_img: pygame.Surface | None = None
        self._load_headlights()

    def _load_headlights(self):
        path = os.path.join(_ASSET_DIR, "headlights.png")
        try:
            raw = pygame.image.load(path).convert_alpha()
            from .constants import CAR_W
            # Scale to match car width, keep aspect ratio
            scale_w = int(CAR_W * 1.4)
            scale_h = int(raw.get_height() * scale_w / raw.get_width())
            self._headlight_img = pygame.transform.smoothscale(raw, (scale_w, scale_h))
        except Exception:
            self._headlight_img = None

    def update_scene(self, level: int):
        new = _scene_for_level(level)
        if new != self._scene:
            self._scene = new
            self._build_background()
            self._build_tree_surface()
            self._build_mountain_surface()

    def road_curve(self, y: float, scroll: float) -> float:
        """Horizontal offset of the road at screen-row y."""
        if not self.curvy:
            return 0.0
        # Multiple sine waves with irrational ratios → non-repeating organic curves
        v = y + scroll
        return (math.sin(v * 0.0037) * 25
              + math.sin(v * 0.0018) * 18
              + math.sin(v * 0.0064) * 12)

    # ── pre-rendered assets ─────────────────────────────────────

    def _pal(self):
        return _SCENE_COLORS[self._scene]

    def _build_background(self):
        """Pre-render sky gradient + full grass. Road drawn per-frame for curves."""
        pal = self._pal()
        self.bg = pygame.Surface((self.w, self.h))
        sky_top, sky_bot = pal["sky_top"], pal["sky_bot"]
        grass, grass_dk, grass_lt = pal["grass"], pal["grass_dk"], pal["grass_lt"]

        # Sky gradient over full screen
        for y in range(self.h):
            t = y / self.h
            r = int(sky_top[0] + (sky_bot[0] - sky_top[0]) * t)
            g = int(sky_top[1] + (sky_bot[1] - sky_top[1]) * t)
            b = int(sky_top[2] + (sky_bot[2] - sky_top[2]) * t)
            pygame.draw.line(self.bg, (r, g, b), (0, y), (self.w, y))

        # Grass covers the full width — curved road will be painted on top each frame
        pygame.draw.rect(self.bg, grass, (0, 0, self.w, self.h))

        # Re-draw sky gradient only in the far margins where grass never appears
        for y in range(self.h):
            t = y / self.h
            r = int(sky_top[0] + (sky_bot[0] - sky_top[0]) * t)
            g = int(sky_top[1] + (sky_bot[1] - sky_top[1]) * t)
            b = int(sky_top[2] + (sky_bot[2] - sky_top[2]) * t)
            pygame.draw.line(self.bg, (r, g, b), (0, y), (self.w, y))

        # Grass rectangles on both side bands
        left_end = ROAD_LEFT - self.CURVE_AMP - 10
        right_start = ROAD_RIGHT + self.CURVE_AMP + 10
        pygame.draw.rect(self.bg, grass, (0, 0, left_end, self.h))
        pygame.draw.rect(self.bg, grass, (right_start, 0, self.w - right_start, self.h))
        # Grass stripe texture
        for y in range(0, self.h, 12):
            c = grass_dk if (y // 12) % 2 == 0 else grass_lt
            pygame.draw.line(self.bg, c, (0, y), (left_end, y), 2)
            pygame.draw.line(self.bg, c, (right_start, y), (self.w, y), 2)

    def _build_tree_surface(self):
        """Pre-render a tree sprite matching the current scene palette."""
        pal = self._pal()
        self.tree_surf = pygame.Surface((40, 60), pygame.SRCALPHA)
        pygame.draw.rect(self.tree_surf, pal["tree_trunk"], (15, 35, 10, 25))
        pygame.draw.circle(self.tree_surf, pal["tree_c1"], (20, 28), 18)
        pygame.draw.circle(self.tree_surf, pal["tree_c2"], (20, 22), 15)
        pygame.draw.circle(self.tree_surf, pal["tree_c3"], (20, 18), 10)

    def _build_mountain_surface(self):
        """Pre-render a mountain range silhouette."""
        pal = self._pal()
        w, h = ROAD_LEFT - 8, 300
        self.mountain_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # Far mountains (lighter)
        base_c = pal["grass_dk"]
        far_c = (base_c[0] + 30, base_c[1] + 20, base_c[2] + 40)
        peaks_far = [(0, h), (0, 120), (30, 80), (55, 50), (80, 70),
                     (100, 30), (130, 60), (w, 100), (w, h)]
        pygame.draw.polygon(self.mountain_surf, far_c, peaks_far)
        # Near mountains (darker)
        near_c = (base_c[0] + 10, base_c[1] + 5, base_c[2] + 15)
        peaks_near = [(0, h), (0, 180), (40, 130), (70, 100), (95, 140),
                      (120, 90), (w, 150), (w, h)]
        pygame.draw.polygon(self.mountain_surf, near_c, peaks_near)
        # Snow caps
        if self._scene == SCENE_NIGHT:
            snow_c = (140, 150, 170, 120)
        else:
            snow_c = (230, 235, 245, 180)
        snow_pts = [(45, 55), (55, 50), (65, 55)]
        pygame.draw.polygon(self.mountain_surf, snow_c, snow_pts)
        snow_pts2 = [(90, 35), (100, 30), (110, 35)]
        pygame.draw.polygon(self.mountain_surf, snow_c, snow_pts2)

    def _gen_stars(self):
        rng = random.Random(777)
        self._stars = [(rng.randint(0, self.w), rng.randint(0, self.h // 2),
                        rng.randint(1, 3)) for _ in range(80)]

    # ── per-frame drawing ───────────────────────────────────────

    def draw_background(self):
        self.screen.blit(self.bg, (0, 0))

    def draw_road(self, scroll: float):
        """Draw the curved road surface, shoulders, and edge lines."""
        pal = self._pal()
        grass = pal["grass"]
        grass_dk, grass_lt = pal["grass_dk"], pal["grass_lt"]
        left_end = ROAD_LEFT - self.CURVE_AMP - 10
        right_start = ROAD_RIGHT + self.CURVE_AMP + 10

        # Pre-compute curve offsets and draw 2-pixel-tall strips
        for y in range(0, self.h, 2):
            cx = self.road_curve(y, scroll)
            il = int(ROAD_LEFT + cx)
            ir = int(ROAD_RIGHT + cx)

            # Grass fill in the curve gap
            gc = grass_dk if (y // 12) % 2 == 0 else grass_lt
            pygame.draw.line(self.screen, gc, (left_end, y), (il - 8, y), 2)
            pygame.draw.line(self.screen, gc, (ir + 8, y), (right_start, y), 2)

            # Road surface
            pygame.draw.line(self.screen, COL_ASPHALT, (il - 8, y), (ir + 8, y), 2)
            # Shoulders
            pygame.draw.line(self.screen, COL_SHOULDER, (il - 8, y), (il, y), 2)
            pygame.draw.line(self.screen, COL_SHOULDER, (ir, y), (ir + 8, y), 2)
            # Edge lines (2px wide)
            pygame.draw.line(self.screen, COL_EDGE_MARK, (il - 1, y), (il + 1, y), 2)
            pygame.draw.line(self.screen, COL_EDGE_MARK, (ir - 1, y), (ir + 1, y), 2)

    def draw_sun_moon(self):
        """Draw sun (day/sunset) or moon + stars (night)."""
        ticks = pygame.time.get_ticks()

        if self._scene == SCENE_DAY:
            # Bright sun top-left area
            sx, sy = 80, 70
            # Glow
            glow = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 240, 100, 50), (60, 60), 55)
            self.screen.blit(glow, (sx - 60, sy - 60))
            # Sun body
            pygame.draw.circle(self.screen, (255, 230, 60), (sx, sy), 30)
            pygame.draw.circle(self.screen, (255, 250, 150), (sx - 5, sy - 5), 12)
            # Rays
            for i in range(8):
                angle = math.radians(i * 45 + (ticks / 40) % 360)
                rx = sx + int(math.cos(angle) * 42)
                ry = sy + int(math.sin(angle) * 42)
                rx2 = sx + int(math.cos(angle) * 52)
                ry2 = sy + int(math.sin(angle) * 52)
                pygame.draw.line(self.screen, (255, 230, 60, 200),
                                 (rx, ry), (rx2, ry2), 2)

        elif self._scene == SCENE_SUNSET:
            # Lower sun with orange glow
            sx, sy = 90, 140
            glow = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 140, 40, 40), (80, 80), 70)
            self.screen.blit(glow, (sx - 80, sy - 80))
            pygame.draw.circle(self.screen, (255, 120, 30), (sx, sy), 28)
            pygame.draw.circle(self.screen, (255, 180, 80), (sx - 4, sy - 4), 12)

        else:  # NIGHT
            # Stars (twinkle)
            for sx, sy, sz in self._stars:
                twinkle = abs(math.sin((ticks / 800.0) + sx * 0.1)) * 0.5 + 0.5
                alpha = int(100 + twinkle * 155)
                c = (200, 210, 255, alpha)
                star_surf = pygame.Surface((sz * 2 + 1, sz * 2 + 1), pygame.SRCALPHA)
                pygame.draw.circle(star_surf, c, (sz, sz), sz)
                self.screen.blit(star_surf, (sx - sz, sy - sz))

            # Moon
            mx, my = self.w - 100, 65
            pygame.draw.circle(self.screen, (220, 225, 240), (mx, my), 28)
            pygame.draw.circle(self.screen, (200, 210, 230), (mx - 3, my - 3), 10)
            # Crescent shadow
            pygame.draw.circle(self.screen,
                               _SCENE_COLORS[SCENE_NIGHT]["sky_top"],
                               (mx + 10, my - 6), 22)
            # Moon glow
            glow = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.circle(glow, (180, 200, 255, 25), (50, 50), 45)
            self.screen.blit(glow, (mx - 50, my - 50))

    def draw_birds(self, dt: float):
        """Animate V-shaped birds flying across the top of the screen."""
        ticks = pygame.time.get_ticks()

        # Spawn new birds occasionally
        self._bird_timer += dt
        if self._bird_timer > 1.5 and len(self._birds) < self.MAX_BIRDS:
            self._bird_timer = 0.0
            if random.random() < 0.4:
                self._birds.append(_Bird(random))

        alive = []
        for b in self._birds:
            b.x += b.vx
            b.y += b.vy
            if -30 < b.x < self.w + 30:
                alive.append(b)
                # Draw V-shape with flapping wings
                wing = math.sin(ticks / 1000.0 * b.wing_speed + b.wing_phase)
                wy = int(wing * b.size * 0.6)
                bx, by = int(b.x), int(b.y)
                if self._scene == SCENE_NIGHT:
                    c = (120, 130, 150)
                else:
                    c = (30, 30, 30)
                pygame.draw.line(self.screen, c,
                                 (bx - b.size, by + wy), (bx, by), 2)
                pygame.draw.line(self.screen, c,
                                 (bx, by), (bx + b.size, by + wy), 2)
        self._birds = alive

    def draw_mountains(self, level: int):
        """Draw mountain silhouettes on the left side from level 6+."""
        if level < 6:
            return
        # Fade in over levels 6-7
        alpha = min(255, (level - 5) * 128)
        if alpha < 255:
            tmp = self.mountain_surf.copy()
            tmp.set_alpha(alpha)
            self.screen.blit(tmp, (0, self.h - 300))
        else:
            self.screen.blit(self.mountain_surf, (0, self.h - 300))

    def draw_river(self, scroll: float, level: int):
        """Draw a meandering zig-zag river on the right side from level 8+."""
        if level < 8:
            return
        ticks = pygame.time.get_ticks()
        base_alpha = min(220, (level - 7) * 110)

        # Scene-based water palette
        if self._scene == SCENE_NIGHT:
            water_color = (15, 40, 80, base_alpha)
            wave_color = (40, 70, 120)
            sparkle_color = (120, 160, 220)
            bank_color = (30, 25, 15, base_alpha)
        elif self._scene == SCENE_SUNSET:
            water_color = (40, 60, 120, base_alpha)
            wave_color = (80, 90, 150)
            sparkle_color = (220, 160, 100)
            bank_color = (50, 35, 20, base_alpha)
        else:
            water_color = (30, 90, 180, base_alpha)
            wave_color = (60, 130, 210)
            sparkle_color = (180, 220, 255)
            bank_color = (60, 45, 25, base_alpha)

        # River center meanders with a zig-zag sine curve
        river_base_x = ROAD_RIGHT + 75
        river_w = 55
        flow_offset = (ticks / 400.0) % (math.pi * 2)

        # Draw river as a series of horizontal slices following zig-zag path
        river_area = pygame.Surface((self.w - ROAD_RIGHT, self.h), pygame.SRCALPHA)
        for y in range(0, self.h, 2):
            # Zig-zag: combine two sine waves for a natural meander
            meander = math.sin((y + scroll * 0.4) * 0.012) * 35 \
                    + math.sin((y + scroll * 0.4) * 0.025) * 15
            cx = int(river_base_x - ROAD_RIGHT + meander)
            half_w = river_w // 2

            # Bank edges (wider, dark)
            lx = max(0, cx - half_w - 5)
            rx = min(self.w - ROAD_RIGHT, cx + half_w + 5)
            pygame.draw.line(river_area, bank_color, (lx, y), (rx, y), 2)

            # Water fill
            lx_w = max(0, cx - half_w)
            rx_w = min(self.w - ROAD_RIGHT, cx + half_w)
            pygame.draw.line(river_area, water_color, (lx_w, y), (rx_w, y), 2)

        # Flowing wave highlights following the meander
        wave_scroll = (ticks / 250.0) % 30
        for wy in range(-30, self.h + 30, 15):
            y = wy + int(wave_scroll)
            if 0 <= y < self.h:
                meander = math.sin((y + scroll * 0.4) * 0.012) * 35 \
                        + math.sin((y + scroll * 0.4) * 0.025) * 15
                cx = int(river_base_x - ROAD_RIGHT + meander)
                wiggle = int(math.sin((y + ticks / 300.0) * 0.08) * 6)
                pygame.draw.line(river_area, (*wave_color, 100),
                                 (cx + wiggle - 10, y), (cx + wiggle + 10, y), 1)

        # Sparkles
        rng = random.Random(int(ticks / 200) % 50)
        for _ in range(8):
            sy = rng.randint(0, self.h)
            meander = math.sin((sy + scroll * 0.4) * 0.012) * 35 \
                    + math.sin((sy + scroll * 0.4) * 0.025) * 15
            sx = int(river_base_x - ROAD_RIGHT + meander + rng.randint(-20, 20))
            if 0 < sx < self.w - ROAD_RIGHT:
                pygame.draw.circle(river_area, (*sparkle_color, 160), (sx, sy), 2)

        self.screen.blit(river_area, (ROAD_RIGHT, 0))

    def draw_headlights(self, player_x: float, player_y: float):
        """Overlay headlight image in front of the player car at night."""
        if self._scene != SCENE_NIGHT:
            return
        if self._headlight_img is None:
            return

        from .constants import CAR_W
        img = self._headlight_img
        # Center horizontally on the car, place above (in front of) the car
        hx = int(player_x + CAR_W / 2 - img.get_width() / 2)
        hy = int(player_y - img.get_height() + 20)
        self.screen.blit(img, (hx, hy))

    def draw_lane_markings(self, scroll: float):
        """Draw dashed lane dividers that follow the road curve."""
        dash_len = 40
        gap_len = 30
        cycle = dash_len + gap_len
        offset = scroll % cycle

        for lane in range(1, NUM_LANES):
            base_x = ROAD_LEFT + lane * LANE_WIDTH
            y = -offset
            while y < self.h:
                if y + dash_len > 0:
                    top = max(0, int(y))
                    bot = min(self.h, int(y + dash_len))
                    # Draw dash as series of points following the curve
                    for dy in range(top, bot, 2):
                        cx = self.road_curve(dy, scroll)
                        px = int(base_x + cx)
                        pygame.draw.line(self.screen, COL_LANE_MARK,
                                         (px - 1, dy), (px + 1, dy), 2)
                y += cycle

    def draw_road_grime(self, scroll: float):
        """Subtle road texture lines to break up flat asphalt."""
        rng = random.Random(42)
        for i in range(20):
            rx = rng.randint(ROAD_LEFT + 5, ROAD_RIGHT - 5)
            ry = (rng.randint(0, self.h) + int(scroll * 0.3)) % self.h
            cx = self.road_curve(ry, scroll)
            pygame.draw.line(self.screen, COL_ASPHALT_L,
                             (int(rx + cx), ry),
                             (int(rx + cx + rng.randint(-5, 5)), ry + rng.randint(2, 8)), 1)

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

    def draw_car(self, surf: pygame.Surface, x: float, y: float,
                 scroll: float = 0.0):
        """Draw a car surface at the given position, shifted by road curve."""
        cx = self.road_curve(y + surf.get_height() / 2, scroll)
        self.screen.blit(surf, (int(x + cx), int(y)))

    def draw_speed_lines(self, player_x: float, player_y: float,
                         level: int, scroll: float = 0.0):
        """Draw motion blur / speed lines behind the player car."""
        if level < 2:
            return
        intensity = min(level * 15, 180)
        num_lines = min(level * 2, 12)
        rng = random.Random(int(pygame.time.get_ticks() / 50))

        from .constants import CAR_H as _CH
        cx = self.road_curve(player_y + _CH, scroll)
        for _ in range(num_lines):
            lx = player_x + cx + rng.randint(5, 50)
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
            cx = self.road_curve(py, scroll)
            alpha = rng.randint(30, 120)
            dot = pygame.Surface((3, 3), pygame.SRCALPHA)
            dot.fill((255, 255, 255, alpha))
            self.screen.blit(dot, (int(px + cx), py))

    def draw_crash_flash(self):
        """Full-screen red flash overlay."""
        flash = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        flash.fill((255, 30, 30, 120))
        self.screen.blit(flash, (0, 0))
