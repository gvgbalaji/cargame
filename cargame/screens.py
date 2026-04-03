"""Splash screen, size check, and curses initialisation."""

import curses
import time

from .constants import (
    CAR_W, CP_CYAN, CP_GREEN, CP_RED, CP_WHITE, CP_YELLOW,
    MIN_COLS, MIN_ROWS, PLAYER_ART, PLAYER_COLOR_OPTIONS,
)


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


def customization_screen(stdscr) -> int:
    """
    Car colour picker. Arrow keys or A/D to cycle, ENTER/SPACE to confirm.
    Returns the chosen color pair ID (defaults to CP_YELLOW on quit).
    """
    h, w      = stdscr.getmaxyx()
    options   = PLAYER_COLOR_OPTIONS
    n         = len(options)
    sel       = 0

    stdscr.nodelay(False)

    while True:
        stdscr.erase()

        # ── title ────────────────────────────────────────────────
        title     = "  CUSTOMIZE YOUR CAR  "
        title_box = "+" + "=" * len(title) + "+"
        ty        = max(1, h // 2 - 7)
        tx        = max(0, w // 2 - len(title_box) // 2)
        try:
            stdscr.addstr(ty,     tx, title_box,
                          curses.color_pair(CP_YELLOW) | curses.A_BOLD)
            stdscr.addstr(ty + 1, tx, "|" + title + "|",
                          curses.color_pair(CP_YELLOW) | curses.A_BOLD)
            stdscr.addstr(ty + 2, tx, title_box,
                          curses.color_pair(CP_YELLOW) | curses.A_BOLD)
        except curses.error:
            pass

        # ── hint ─────────────────────────────────────────────────
        hint = "  ← / →  choose colour      ENTER  race!      Q  back  "
        try:
            stdscr.addstr(ty + 4, max(0, w // 2 - len(hint) // 2),
                          hint, curses.color_pair(CP_WHITE))
        except curses.error:
            pass

        # ── car grid ─────────────────────────────────────────────
        gap     = 3                            # spaces between cars
        slot_w  = CAR_W + gap                  # 10 per slot
        total_w = n * CAR_W + (n - 1) * gap   # 6*7 + 5*3 = 57
        sx      = max(0, w // 2 - total_w // 2)
        car_top = ty + 7                       # top row of car art

        for i, (name, cp) in enumerate(options):
            x      = sx + i * slot_w
            is_sel = (i == sel)
            car_attr  = curses.color_pair(cp) | (curses.A_BOLD if is_sel else curses.A_DIM)
            name_attr = curses.color_pair(cp) | (curses.A_BOLD if is_sel else curses.A_DIM)

            # selector arrow
            if is_sel:
                try:
                    stdscr.addstr(car_top - 1, x + CAR_W // 2, "▼",
                                  curses.color_pair(CP_WHITE) | curses.A_BOLD)
                except curses.error:
                    pass

            # car art (3 rows)
            for row_i, line in enumerate(PLAYER_ART):
                try:
                    stdscr.addstr(car_top + row_i, x, line, car_attr)
                except curses.error:
                    pass

            # highlight box around selected car
            if is_sel:
                bx = x - 1
                for row_i in range(len(PLAYER_ART)):
                    try:
                        stdscr.addstr(car_top + row_i, bx, "[",
                                      curses.color_pair(CP_WHITE) | curses.A_BOLD)
                        stdscr.addstr(car_top + row_i, bx + CAR_W + 1, "]",
                                      curses.color_pair(CP_WHITE) | curses.A_BOLD)
                    except curses.error:
                        pass

            # colour name below
            nx = x + max(0, CAR_W // 2 - len(name) // 2)
            try:
                stdscr.addstr(car_top + len(PLAYER_ART) + 1, nx, name, name_attr)
            except curses.error:
                pass

        stdscr.refresh()

        # ── input ────────────────────────────────────────────────
        k = stdscr.getch()
        if k in (curses.KEY_LEFT, ord("a"), ord("A")):
            sel = (sel - 1) % n
        elif k in (curses.KEY_RIGHT, ord("d"), ord("D")):
            sel = (sel + 1) % n
        elif k in (ord(" "), 10, 13, curses.KEY_ENTER):
            return options[sel][1]
        elif k in (ord("q"), ord("Q")):
            return options[0][1]   # default to yellow
