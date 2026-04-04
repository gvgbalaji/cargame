"""Splash screen, customization screen (Pygame version)."""

import math
import pygame

from .constants import (
    WIDTH, HEIGHT, FPS,
    COL_HUD_BG, COL_HUD_BORDER, COL_HUD_TEXT, COL_HUD_ACCENT,
    COL_HUD_WARN, COL_HUD_GOOD, COL_HUD_GOLD, COL_HUD_DIM,
    COL_PLAYER_COLORS, SOUND_THEMES,
    COL_ASPHALT, COL_LANE_MARK, COL_GRASS,
)
from .cars import make_car_surface


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
    """Car and sound theme picker. Returns (skin_index, sound_theme)."""
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Arial", 36, bold=True)
    font_med   = pygame.font.SysFont("Arial", 20, bold=True)
    font_small = pygame.font.SysFont("Arial", 16)
    font_key   = pygame.font.SysFont("Arial", 14, bold=True)

    skin_sel  = 0
    sound_sel = 0
    section   = 0  # 0 = car, 1 = sound
    tick      = 0

    # Pre-build car preview surfaces
    car_previews = []
    for _name, color in COL_PLAYER_COLORS:
        car_previews.append(make_car_surface(color, is_player=True))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return (0, "engine")
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_TAB, pygame.K_UP, pygame.K_DOWN):
                    section = 1 - section
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if section == 0:
                        skin_sel = (skin_sel - 1) % len(COL_PLAYER_COLORS)
                    else:
                        sound_sel = (sound_sel - 1) % len(SOUND_THEMES)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if section == 0:
                        skin_sel = (skin_sel + 1) % len(COL_PLAYER_COLORS)
                    else:
                        sound_sel = (sound_sel + 1) % len(SOUND_THEMES)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return (skin_sel, SOUND_THEMES[sound_sel][1])
                elif event.key == pygame.K_q:
                    return (0, "engine")

        _draw_bg(screen, tick)

        # Title
        title = font_title.render("CUSTOMIZE", True, COL_HUD_GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

        # ── Car section (left) ──────────────────────────────────
        car_active = (section == 0)
        car_border = COL_HUD_ACCENT if car_active else COL_HUD_DIM

        car_panel = pygame.Rect(WIDTH // 2 - 340, 100, 300, 350)
        panel_s = pygame.Surface((car_panel.w, car_panel.h), pygame.SRCALPHA)
        pygame.draw.rect(panel_s, (10, 10, 15, 180),
                         (0, 0, car_panel.w, car_panel.h), border_radius=12)
        pygame.draw.rect(panel_s, car_border,
                         (0, 0, car_panel.w, car_panel.h), width=2, border_radius=12)
        screen.blit(panel_s, car_panel.topleft)

        # Header
        hdr = font_med.render("YOUR CAR", True, car_border)
        screen.blit(hdr, hdr.get_rect(center=(car_panel.centerx, car_panel.y + 25)))

        # Car name with arrows
        name = COL_PLAYER_COLORS[skin_sel][0]
        arrow_color = COL_HUD_ACCENT if car_active else COL_HUD_DIM
        left_arr  = font_med.render("\u25C0", True, arrow_color)
        right_arr = font_med.render("\u25B6", True, arrow_color)
        name_text = font_med.render(name, True, COL_HUD_GOLD)

        cy = car_panel.y + 60
        screen.blit(left_arr, (car_panel.x + 30, cy))
        screen.blit(name_text, name_text.get_rect(center=(car_panel.centerx, cy + 10)))
        screen.blit(right_arr, (car_panel.right - 50, cy))

        # Car preview (large, centered)
        preview = car_previews[skin_sel]
        big_preview = pygame.transform.scale(preview, (120, 220))
        preview_rect = big_preview.get_rect(
            center=(car_panel.centerx, car_panel.y + 220))
        screen.blit(big_preview, preview_rect)

        # ── Sound section (right) ───────────────────────────────
        snd_active = (section == 1)
        snd_border = COL_HUD_ACCENT if snd_active else COL_HUD_DIM

        snd_panel = pygame.Rect(WIDTH // 2 + 40, 100, 300, 350)
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

        sy = snd_panel.y + 60
        la = font_med.render("\u25C0", True, sarr_color)
        ra = font_med.render("\u25B6", True, sarr_color)
        sn = font_med.render(snd_name, True, COL_HUD_GOLD)

        screen.blit(la, (snd_panel.x + 30, sy))
        screen.blit(sn, sn.get_rect(center=(snd_panel.centerx, sy + 10)))
        screen.blit(ra, (snd_panel.right - 50, sy))

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

        # ── Bottom hints ────────────────────────────────────────
        hints = [
            "[</>] Cycle   [TAB] Switch   [ENTER] Race!   [Q] Back"
        ]
        for i, h in enumerate(hints):
            t = font_key.render(h, True, COL_HUD_DIM)
            screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT - 50 + i * 20)))

        pygame.display.flip()
        clock.tick(FPS)
        tick += 1
