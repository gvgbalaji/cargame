"""Splash screen, customization screen (Pygame version)."""

import math
import pygame

from .constants import (
    WIDTH, HEIGHT, FPS,
    COL_HUD_BG, COL_HUD_BORDER, COL_HUD_TEXT, COL_HUD_ACCENT,
    COL_HUD_WARN, COL_HUD_GOOD, COL_HUD_GOLD, COL_HUD_DIM,
    SOUND_THEMES,
    COL_ASPHALT, COL_LANE_MARK, COL_GRASS,
)
from .cars import make_player_surface, PLAYER_STYLES


def _draw_bg(screen: pygame.Surface, tick: int):
    """Animated background for menus."""
    screen.fill((15, 15, 25))

    # Scrolling road in background
    road_x = WIDTH // 2 - 100
    pygame.draw.rect(screen, COL_ASPHALT, (road_x, 0, 200, HEIGHT))
    offset = tick % 70
    for y in range(-70, HEIGHT + 70, 70):
        yy = y + offset
        pygame.draw.rect(screen, COL_LANE_MARK,
                         (road_x + 98, yy, 4, 40))

    # Grass strips
    pygame.draw.rect(screen, COL_GRASS, (0, 0, road_x, HEIGHT))
    pygame.draw.rect(screen, COL_GRASS, (road_x + 200, 0, WIDTH - road_x - 200, HEIGHT))

    # Dark overlay for readability
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((15, 15, 25, 180))
    screen.blit(overlay, (0, 0))


def splash(screen: pygame.Surface) -> bool:
    """Title screen. Returns True to continue, False to quit."""
    clock = pygame.time.Clock()

    font_title  = pygame.font.SysFont("Arial", 60, bold=True)
    font_sub    = pygame.font.SysFont("Arial", 22)
    font_small  = pygame.font.SysFont("Arial", 17)
    font_key    = pygame.font.SysFont("Arial", 18, bold=True)

    tick = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return True
                if event.key == pygame.K_q:
                    return False

        _draw_bg(screen, tick)

        # Title with glow
        title = font_title.render("CAR DODGE", True, COL_HUD_GOLD)
        title_rect = title.get_rect(center=(WIDTH // 2, 120))

        # Pulsing glow
        pulse = abs(math.sin(tick * 0.03)) * 30 + 20
        glow = pygame.Surface((title.get_width() + 60, title.get_height() + 30),
                              pygame.SRCALPHA)
        glow.fill((255, 215, 0, int(pulse)))
        screen.blit(glow, glow.get_rect(center=title_rect.center))
        screen.blit(title, title_rect)

        # Subtitle
        sub = font_sub.render("Dodge oncoming traffic!", True, COL_HUD_DIM)
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 180)))

        # Instructions box
        box_w, box_h = 420, 260
        bx = WIDTH // 2 - box_w // 2
        by = 220

        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 10, 15, 180), (0, 0, box_w, box_h),
                         border_radius=12)
        pygame.draw.rect(panel, COL_HUD_BORDER, (0, 0, box_w, box_h),
                         width=2, border_radius=12)
        screen.blit(panel, (bx, by))

        # Control info
        info_lines = [
            ("Controls", COL_HUD_ACCENT, True),
            ("", None, False),
            ("LEFT / A     Move left", COL_HUD_TEXT, False),
            ("RIGHT / D    Move right", COL_HUD_TEXT, False),
            ("Q            Quit", COL_HUD_TEXT, False),
            ("", None, False),
            ("Rules", COL_HUD_ACCENT, True),
            ("", None, False),
            ("+1 point for every car you dodge", COL_HUD_GOOD, False),
            ("Speed increases every 5 cars", COL_HUD_WARN, False),
            ("Don't crash!", COL_HUD_WARN, False),
        ]

        ly = by + 15
        for text, color, is_header in info_lines:
            if not text:
                ly += 8
                continue
            font = font_key if is_header else font_small
            t = font.render(text, True, color)
            screen.blit(t, (bx + 25, ly))
            ly += 24

        # Start prompt (pulsing)
        if (tick // 30) % 2 == 0:
            start = font_key.render("Press SPACE or ENTER to start...",
                                    True, COL_HUD_GOLD)
            screen.blit(start, start.get_rect(center=(WIDTH // 2, HEIGHT - 60)))

        pygame.display.flip()
        clock.tick(FPS)
        tick += 1


def customization_screen(screen: pygame.Surface) -> tuple[int, str]:
    """Car style and sound theme picker. Returns (style_index, sound_theme)."""
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Arial", 36, bold=True)
    font_med   = pygame.font.SysFont("Arial", 20, bold=True)
    font_small = pygame.font.SysFont("Arial", 16)
    font_key   = pygame.font.SysFont("Arial", 14, bold=True)

    style_sel = 0
    sound_sel = 0
    section   = 0  # 0 = car, 1 = sound
    tick      = 0
    n_styles  = len(PLAYER_STYLES)

    # Pre-build car preview surfaces (scaled up for display)
    car_previews = []
    for i in range(n_styles):
        car_previews.append(make_player_surface(i))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return (0, "engine")
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_TAB, pygame.K_UP, pygame.K_DOWN):
                    section = 1 - section
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if section == 0:
                        style_sel = (style_sel - 1) % n_styles
                    else:
                        sound_sel = (sound_sel - 1) % len(SOUND_THEMES)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if section == 0:
                        style_sel = (style_sel + 1) % n_styles
                    else:
                        sound_sel = (sound_sel + 1) % len(SOUND_THEMES)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return (style_sel, SOUND_THEMES[sound_sel][1])
                elif event.key == pygame.K_q:
                    return (0, "engine")

        _draw_bg(screen, tick)

        # Title
        title = font_title.render("CUSTOMIZE", True, COL_HUD_GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

        # ── Car section (left) ──────────────────────────────────
        car_active = (section == 0)
        car_border = COL_HUD_ACCENT if car_active else COL_HUD_DIM

        car_panel = pygame.Rect(WIDTH // 2 - 340, 90, 300, 410)
        panel_s = pygame.Surface((car_panel.w, car_panel.h), pygame.SRCALPHA)
        pygame.draw.rect(panel_s, (10, 10, 15, 180),
                         (0, 0, car_panel.w, car_panel.h), border_radius=12)
        pygame.draw.rect(panel_s, car_border,
                         (0, 0, car_panel.w, car_panel.h), width=2, border_radius=12)
        screen.blit(panel_s, car_panel.topleft)

        # Header
        hdr = font_med.render("YOUR CAR", True, car_border)
        screen.blit(hdr, hdr.get_rect(center=(car_panel.centerx, car_panel.y + 25)))

        # Car style name with arrows
        style_name = PLAYER_STYLES[style_sel][0]
        arrow_color = COL_HUD_ACCENT if car_active else COL_HUD_DIM
        left_arr  = font_med.render("\u25C0", True, arrow_color)
        right_arr = font_med.render("\u25B6", True, arrow_color)
        name_text = font_med.render(style_name, True, COL_HUD_GOLD)

        cy = car_panel.y + 55
        screen.blit(left_arr, (car_panel.x + 20, cy))
        screen.blit(name_text, name_text.get_rect(center=(car_panel.centerx, cy + 10)))
        screen.blit(right_arr, (car_panel.right - 40, cy))

        # Car preview (large, centered) with gentle bobbing
        preview = car_previews[style_sel]
        big_preview = pygame.transform.scale(preview, (150, 275))
        bob = int(math.sin(tick * 0.05) * 3)
        preview_rect = big_preview.get_rect(
            center=(car_panel.centerx, car_panel.y + 240 + bob))
        screen.blit(big_preview, preview_rect)

        # Style counter
        counter = font_small.render(
            f"{style_sel + 1} / {n_styles}", True, COL_HUD_DIM)
        screen.blit(counter, counter.get_rect(
            center=(car_panel.centerx, car_panel.y + 390)))

        # ── Sound section (right) ───────────────────────────────
        snd_active = (section == 1)
        snd_border = COL_HUD_ACCENT if snd_active else COL_HUD_DIM

        snd_panel = pygame.Rect(WIDTH // 2 + 40, 90, 300, 410)
        panel_s2 = pygame.Surface((snd_panel.w, snd_panel.h), pygame.SRCALPHA)
        pygame.draw.rect(panel_s2, (10, 10, 15, 180),
                         (0, 0, snd_panel.w, snd_panel.h), border_radius=12)
        pygame.draw.rect(panel_s2, snd_border,
                         (0, 0, snd_panel.w, snd_panel.h), width=2, border_radius=12)
        screen.blit(panel_s2, snd_panel.topleft)

        # Header
        shdr = font_med.render("SOUND THEME", True, snd_border)
        screen.blit(shdr, shdr.get_rect(center=(snd_panel.centerx, snd_panel.y + 25)))

        # Theme name with arrows
        snd_name = SOUND_THEMES[sound_sel][0]
        snd_desc = SOUND_THEMES[sound_sel][2]
        sarr_color = COL_HUD_ACCENT if snd_active else COL_HUD_DIM

        sy = snd_panel.y + 55
        la = font_med.render("\u25C0", True, sarr_color)
        ra = font_med.render("\u25B6", True, sarr_color)
        sn = font_med.render(snd_name, True, COL_HUD_GOLD)

        screen.blit(la, (snd_panel.x + 20, sy))
        screen.blit(sn, sn.get_rect(center=(snd_panel.centerx, sy + 10)))
        screen.blit(ra, (snd_panel.right - 40, sy))

        # Description
        desc_text = font_small.render(snd_desc, True, COL_HUD_DIM)
        screen.blit(desc_text, desc_text.get_rect(
            center=(snd_panel.centerx, sy + 45)))

        # Sound visualization (decorative bars)
        bar_y = snd_panel.y + 150
        bar_count = 12
        bar_spacing = 18
        bar_start_x = snd_panel.centerx - (bar_count * bar_spacing) // 2

        for i in range(bar_count):
            bh = int(abs(math.sin((tick + i * 8) * 0.08)) * 80 + 10)
            bx_pos = bar_start_x + i * bar_spacing
            bar_color = COL_HUD_ACCENT if snd_active else COL_HUD_DIM
            pygame.draw.rect(screen, bar_color,
                             (bx_pos, bar_y + 100 - bh, 10, bh),
                             border_radius=3)

        # Sound counter
        snd_counter = font_small.render(
            f"{sound_sel + 1} / {len(SOUND_THEMES)}", True, COL_HUD_DIM)
        screen.blit(snd_counter, snd_counter.get_rect(
            center=(snd_panel.centerx, snd_panel.y + 390)))

        # ── Bottom hints ────────────────────────────────────────
        hints = font_key.render(
            "[</>] Cycle   [TAB] Switch   [ENTER] Race!   [Q] Back",
            True, COL_HUD_DIM)
        screen.blit(hints, hints.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

        pygame.display.flip()
        clock.tick(FPS)
        tick += 1
