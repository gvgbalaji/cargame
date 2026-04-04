"""Rich HUD overlay — speedometer, progress, score, popups."""

import math
import pygame

from .constants import (
    WIDTH, HEIGHT,
    COL_HUD_BG, COL_HUD_BORDER, COL_HUD_TEXT, COL_HUD_ACCENT,
    COL_HUD_WARN, COL_HUD_GOOD, COL_HUD_GOLD, COL_HUD_DIM,
    LEVEL_TIPS,
)


class HUD:
    """Draws all heads-up display elements."""

    def __init__(self):
        pygame.font.init()
        self.font_huge  = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_med   = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 15)
        self.font_tiny  = pygame.font.SysFont("Arial", 12)

        # Floating text popups: list of (text, x, y, timer, color)
        self.popups: list[tuple[str, float, float, float, tuple]] = []

    # ── helper ──────────────────────────────────────────────────

    @staticmethod
    def _draw_panel(screen: pygame.Surface, rect: pygame.Rect,
                    alpha: int = 180, border_color=COL_HUD_BORDER):
        """Draw a semi-transparent rounded panel."""
        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 10, 15, alpha), (0, 0, rect.w, rect.h),
                         border_radius=10)
        pygame.draw.rect(panel, border_color, (0, 0, rect.w, rect.h),
                         width=2, border_radius=10)
        screen.blit(panel, rect.topleft)

    # ── top bar ─────────────────────────────────────────────────

    def draw_top_bar(self, screen: pygame.Surface, score: int, level: int,
                     best: int, cars_to_next: int):
        """Score, level, and progress at the top."""
        # Left panel — Score
        self._draw_panel(screen, pygame.Rect(15, 10, 180, 60))
        score_label = self.font_small.render("SCORE", True, COL_HUD_DIM)
        score_val   = self.font_large.render(f"{score:05d}", True, COL_HUD_TEXT)
        screen.blit(score_label, (25, 14))
        screen.blit(score_val, (25, 32))

        # Best score (small, under score)
        best_text = self.font_tiny.render(f"BEST {best:05d}", True, COL_HUD_DIM)
        screen.blit(best_text, (135, 18))

        # Center panel — Level
        lx = WIDTH // 2 - 90
        self._draw_panel(screen, pygame.Rect(lx, 10, 180, 60))
        lvl_label = self.font_small.render("LEVEL", True, COL_HUD_DIM)
        lvl_val   = self.font_large.render(f"{level:02d}", True, COL_HUD_GOLD)
        screen.blit(lvl_label, (lx + 10, 14))
        screen.blit(lvl_val, (lx + 10, 32))

        # Progress to next level (bar)
        progress = (5 - cars_to_next) / 5.0
        bar_x = lx + 65
        bar_y = 40
        bar_w = 100
        bar_h = 14
        # Background
        pygame.draw.rect(screen, (30, 30, 40), (bar_x, bar_y, bar_w, bar_h),
                         border_radius=7)
        # Fill
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            pygame.draw.rect(screen, COL_HUD_ACCENT,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=7)
        # Label
        next_text = self.font_tiny.render(f"{5-cars_to_next}/5 next", True, COL_HUD_DIM)
        screen.blit(next_text, (bar_x + 5, bar_y - 14))

        # Right panel — Tip
        tip_idx = min(level - 1, len(LEVEL_TIPS) - 1)
        tip = LEVEL_TIPS[tip_idx]
        rx = WIDTH - 195
        self._draw_panel(screen, pygame.Rect(rx, 10, 180, 60))
        tip_label = self.font_small.render("STATUS", True, COL_HUD_DIM)
        tip_color = COL_HUD_WARN if level > 8 else COL_HUD_GOOD
        tip_val   = self.font_med.render(tip, True, tip_color)
        screen.blit(tip_label, (rx + 10, 14))
        screen.blit(tip_val, (rx + 10, 36))

    # ── speedometer ─────────────────────────────────────────────

    def draw_speedometer(self, screen: pygame.Surface, speed_pct: float,
                         speed_display: int):
        """Circular gauge at the bottom-right, inspired by racing games."""
        cx = WIDTH - 100
        cy = HEIGHT - 110
        radius = 75

        # Panel behind gauge
        panel = pygame.Surface((180, 180), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 10, 15, 160), (0, 0, 180, 180),
                         border_radius=15)
        screen.blit(panel, (cx - 90, cy - 90))

        # Gauge arc background (dark ring)
        start_angle = math.radians(135)
        end_angle   = math.radians(405)
        total_arc   = end_angle - start_angle

        # Tick marks
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

        # Colored arc (filled portion)
        points_bg = []
        points_fill = []
        steps = 60

        for i in range(steps + 1):
            t = i / steps
            angle = start_angle + t * total_arc
            x = cx + math.cos(angle) * (radius - 8)
            y = cy - math.sin(angle) * (radius - 8)
            points_bg.append((x, y))

        for i in range(int(steps * speed_pct) + 1):
            t = i / steps
            angle = start_angle + t * total_arc
            r_outer = radius - 4
            r_inner = radius - 14
            x_o = cx + math.cos(angle) * r_outer
            y_o = cy - math.sin(angle) * r_outer
            x_i = cx + math.cos(angle) * r_inner
            y_i = cy - math.sin(angle) * r_inner

            # Color gradient from green to yellow to red
            if t < 0.5:
                color = (int(80 + 350 * t), 255, 80)
            elif t < 0.75:
                color = (255, int(255 - 400 * (t - 0.5)), 60)
            else:
                color = (255, int(max(0, 155 - 600 * (t - 0.75))), 60)

            pygame.draw.line(screen, color, (x_o, y_o), (x_i, y_i), 3)

        # Needle
        needle_angle = start_angle + speed_pct * total_arc
        nx = cx + math.cos(needle_angle) * (radius - 18)
        ny = cy - math.sin(needle_angle) * (radius - 18)
        pygame.draw.line(screen, (255, 255, 255), (cx, cy), (nx, ny), 2)
        pygame.draw.circle(screen, COL_HUD_ACCENT, (cx, cy), 5)

        # Speed number (large, centered)
        speed_text = self.font_huge.render(str(speed_display), True, COL_HUD_TEXT)
        text_rect = speed_text.get_rect(center=(cx, cy + 30))
        screen.blit(speed_text, text_rect)

        # "KM/H" label
        unit_text = self.font_tiny.render("KM/H", True, COL_HUD_DIM)
        unit_rect = unit_text.get_rect(center=(cx, cy + 55))
        screen.blit(unit_text, unit_rect)

    # ── bottom bar ──────────────────────────────────────────────

    def draw_controls(self, screen: pygame.Surface):
        """Control hints at the bottom."""
        self._draw_panel(screen, pygame.Rect(15, HEIGHT - 45, 260, 35),
                         alpha=140)
        keys = self.font_small.render(
            "[A/\u2190] Left   [D/\u2192] Right   [Q] Quit", True, COL_HUD_DIM)
        screen.blit(keys, (25, HEIGHT - 40))

    # ── floating popups ─────────────────────────────────────────

    def add_popup(self, text: str, x: float, y: float, color=COL_HUD_GOLD):
        self.popups.append((text, x, y, 1.5, color))

    def update_popups(self, dt: float):
        updated = []
        for text, x, y, timer, color in self.popups:
            timer -= dt
            y -= 40 * dt  # float upward
            if timer > 0:
                updated.append((text, x, y, timer, color))
        self.popups = updated

    def draw_popups(self, screen: pygame.Surface):
        for text, x, y, timer, color in self.popups:
            alpha = min(255, int(timer / 0.5 * 255))
            surf = self.font_med.render(text, True, color)
            surf.set_alpha(alpha)
            screen.blit(surf, (int(x), int(y)))

    # ── milestone banner ────────────────────────────────────────

    def draw_milestone(self, screen: pygame.Surface, frame: int):
        """Big center banner for score milestones."""
        if frame > 80:
            return

        alpha = 255 if frame < 40 else max(0, 255 - (frame - 40) * 6)
        scale = min(1.0, frame / 10.0)

        text = self.font_large.render("MILESTONE!", True, COL_HUD_GOLD)
        text.set_alpha(alpha)

        w = int(text.get_width() * scale)
        h = int(text.get_height() * scale)
        if w > 0 and h > 0:
            scaled = pygame.transform.scale(text, (w, h))
            rect = scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))

            # Glow behind
            glow = pygame.Surface((w + 40, h + 20), pygame.SRCALPHA)
            glow.fill((255, 215, 0, min(60, alpha // 3)))
            glow_rect = glow.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
            screen.blit(glow, glow_rect)
            screen.blit(scaled, rect)

    # ── game over overlay ───────────────────────────────────────

    def draw_game_over(self, screen: pygame.Surface, score: int, level: int,
                       best: int, is_new_best: bool):
        """Full game over screen overlay."""
        # Darken background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Main box
        box_w, box_h = 400, 320
        bx = WIDTH // 2 - box_w // 2
        by = HEIGHT // 2 - box_h // 2

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box, (15, 15, 25, 230), (0, 0, box_w, box_h),
                         border_radius=15)
        pygame.draw.rect(box, COL_HUD_WARN, (0, 0, box_w, box_h),
                         width=3, border_radius=15)
        screen.blit(box, (bx, by))

        # Title
        title = self.font_large.render("GAME OVER", True, COL_HUD_WARN)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, by + 40)))

        # Divider
        pygame.draw.line(screen, COL_HUD_DIM,
                         (bx + 30, by + 65), (bx + box_w - 30, by + 65), 1)

        # Stats
        y_off = by + 85
        stats = [
            ("Score", f"{score:05d}", COL_HUD_TEXT),
            ("Level", f"{level}", COL_HUD_GOLD),
            ("Best", f"{best:05d}", COL_HUD_ACCENT),
        ]
        for label, value, color in stats:
            lbl = self.font_med.render(label, True, COL_HUD_DIM)
            val = self.font_large.render(value, True, color)
            screen.blit(lbl, (bx + 60, y_off))
            screen.blit(val, (bx + box_w - 60 - val.get_width(), y_off - 4))
            y_off += 45

        if is_new_best:
            nb = self.font_med.render("NEW BEST!", True, COL_HUD_GOLD)
            screen.blit(nb, nb.get_rect(center=(WIDTH // 2, y_off + 5)))
            y_off += 30

        # Divider
        pygame.draw.line(screen, COL_HUD_DIM,
                         (bx + 30, y_off + 10), (bx + box_w - 30, y_off + 10), 1)

        # Buttons
        btn_y = y_off + 25
        btns = [
            ("[R] Retry", COL_HUD_GOOD),
            ("[C] Customize", COL_HUD_ACCENT),
            ("[Q] Quit", COL_HUD_WARN),
        ]
        btn_x = bx + 40
        for text, color in btns:
            t = self.font_med.render(text, True, color)
            screen.blit(t, (btn_x, btn_y))
            btn_x += 130
