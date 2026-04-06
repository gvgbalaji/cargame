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
from .surface_cache import SurfaceCache


# ── Module-level font pool (Flyweight) ────────────────────────
# Fonts are created once at import time and reused by both splash()
# and customization_screen() instead of being re-created on every call.
# These are initialised lazily (first access) so that pygame.font.init()
# has already been called before we construct them.
_fonts: dict[str, "pygame.font.Font | None"] = {}


def _get_fonts() -> dict[str, "pygame.font.Font"]:
    """Return (and lazily initialise) the shared font pool for screen functions."""
    if not _fonts:
        pygame.font.init()
        _fonts["splash_title"]  = pygame.font.SysFont("Arial", 60, bold=True)
        _fonts["splash_sub"]    = pygame.font.SysFont("Arial", 22)
        _fonts["splash_small"]  = pygame.font.SysFont("Arial", 17)
        _fonts["splash_key"]    = pygame.font.SysFont("Arial", 18, bold=True)
        _fonts["cust_title"]    = pygame.font.SysFont("Arial", 36, bold=True)
        _fonts["cust_med"]      = pygame.font.SysFont("Arial", 20, bold=True)
        _fonts["cust_small"]    = pygame.font.SysFont("Arial", 16)
        _fonts["cust_key"]      = pygame.font.SysFont("Arial", 14, bold=True)
    return _fonts


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

    # Dark overlay — reuse cached surface instead of allocating each frame
    overlay = SurfaceCache.get(WIDTH, HEIGHT)
    overlay.fill((15, 15, 25, 180))
    screen.blit(overlay, (0, 0))


def splash(screen: pygame.Surface) -> bool:
    """Title screen. Returns True to continue, False to quit."""
    clock = pygame.time.Clock()

    # Use shared module-level font pool (Flyweight) — no per-call allocation
    fonts = _get_fonts()
    font_title = fonts["splash_title"]
    font_sub   = fonts["splash_sub"]
    font_small = fonts["splash_small"]
    font_key   = fonts["splash_key"]

    # Pre-render the static title surface (same every frame)
    title = font_title.render("CAR DODGE", True, COL_HUD_GOLD)
    title_rect = title.get_rect(center=(WIDTH // 2, 120))
    # Pre-render the static glow surface at fixed size
    _glow_w = title.get_width() + 60
    _glow_h = title.get_height() + 30
    # Pre-render the subtitle
    sub = font_sub.render("Dodge oncoming traffic!", True, COL_HUD_DIM)
    # Pre-render the start prompt
    start_text = font_key.render("Press SPACE or ENTER to start...", True, COL_HUD_GOLD)

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

        # Title with pulsing glow — reuse cached glow surface
        pulse = abs(math.sin(tick * 0.03)) * 30 + 20
        glow = SurfaceCache.get(_glow_w, _glow_h)
        glow.fill((255, 215, 0, int(pulse)))
        screen.blit(glow, glow.get_rect(center=title_rect.center))
        screen.blit(title, title_rect)

        # Subtitle (pre-rendered, same every frame)
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 180)))

        # Instructions box — reuse cached panel surface
        box_w, box_h = 420, 260
        bx = WIDTH // 2 - box_w // 2
        by = 220

        panel = SurfaceCache.get(box_w, box_h)
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

        # Start prompt (pulsing visibility)
        if (tick // 30) % 2 == 0:
            screen.blit(start_text, start_text.get_rect(center=(WIDTH // 2, HEIGHT - 60)))

        pygame.display.flip()
        clock.tick(FPS)
        tick += 1


_ROAD_MODES = [
    ("STRAIGHT", "Classic straight lanes"),
    ("CURVY",    "Racing curves — free steering"),
]


def customization_screen(screen: pygame.Surface) -> tuple[int, str, bool]:
    """Car style, sound, and road type picker.
    Returns (style_index, sound_theme, curvy)."""
    clock = pygame.time.Clock()

    # Use shared module-level font pool (Flyweight) — no per-call allocation
    fonts = _get_fonts()
    font_title = fonts["cust_title"]
    font_med   = fonts["cust_med"]
    font_small = fonts["cust_small"]
    font_key   = fonts["cust_key"]

    style_sel = 0
    sound_sel = 0
    road_sel  = 0
    section   = 0  # 0 = car, 1 = sound, 2 = road
    tick      = 0
    n_styles  = len(PLAYER_STYLES)
    n_sections = 3

    # Pre-build car preview surfaces (scaled up for display)
    car_previews = []
    for i in range(n_styles):
        car_previews.append(make_player_surface(i))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return (0, "engine", False)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_TAB, pygame.K_DOWN):
                    section = (section + 1) % n_sections
                elif event.key == pygame.K_UP:
                    section = (section - 1) % n_sections
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if section == 0:
                        style_sel = (style_sel - 1) % n_styles
                    elif section == 1:
                        sound_sel = (sound_sel - 1) % len(SOUND_THEMES)
                    else:
                        road_sel = (road_sel - 1) % len(_ROAD_MODES)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if section == 0:
                        style_sel = (style_sel + 1) % n_styles
                    elif section == 1:
                        sound_sel = (sound_sel + 1) % len(SOUND_THEMES)
                    else:
                        road_sel = (road_sel + 1) % len(_ROAD_MODES)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return (style_sel, SOUND_THEMES[sound_sel][1],
                            road_sel == 1)
                elif event.key == pygame.K_q:
                    return (0, "engine", False)

        _draw_bg(screen, tick)

        # Title
        title = font_title.render("CUSTOMIZE", True, COL_HUD_GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

        # ── Car section (left) ──────────────────────────────────
        car_active = (section == 0)
        car_border = COL_HUD_ACCENT if car_active else COL_HUD_DIM

        car_panel = pygame.Rect(WIDTH // 2 - 440, 90, 280, 410)
        panel_s = SurfaceCache.get(car_panel.w, car_panel.h)
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

        # ── Sound section (center) ─────────────────────────────
        snd_active = (section == 1)
        snd_border = COL_HUD_ACCENT if snd_active else COL_HUD_DIM

        snd_panel = pygame.Rect(WIDTH // 2 - 140, 90, 280, 410)
        panel_s2 = SurfaceCache.get(snd_panel.w, snd_panel.h)
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

        # ── Road type section (right) ─────────────────────────
        road_active = (section == 2)
        road_border = COL_HUD_ACCENT if road_active else COL_HUD_DIM

        road_panel = pygame.Rect(WIDTH // 2 + 160, 90, 280, 410)
        panel_s3 = SurfaceCache.get(road_panel.w, road_panel.h)
        pygame.draw.rect(panel_s3, (10, 10, 15, 180),
                         (0, 0, road_panel.w, road_panel.h), border_radius=12)
        pygame.draw.rect(panel_s3, road_border,
                         (0, 0, road_panel.w, road_panel.h), width=2, border_radius=12)
        screen.blit(panel_s3, road_panel.topleft)

        # Header
        rhdr = font_med.render("ROAD TYPE", True, road_border)
        screen.blit(rhdr, rhdr.get_rect(center=(road_panel.centerx, road_panel.y + 25)))

        # Road name with arrows
        road_name = _ROAD_MODES[road_sel][0]
        road_desc = _ROAD_MODES[road_sel][1]
        rarr_color = COL_HUD_ACCENT if road_active else COL_HUD_DIM

        ry = road_panel.y + 55
        rla = font_med.render("\u25C0", True, rarr_color)
        rra = font_med.render("\u25B6", True, rarr_color)
        rn = font_med.render(road_name, True, COL_HUD_GOLD)

        screen.blit(rla, (road_panel.x + 20, ry))
        screen.blit(rn, rn.get_rect(center=(road_panel.centerx, ry + 10)))
        screen.blit(rra, (road_panel.right - 40, ry))

        # Description
        rdesc_text = font_small.render(road_desc, True, COL_HUD_DIM)
        screen.blit(rdesc_text, rdesc_text.get_rect(
            center=(road_panel.centerx, ry + 45)))

        # Road preview illustration
        rpy = road_panel.y + 140
        rpw, rph = 100, 220
        rpx = road_panel.centerx - rpw // 2
        preview_s = SurfaceCache.get(rpw, rph)
        # Mini road
        pygame.draw.rect(preview_s, COL_ASPHALT, (15, 0, 70, rph))
        # Lane markings
        for dy in range(0, rph, 20):
            yy = (dy + tick) % rph
            if road_sel == 0:
                # Straight
                pygame.draw.rect(preview_s, COL_LANE_MARK, (37, yy, 3, 12))
                pygame.draw.rect(preview_s, COL_LANE_MARK, (60, yy, 3, 12))
            else:
                # Curvy
                cx = int(math.sin((yy + tick * 2) * 0.04) * 12)
                pygame.draw.rect(preview_s, COL_LANE_MARK,
                                 (37 + cx, yy, 3, 12))
                pygame.draw.rect(preview_s, COL_LANE_MARK,
                                 (60 + cx, yy, 3, 12))
        screen.blit(preview_s, (rpx, rpy))

        # Counter
        road_counter = font_small.render(
            f"{road_sel + 1} / {len(_ROAD_MODES)}", True, COL_HUD_DIM)
        screen.blit(road_counter, road_counter.get_rect(
            center=(road_panel.centerx, road_panel.y + 390)))

        # ── Bottom hints ────────────────────────────────────────
        hints = font_key.render(
            "[</>] Cycle   [TAB/\u2191\u2193] Switch   [ENTER] Race!   [Q] Back",
            True, COL_HUD_DIM)
        screen.blit(hints, hints.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

        pygame.display.flip()
        clock.tick(FPS)
        tick += 1
