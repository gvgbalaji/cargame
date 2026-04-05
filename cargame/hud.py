"""Rich HUD overlay — speedometer, progress, score, popups, confetti, booster."""

import json
import math
import os
import random

import pygame

from .constants import (
    WIDTH, HEIGHT,
    COL_HUD_BG, COL_HUD_BORDER, COL_HUD_TEXT, COL_HUD_ACCENT,
    COL_HUD_WARN, COL_HUD_GOOD, COL_HUD_GOLD, COL_HUD_DIM,
)

_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

def _load_f1_facts() -> list[str]:
    path = os.path.join(_ASSET_DIR, "facts", "f1_facts.json")
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return [item["text"] for item in data]
    except Exception:
        return ["Trust the RNG", "Speed is life", "No brakes club"]

_F1_FACTS = _load_f1_facts()

# ── Confetti colors ─────────────────────────────────────────────
_CONFETTI_COLORS = [
    (255, 60, 60), (60, 200, 255), (255, 215, 0),
    (80, 255, 120), (255, 100, 200), (255, 140, 40),
    (180, 80, 255), (255, 255, 255),
]


class ConfettiParticle:
    """A single confetti piece — pre-allocated, reusable."""
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "rot", "rot_speed", "life")

    def __init__(self):
        self.reset(0, 0)

    def reset(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(1, 4)
        self.color = random.choice(_CONFETTI_COLORS)
        self.size = random.randint(4, 8)
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)
        self.life = 1.0

    def update(self, dt: float) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15  # gravity
        self.vx *= 0.99
        self.rot += self.rot_speed
        self.life -= dt * 0.5
        return self.life > 0 and self.y < HEIGHT + 20

    def draw(self, screen: pygame.Surface):
        alpha = max(0, min(255, int(self.life * 255)))
        s = self.size
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        c = (*self.color, alpha)
        pygame.draw.rect(surf, c, (0, 0, s, s))
        rotated = pygame.transform.rotate(surf, self.rot)
        screen.blit(rotated, (int(self.x), int(self.y)))


class HUD:
    """Draws all heads-up display elements."""

    # Mute icon rect — used for click detection in game.py
    MUTE_ICON_RECT = pygame.Rect(15, HEIGHT - 90, 42, 42)

    def __init__(self):
        pygame.font.init()
        self.font_huge  = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_med   = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 15)
        self.font_tiny  = pygame.font.SysFont("Arial", 12)

        # Floating text popups
        self.popups: list[tuple[str, float, float, float, tuple]] = []

        # Confetti particles (pre-allocate pool)
        self.confetti: list[ConfettiParticle] = []

        # Booster image
        self._booster_img: pygame.Surface | None = None
        self._load_booster()

        # Score medal, race flag, firepower images
        self._medal_img:        pygame.Surface | None = None
        self._flag_img:         pygame.Surface | None = None
        self._firepower_icon:   pygame.Surface | None = None
        self._firepower_bullet: pygame.Surface | None = None
        self._load_hud_images()

        # F1 fact — one random fact per game session
        self._fact_text = random.choice(_F1_FACTS)

    def _load_hud_images(self):
        specs = [
            ("_medal_img",       "score.png",     (72, 72)),
            ("_flag_img",        "flag.png",       (62, 56)),
            ("_firepower_icon",  "firepower.png",  (44, 44)),   # indicator stack
            ("_firepower_bullet","firepower.png",  (32, 32)),   # in-flight bullet
        ]
        for attr, fname, size in specs:
            path = os.path.join(_ASSET_DIR, fname)
            try:
                raw = pygame.image.load(path).convert_alpha()
                setattr(self, attr, pygame.transform.smoothscale(raw, size))
            except Exception:
                setattr(self, attr, None)

    def _load_booster(self):
        path = os.path.join(_ASSET_DIR, "booster.png")
        try:
            raw = pygame.image.load(path).convert_alpha()
            self._booster_img = pygame.transform.smoothscale(raw, (120, 102))
        except Exception:
            self._booster_img = None

    # ── helper ──────────────────────────────────────────────────

    def new_fact(self):
        """Pick a new random F1 fact (call on game reset)."""
        self._fact_text = random.choice(_F1_FACTS)

    @staticmethod
    def _draw_panel(screen: pygame.Surface, rect: pygame.Rect,
                    alpha: int = 180, border_color=COL_HUD_BORDER):
        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 10, 15, alpha), (0, 0, rect.w, rect.h),
                         border_radius=10)
        pygame.draw.rect(panel, border_color, (0, 0, rect.w, rect.h),
                         width=2, border_radius=10)
        screen.blit(panel, rect.topleft)

    # ── top bar ─────────────────────────────────────────────────

    def draw_top_bar(self, screen: pygame.Surface, score: int, level: int,
                     best: int, cars_to_next: int):
        # ── Score panel (right) with gold medal ─────────────────
        sp_w, sp_h = 240, 90
        sx = WIDTH - sp_w - 255
        self._draw_panel(screen, pygame.Rect(sx, 8, sp_w, sp_h),
                         border_color=COL_HUD_GOLD)

        if self._medal_img:
            screen.blit(self._medal_img, (sx + 6, 3))
            text_x = sx + 86
        else:
            text_x = sx + 12

        screen.blit(self.font_small.render("SCORE", True, COL_HUD_DIM),
                    (text_x, 14))
        score_val = self.font_large.render(str(score), True, COL_HUD_TEXT)
        screen.blit(score_val, (text_x, 32))
        screen.blit(self.font_tiny.render(f"BEST  {best}", True, COL_HUD_GOLD),
                    (text_x, 55))
        screen.blit(self.font_tiny.render("(all time)", True, COL_HUD_DIM),
                    (text_x, 68))

        # ── Level panel (far right) with checkered flag ──────────
        lp_w, lp_h = 240, 90
        lx = WIDTH - lp_w - 10
        self._draw_panel(screen, pygame.Rect(lx, 8, lp_w, lp_h),
                         border_color=(255, 80, 80))

        if self._flag_img:
            screen.blit(self._flag_img, (lx + 6, 14))
            lvl_text_x = lx + 78
        else:
            lvl_text_x = lx + 12

        screen.blit(self.font_small.render("LEVEL", True, COL_HUD_DIM),
                    (lvl_text_x, 14))
        screen.blit(self.font_large.render(f"{level:02d}", True, COL_HUD_GOLD),
                    (lvl_text_x, 32))

        progress = (5 - cars_to_next) / 5.0
        bx2 = lvl_text_x
        bw2 = lp_w - (lvl_text_x - lx) - 12
        pygame.draw.rect(screen, (30, 30, 40), (bx2, 67, bw2, 12), border_radius=6)
        fw = int(bw2 * progress)
        if fw > 0:
            pygame.draw.rect(screen, COL_HUD_ACCENT, (bx2, 67, fw, 12), border_radius=6)
        screen.blit(self.font_tiny.render(f"{5 - cars_to_next}/5", True, COL_HUD_DIM),
                    (bx2 + bw2 + 4, 68))

    # ── speedometer ─────────────────────────────────────────────

    def draw_speedometer(self, screen: pygame.Surface, speed_pct: float,
                         speed_display: int):
        cx = WIDTH - 100
        cy = HEIGHT - 110
        radius = 75

        panel = pygame.Surface((180, 180), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 10, 15, 160), (0, 0, 180, 180),
                         border_radius=15)
        screen.blit(panel, (cx - 90, cy - 90))

        start_angle = math.radians(135)
        end_angle   = math.radians(405)
        total_arc   = end_angle - start_angle

        for i in range(13):
            t = i / 12.0
            angle = start_angle + t * total_arc
            inner = radius - 12
            outer = radius - 2
            x1 = cx + math.cos(angle) * inner
            y1 = cy - math.sin(angle) * inner
            x2 = cx + math.cos(angle) * outer
            y2 = cy - math.sin(angle) * outer
            tick_color = COL_HUD_WARN if t > 0.7 else COL_HUD_DIM
            width = 2 if i % 3 == 0 else 1
            pygame.draw.line(screen, tick_color, (x1, y1), (x2, y2), width)

        steps = 60
        for i in range(int(steps * speed_pct) + 1):
            t = i / steps
            angle = start_angle + t * total_arc
            r_outer = radius - 4
            r_inner = radius - 14
            x_o = cx + math.cos(angle) * r_outer
            y_o = cy - math.sin(angle) * r_outer
            x_i = cx + math.cos(angle) * r_inner
            y_i = cy - math.sin(angle) * r_inner

            if t < 0.5:
                color = (int(80 + 350 * t), 255, 80)
            elif t < 0.75:
                color = (255, int(255 - 400 * (t - 0.5)), 60)
            else:
                color = (255, int(max(0, 155 - 600 * (t - 0.75))), 60)
            pygame.draw.line(screen, color, (x_o, y_o), (x_i, y_i), 3)

        needle_angle = start_angle + speed_pct * total_arc
        nx = cx + math.cos(needle_angle) * (radius - 18)
        ny = cy - math.sin(needle_angle) * (radius - 18)
        pygame.draw.line(screen, (255, 255, 255), (cx, cy), (nx, ny), 2)
        pygame.draw.circle(screen, COL_HUD_ACCENT, (cx, cy), 5)

        speed_text = self.font_huge.render(str(speed_display), True, COL_HUD_TEXT)
        text_rect = speed_text.get_rect(center=(cx, cy + 30))
        screen.blit(speed_text, text_rect)

        unit_text = self.font_tiny.render("KM/H", True, COL_HUD_DIM)
        unit_rect = unit_text.get_rect(center=(cx, cy + 55))
        screen.blit(unit_text, unit_rect)

    # ── bottom bar ──────────────────────────────────────────────

    def draw_controls(self, screen: pygame.Surface, boost: int = 0, shots: int = 0):
        self._draw_panel(screen, pygame.Rect(15, HEIGHT - 45, 500, 35),
                         alpha=140)
        ctrl = "[A/\u2190] Left   [D/\u2192] Right   [\u2191] Boost   [\u2193/SPC] Fire   [M] Mute   [Q] Quit"
        keys = self.font_small.render(ctrl, True, COL_HUD_DIM)
        screen.blit(keys, (25, HEIGHT - 40))

    def draw_mute_icon(self, screen: pygame.Surface, sound_on: bool):
        """Draw a clickable speaker icon (matches MUTE_ICON_RECT)."""
        ix, iy = self.MUTE_ICON_RECT.x, self.MUTE_ICON_RECT.y
        size = 32
        # Highlight on mouse hover
        mx, my = pygame.mouse.get_pos()
        hovered = self.MUTE_ICON_RECT.collidepoint(mx, my)
        panel = pygame.Surface((size + 10, size + 10), pygame.SRCALPHA)
        bg_alpha = 200 if hovered else 160
        pygame.draw.rect(panel, (10, 10, 15, bg_alpha), (0, 0, size + 10, size + 10),
                         border_radius=7)
        col = COL_HUD_ACCENT if sound_on else COL_HUD_WARN
        border_w = 2 if hovered else 1
        pygame.draw.rect(panel, col, (0, 0, size + 10, size + 10),
                         width=border_w, border_radius=7)
        screen.blit(panel, (ix, iy))

        # Speaker body (trapezoid)
        cx, cy = ix + 5, iy + 5
        sx, sy = cx + 4, cy + size // 2 - 6
        body = [(sx, sy + 2), (sx + 7, sy - 3),
                (sx + 7, sy + 15), (sx, sy + 10)]
        pygame.draw.polygon(screen, col, body)

        if sound_on:
            # Sound waves (two arcs drawn as lines)
            for r, a_start, a_end in [(9, -35, 35), (14, -50, 50)]:
                import math as _m
                points = []
                for deg in range(a_start, a_end + 1, 5):
                    rad = _m.radians(deg)
                    px = sx + 7 + int(_m.cos(rad) * r)
                    py = sy + 6 + int(_m.sin(rad) * r)
                    points.append((px, py))
                if len(points) > 1:
                    pygame.draw.lines(screen, col, False, points, 1)
        else:
            # Red X for muted
            x1, y1 = cx + 18, cy + 4
            x2, y2 = cx + 30, cy + 22
            pygame.draw.line(screen, (255, 60, 60), (x1, y1), (x2, y2), 2)
            pygame.draw.line(screen, (255, 60, 60), (x1, y2), (x2, y1), 2)

    # ── floating popups ─────────────────────────────────────────

    def add_popup(self, text: str, x: float, y: float, color=COL_HUD_GOLD):
        self.popups.append((text, x, y, 1.5, color))

    def update_popups(self, dt: float):
        updated = []
        for text, x, y, timer, color in self.popups:
            timer -= dt
            y -= 40 * dt
            if timer > 0:
                updated.append((text, x, y, timer, color))
        self.popups = updated

    def draw_popups(self, screen: pygame.Surface):
        for text, x, y, timer, color in self.popups:
            alpha = min(255, int(timer / 0.5 * 255))
            surf = self.font_med.render(text, True, color)
            surf.set_alpha(alpha)
            screen.blit(surf, (int(x), int(y)))

    # ── confetti ────────────────────────────────────────────────

    def spawn_confetti(self, count: int = 60):
        """Spawn a burst of confetti from the top of the screen."""
        for _ in range(count):
            p = ConfettiParticle()
            p.reset(random.uniform(0, WIDTH), random.uniform(-20, 0))
            p.vy = random.uniform(2, 6)
            p.vx = random.uniform(-4, 4)
            self.confetti.append(p)

    def update_confetti(self, dt: float):
        self.confetti = [p for p in self.confetti if p.update(dt)]

    def draw_confetti(self, screen: pygame.Surface):
        for p in self.confetti:
            p.draw(screen)

    # ── booster / invincible display ────────────────────────────

    def draw_booster_active(self, screen: pygame.Surface, time_left: float):
        """Show booster image and countdown on the right side."""
        if self._booster_img is None:
            return

        # Position on the right side, above speedometer
        bx = WIDTH - 150
        by = HEIGHT // 2 - 100

        # Glowing panel behind
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 40 + 20
        glow = pygame.Surface((160, 180), pygame.SRCALPHA)
        glow.fill((160, 60, 220, int(pulse)))
        screen.blit(glow, (bx - 20, by - 10))

        panel = pygame.Surface((160, 180), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 10, 40, 180), (0, 0, 160, 180),
                         border_radius=12)
        pygame.draw.rect(panel, (180, 80, 255), (0, 0, 160, 180),
                         width=2, border_radius=12)
        screen.blit(panel, (bx - 20, by - 10))

        # Booster image
        screen.blit(self._booster_img, (bx - 1, by))

        # "INVINCIBLE" text
        inv_text = self.font_med.render("INVINCIBLE", True, (255, 200, 60))
        screen.blit(inv_text,
                    inv_text.get_rect(center=(bx + 60, by + 115)))

        # Countdown bar
        bar_w = 120
        bar_h = 10
        bar_x = bx + 60 - bar_w // 2
        bar_y = by + 140
        pct = max(0, time_left / 3.0)
        pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h),
                         border_radius=5)
        fill = int(bar_w * pct)
        if fill > 0:
            pygame.draw.rect(screen, (180, 80, 255),
                             (bar_x, bar_y, fill, bar_h), border_radius=5)

        # Time left
        time_text = self.font_small.render(f"{time_left:.1f}s", True, COL_HUD_TEXT)
        screen.blit(time_text,
                    time_text.get_rect(center=(bx + 60, by + 160)))

    def draw_power_indicator(self, screen: pygame.Surface, powers: int):
        """Show boost icons in the second-from-right column."""
        if self._booster_img is None:
            return

        icon_w, icon_h = 44, 38
        # Boost lives in the column just LEFT of the fire column
        bx = WIDTH - icon_w * 2 - 36
        start_y = 108
        ticks = pygame.time.get_ticks()

        max_show = max(0, min(powers, 5))
        # Always show panel (at least label) so player knows boost exists
        panel_h = max(50, max_show * (icon_h + 5) + 26)
        self._draw_panel(screen, pygame.Rect(bx - 8, start_y - 8, icon_w + 18, panel_h),
                         alpha=150, border_color=(180, 80, 255))

        lbl = self.font_tiny.render("BOOST", True, (200, 140, 255))
        screen.blit(lbl, lbl.get_rect(center=(bx + icon_w // 2, start_y + 3)))

        mini = pygame.transform.smoothscale(self._booster_img, (icon_w, icon_h))
        for i in range(max_show):
            iy = start_y + 18 + i * (icon_h + 5)
            if i == 0:
                pulse = abs(math.sin(ticks * 0.004)) * 0.13
                sw = int(icon_w * (1 + pulse))
                sh = int(icon_h * (1 + pulse))
                pulsed = pygame.transform.smoothscale(self._booster_img, (sw, sh))
                screen.blit(pulsed, (bx + (icon_w - sw) // 2, iy + (icon_h - sh) // 2))
            else:
                screen.blit(mini, (bx, iy))

        if powers > 5:
            extra = self.font_tiny.render(f"+{powers-5}", True, (200, 140, 255))
            screen.blit(extra, extra.get_rect(
                center=(bx + icon_w // 2, start_y + 18 + max_show * (icon_h + 5))))

    def draw_fire_indicator(self, screen: pygame.Surface, shots: int):
        """Show fire power count on far-right column using firepower.png icons."""
        icon_w, icon_h = 44, 44
        bx = WIDTH - icon_w - 12       # far-right column
        start_y = 108
        ticks = pygame.time.get_ticks()

        max_show = max(0, min(shots, 5))
        panel_h = max(50, max_show * (icon_h + 5) + 26)
        self._draw_panel(screen, pygame.Rect(bx - 8, start_y - 8, icon_w + 18, panel_h),
                         alpha=150, border_color=(60, 140, 255))

        lbl = self.font_tiny.render("FIRE", True, (100, 180, 255))
        screen.blit(lbl, lbl.get_rect(center=(bx + icon_w // 2, start_y + 3)))

        if self._firepower_icon:
            mini = self._firepower_icon
            for i in range(max_show):
                iy = start_y + 18 + i * (icon_h + 5)
                if i == 0:
                    pulse = abs(math.sin(ticks * 0.005)) * 0.14
                    sw = int(icon_w * (1 + pulse))
                    sh = int(icon_h * (1 + pulse))
                    scaled = pygame.transform.smoothscale(self._firepower_icon, (sw, sh))
                    screen.blit(scaled, (bx + (icon_w - sw) // 2,
                                         iy + (icon_h - sh) // 2))
                else:
                    screen.blit(mini, (bx, iy))
        else:
            # Fallback: draw electric circles
            for i in range(max_show):
                iy = start_y + 18 + i * (icon_h + 5)
                pygame.draw.circle(screen, (60, 120, 255),
                                   (bx + icon_w // 2, iy + icon_h // 2), icon_w // 2 - 2)

        if shots > 5:
            extra = self.font_tiny.render(f"+{shots - 5}", True, (100, 180, 255))
            screen.blit(extra, extra.get_rect(
                center=(bx + icon_w // 2, start_y + 18 + max_show * (icon_h + 5))))

    def draw_f1_fact(self, screen: pygame.Surface, level: int):
        """F1 fact panel — bottom-right, beside the speedometer."""
        panel_w, panel_h = 295, 115
        px = WIDTH - 310 - 200   # to the left of speedometer
        py = HEIGHT - panel_h - 48
        self._draw_panel(screen, pygame.Rect(px, py, panel_w, panel_h))

        screen.blit(self.font_med.render("F1 FACT", True, COL_HUD_ACCENT),
                    (px + 10, py + 8))

        tip_color = COL_HUD_WARN if level > 8 else COL_HUD_GOOD
        words = self._fact_text.split()
        lines: list[str] = []
        cur = ""
        for w in words:
            test = f"{cur} {w}".strip()
            if self.font_small.size(test)[0] <= panel_w - 20:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        for i, ln in enumerate(lines[:4]):
            screen.blit(self.font_small.render(ln, True, tip_color),
                        (px + 10, py + 32 + i * 18))

    # ── game over overlay ───────────────────────────────────────

    def draw_game_over(self, screen: pygame.Surface, score: int, level: int,
                       best: int, is_new_best: bool,
                       top5: list[tuple[int, int, str]] | None = None):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        # ── Main game-over box ───────────────────────────────────
        box_w, box_h = 400, 290
        bx = WIDTH // 2 - box_w // 2 - 220
        by = HEIGHT // 2 - box_h // 2

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box, (15, 15, 25, 230), (0, 0, box_w, box_h), border_radius=15)
        pygame.draw.rect(box, COL_HUD_WARN, (0, 0, box_w, box_h), width=3, border_radius=15)
        screen.blit(box, (bx, by))

        title = self.font_large.render("GAME OVER", True, COL_HUD_WARN)
        screen.blit(title, title.get_rect(center=(bx + box_w // 2, by + 38)))

        pygame.draw.line(screen, COL_HUD_DIM,
                         (bx + 30, by + 62), (bx + box_w - 30, by + 62), 1)

        y_off = by + 78
        for label, value, color in [
            ("Score", str(score),     COL_HUD_TEXT),
            ("Level", str(level),     COL_HUD_GOLD),
            ("Best",  str(best),      COL_HUD_ACCENT),
        ]:
            lbl = self.font_med.render(label, True, COL_HUD_DIM)
            val = self.font_large.render(value, True, color)
            screen.blit(lbl, (bx + 55, y_off))
            screen.blit(val, (bx + box_w - 55 - val.get_width(), y_off - 4))
            y_off += 44

        if is_new_best:
            nb = self.font_med.render("NEW BEST!", True, COL_HUD_GOLD)
            screen.blit(nb, nb.get_rect(center=(bx + box_w // 2, y_off + 4)))
            y_off += 28

        pygame.draw.line(screen, COL_HUD_DIM,
                         (bx + 30, y_off + 8), (bx + box_w - 30, y_off + 8), 1)

        btn_y = y_off + 20
        btn_x = bx + 35
        for text, color in [("[R] Retry", COL_HUD_GOOD),
                             ("[C] Customize", COL_HUD_ACCENT),
                             ("[Q] Quit", COL_HUD_WARN)]:
            screen.blit(self.font_med.render(text, True, color), (btn_x, btn_y))
            btn_x += 125

        # ── Leaderboard box (right side) ─────────────────────────
        lb_w, lb_h = 340, box_h
        lbx = bx + box_w + 20
        lby = by

        lb = pygame.Surface((lb_w, lb_h), pygame.SRCALPHA)
        pygame.draw.rect(lb, (10, 15, 30, 230), (0, 0, lb_w, lb_h), border_radius=15)
        pygame.draw.rect(lb, COL_HUD_GOLD, (0, 0, lb_w, lb_h), width=2, border_radius=15)
        screen.blit(lb, (lbx, lby))

        screen.blit(
            self.font_large.render("TOP  5", True, COL_HUD_GOLD),
            self.font_large.render("TOP  5", True, COL_HUD_GOLD).get_rect(
                center=(lbx + lb_w // 2, lby + 30)),
        )
        pygame.draw.line(screen, COL_HUD_DIM,
                         (lbx + 20, lby + 52), (lbx + lb_w - 20, lby + 52), 1)

        rows = top5 or []
        for rank, (sc, lv, dt) in enumerate(rows, 1):
            ry = lby + 60 + (rank - 1) * 44
            medal_colors = [(255, 215, 0), (180, 180, 180), (200, 130, 60)]
            rc = medal_colors[rank - 1] if rank <= 3 else COL_HUD_DIM
            screen.blit(self.font_med.render(f"#{rank}", True, rc), (lbx + 18, ry))
            screen.blit(self.font_med.render(str(sc), True, COL_HUD_TEXT), (lbx + 65, ry))
            screen.blit(self.font_tiny.render(f"Lv{lv}", True, COL_HUD_GOLD), (lbx + 160, ry + 4))
            screen.blit(self.font_tiny.render(dt, True, COL_HUD_DIM), (lbx + 210, ry + 4))

        if not rows:
            no_data = self.font_small.render("No scores yet!", True, COL_HUD_DIM)
            screen.blit(no_data, no_data.get_rect(center=(lbx + lb_w // 2, lby + lb_h // 2)))
