"""Splash screen, size check, and curses initialisation."""

import curses
import time

from .constants import (
    CAR_W, CAR_H, CP_CYAN, CP_GREEN, CP_RED, CP_WHITE, CP_YELLOW,
    MIN_COLS, MIN_ROWS, PLAYER_ART, CAR_SKINS, SOUND_THEMES,
)
from .image_art import png_to_block_art, art_to_curses


def setup_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_RED,     curses.COLOR_RED,     -1)
    curses.init_pair(CP_GREEN,   curses.COLOR_GREEN,   -1)
    curses.init_pair(CP_YELLOW,  curses.COLOR_YELLOW,  -1)
    curses.init_pair(4,          curses.COLOR_BLUE,    -1)
    curses.init_pair(CP_CYAN,    curses.COLOR_CYAN,    -1)
    curses.init_pair(6,          curses.COLOR_MAGENTA, -1)
    curses.init_pair(CP_WHITE,   curses.COLOR_WHITE,   -1)


def size_ok(stdscr) -> bool:
    h, w = stdscr.getmaxyx()
    if w < MIN_COLS or h < MIN_ROWS:
        stdscr.erase()
        try:
            stdscr.addstr(0, 0,
                          f"Terminal too small! Need {MIN_COLS}x{MIN_ROWS}, got {w}x{h}.",
                          curses.color_pair(CP_RED) | curses.A_BOLD)
            stdscr.addstr(1, 0, "Please resize and restart.",
                          curses.color_pair(CP_WHITE))
        except curses.error:
            pass
        stdscr.refresh()
        time.sleep(3)
        return False
    return True


def splash(stdscr) -> bool:
    """Show title screen. Returns True to start, False to quit."""
    h, w = stdscr.getmaxyx()
    stdscr.erase()

    banner = [
        r"  ____    _    ____     ____   ___  ____   ____ ___ ",
        r" / ___|  / \  |  _ \   |  _ \ / _ \|  _ \ / ___| __|",
        r"| |     / _ \ | |_) |  | | | | | | | | | | |  |  _| ",
        r"| |___ / ___ \|  _ <   | |_| | |_| | |_| | |__| |___",
        r" \____/_/   \_\_| \_\  |____/ \___/|____/ \____|____|",
    ]

    sy = max(1, h // 2 - 9)
    for i, line in enumerate(banner):
        x = max(0, w // 2 - len(line) // 2)
        try:
            stdscr.addstr(sy + i, x, line,
                          curses.color_pair(CP_YELLOW) | curses.A_BOLD)
        except curses.error:
            pass

    info = [
        ("Dodge cars coming at you from the opposite direction!", CP_WHITE, 0),
        ("",                                                       CP_WHITE, 0),
        ("  Controls",                                             CP_CYAN,  curses.A_BOLD | curses.A_UNDERLINE),
        ("  LEFT / A    Move to the left lane",                    CP_WHITE, 0),
        ("  RIGHT / D   Move to the right lane",                   CP_WHITE, 0),
        ("  Q           Quit",                                     CP_WHITE, 0),
        ("",                                                       CP_WHITE, 0),
        ("  Score 1 point for every car you dodge.",               CP_GREEN, 0),
        ("  Speed increases every 5 cars dodged.",                 CP_GREEN, 0),
        ("  Don't crash!",                                         CP_RED,   curses.A_BOLD),
        ("",                                                       CP_WHITE, 0),
        ("  Press SPACE or ENTER to start ...",                    CP_YELLOW, curses.A_BOLD),
    ]

    start = sy + len(banner) + 2
    lx    = max(0, w // 2 - 27)
    for i, (text, color, extra) in enumerate(info):
        try:
            stdscr.addstr(start + i, lx, text,
                          curses.color_pair(color) | extra)
        except curses.error:
            pass

    stdscr.refresh()
    stdscr.nodelay(False)

    while True:
        k = stdscr.getch()
        if k in (ord(" "), 10, 13, curses.KEY_ENTER):
            return True
        if k in (ord("q"), ord("Q")):
            return False


def customization_screen(stdscr) -> tuple[int, str]:
    """
    Two-section customization screen:
      LEFT  — Car skin picker  (← / → to cycle)
      RIGHT — Sound theme picker (← / → to cycle)
    TAB or UP/DOWN switches between sections.
    ENTER/SPACE confirms. Q goes back (returns defaults).

    Returns (skin_index: int, sound_theme: str).
    """
    h, w = stdscr.getmaxyx()
    skins  = CAR_SKINS
    n_skins = len(skins)
    n_sounds = len(SOUND_THEMES)

    skin_sel  = 0   # chosen skin index
    sound_sel = 0   # chosen sound theme index
    section   = 0   # 0 = car section active, 1 = sound section active

    # Pre-load all skin block art
    raw_arts: list[list[list[tuple[str, int, int]]] | None] = []
    for _name, path, _color in skins:
        try:
            raw_arts.append(png_to_block_art(path, CAR_W, CAR_H))
        except Exception:
            raw_arts.append(None)

    # Convert to curses attrs
    curses_arts: list[list[list[tuple[str, int]]] | None] = []
    for raw in raw_arts:
        if raw is not None:
            try:
                curses_arts.append(art_to_curses(raw))
            except Exception:
                curses_arts.append(None)
        else:
            curses_arts.append(None)

    stdscr.nodelay(False)

    while True:
        stdscr.erase()

        # ── title ────────────────────────────────────────────────
        title     = "=======  CUSTOMIZE  ======="
        ty        = max(1, h // 2 - 11)
        tx        = max(0, w // 2 - len(title) // 2)
        try:
            stdscr.addstr(ty, tx, "+" + "=" * (len(title) - 2) + "+",
                          curses.color_pair(CP_YELLOW) | curses.A_BOLD)
            stdscr.addstr(ty + 1, tx, "|" + title + "|",
                          curses.color_pair(CP_YELLOW) | curses.A_BOLD)
            stdscr.addstr(ty + 2, tx, "+" + "=" * (len(title) - 2) + "+",
                          curses.color_pair(CP_YELLOW) | curses.A_BOLD)
        except curses.error:
            pass

        # ── layout: two columns side by side ─────────────────────
        # Left column: car picker.  Right column: sound picker.
        # Total width: CAR_W + gap + sound_col_w
        gap           = 8
        sound_col_w   = 20
        total_w       = CAR_W + gap + sound_col_w
        left_x        = max(0, w // 2 - total_w // 2)
        right_x       = left_x + CAR_W + gap
        content_top   = ty + 5      # first row of section headers

        # ── CAR section header ───────────────────────────────────
        car_active = (section == 0)
        car_hdr_attr = (curses.color_pair(CP_CYAN) | curses.A_BOLD | curses.A_UNDERLINE
                        if car_active
                        else curses.color_pair(CP_WHITE) | curses.A_DIM)
        try:
            stdscr.addstr(content_top, left_x, "  YOUR CAR  ", car_hdr_attr)
        except curses.error:
            pass

        # ── car selector row: ← NAME → ──────────────────────────
        skin_name = skins[skin_sel][0]
        arrow_attr = (curses.color_pair(CP_CYAN) | curses.A_BOLD
                      if car_active
                      else curses.color_pair(CP_WHITE) | curses.A_DIM)
        name_attr  = (curses.color_pair(CP_YELLOW) | curses.A_BOLD
                      if car_active
                      else curses.color_pair(CP_WHITE) | curses.A_DIM)
        car_label  = f"\u2190 {skin_name:^6s} \u2192"   # ← NAME →
        try:
            stdscr.addstr(content_top + 1, left_x, "← ", arrow_attr)
            stdscr.addstr(content_top + 1, left_x + 2, f"{skin_name:^6s}", name_attr)
            stdscr.addstr(content_top + 1, left_x + 2 + 6, " →", arrow_attr)
        except curses.error:
            pass

        # ── car art ──────────────────────────────────────────────
        car_art_top = content_top + 3
        art_curses  = curses_arts[skin_sel]
        if art_curses is not None:
            for row_i, row in enumerate(art_curses):
                for col_i, (ch, attr) in enumerate(row):
                    try:
                        stdscr.addch(car_art_top + row_i, left_x + col_i, ch, attr)
                    except curses.error:
                        pass
        else:
            fb_attr = (curses.color_pair(CP_CYAN) | curses.A_BOLD
                       if car_active
                       else curses.color_pair(CP_WHITE) | curses.A_DIM)
            for row_i, line in enumerate(PLAYER_ART):
                try:
                    stdscr.addstr(car_art_top + row_i, left_x, line, fb_attr)
                except curses.error:
                    pass

        # selection box around car art
        box_attr = (curses.color_pair(CP_CYAN) | curses.A_BOLD
                    if car_active
                    else curses.color_pair(CP_WHITE) | curses.A_DIM)
        for row_i in range(CAR_H):
            try:
                stdscr.addstr(car_art_top + row_i, left_x - 1, "[", box_attr)
                stdscr.addstr(car_art_top + row_i, left_x + CAR_W, "]", box_attr)
            except curses.error:
                pass

        # ── SOUND section header ─────────────────────────────────
        snd_active   = (section == 1)
        snd_hdr_attr = (curses.color_pair(CP_CYAN) | curses.A_BOLD | curses.A_UNDERLINE
                        if snd_active
                        else curses.color_pair(CP_WHITE) | curses.A_DIM)
        try:
            stdscr.addstr(content_top, right_x, "    SOUND   ", snd_hdr_attr)
        except curses.error:
            pass

        # ── sound selector row: ← THEME → ───────────────────────
        snd_disp_name, snd_key, snd_desc = SOUND_THEMES[sound_sel]
        snd_arrow_attr = (curses.color_pair(CP_CYAN) | curses.A_BOLD
                          if snd_active
                          else curses.color_pair(CP_WHITE) | curses.A_DIM)
        snd_name_attr  = (curses.color_pair(CP_YELLOW) | curses.A_BOLD
                          if snd_active
                          else curses.color_pair(CP_WHITE) | curses.A_DIM)
        snd_desc_attr  = (curses.color_pair(CP_GREEN) | curses.A_BOLD
                          if snd_active
                          else curses.color_pair(CP_WHITE) | curses.A_DIM)
        try:
            stdscr.addstr(content_top + 1, right_x, "← ", snd_arrow_attr)
            stdscr.addstr(content_top + 1, right_x + 2, f"{snd_disp_name:^8s}", snd_name_attr)
            stdscr.addstr(content_top + 1, right_x + 2 + 8, " →", snd_arrow_attr)
        except curses.error:
            pass

        # description line
        try:
            stdscr.addstr(content_top + 3, right_x, snd_desc[:sound_col_w], snd_desc_attr)
        except curses.error:
            pass

        # sound section box (vertical lines matching car art height)
        snd_box_attr = (curses.color_pair(CP_CYAN) | curses.A_BOLD
                        if snd_active
                        else curses.color_pair(CP_WHITE) | curses.A_DIM)
        for row_i in range(CAR_H):
            try:
                stdscr.addstr(car_art_top + row_i, right_x - 1, "[", snd_box_attr)
                stdscr.addstr(car_art_top + row_i, right_x + sound_col_w, "]", snd_box_attr)
            except curses.error:
                pass

        # ── bottom hints ─────────────────────────────────────────
        hint_y = car_art_top + CAR_H + 2
        hints = [
            ("← / →  cycle within section", CP_WHITE, 0),
            ("TAB     switch section",        CP_WHITE, 0),
            ("ENTER   race!     Q  back",     CP_YELLOW, curses.A_BOLD),
        ]
        for hi, (htxt, hcol, hextra) in enumerate(hints):
            hx = max(0, w // 2 - len(htxt) // 2)
            try:
                stdscr.addstr(hint_y + hi, hx, htxt,
                              curses.color_pair(hcol) | hextra)
            except curses.error:
                pass

        stdscr.refresh()

        # ── input ────────────────────────────────────────────────
        k = stdscr.getch()
        if k in (9, curses.KEY_UP, curses.KEY_DOWN,
                 ord("\t")):          # TAB / UP / DOWN → switch section
            section = 1 - section
        elif k in (curses.KEY_LEFT, ord("a"), ord("A")):
            if section == 0:
                skin_sel = (skin_sel - 1) % n_skins
            else:
                sound_sel = (sound_sel - 1) % n_sounds
        elif k in (curses.KEY_RIGHT, ord("d"), ord("D")):
            if section == 0:
                skin_sel = (skin_sel + 1) % n_skins
            else:
                sound_sel = (sound_sel + 1) % n_sounds
        elif k in (ord(" "), 10, 13, curses.KEY_ENTER):
            return (skin_sel, SOUND_THEMES[sound_sel][1])
        elif k in (ord("q"), ord("Q")):
            return (0, "engine")   # defaults
