#!/usr/bin/env python3
"""
CAR DODGE  -  Terminal Car Dodging Game
Dodge oncoming cars for as long as you can!

Controls:
  LEFT / A  -  Move left lane
  RIGHT / D -  Move right lane
  Q         -  Quit

No external packages required - uses Python stdlib only.
"""

import curses
import random
import time

# ── Road layout ────────────────────────────────────────────────
ROAD_LEFT   = 6       # x-column of left road edge
ROAD_WIDTH  = 36      # total drivable width
NUM_LANES   = 3
LANE_WIDTH  = ROAD_WIDTH // NUM_LANES   # 12 per lane

# ── Car dimensions ─────────────────────────────────────────────
CAR_W = 7
CAR_H = 3

MIN_COLS = ROAD_LEFT + ROAD_WIDTH + 12
MIN_ROWS = 24

# ── Right-side scenery layout (relative to road_right = 42) ────
GRASS_EXTRA_W = 10          # wider grass strip
TREE_COL_1    = 14          # offset from road_right
TREE_COL_2    = 19          # offset from road_right (staggered)
SIDEBAR_X_OFF = 24          # offset from road_right where panel starts
SIDEBAR_IW    = 16          # inner width of panel (border = iw+2 = 18)
SIDEBAR_H     = 16          # rows tall

LEVEL_TIPS = [
    "Stay focused! ",
    "Eyes on road! ",
    "Keep dodging! ",
    "Don't blink!  ",
    "Speed rising! ",
    "Heart pounding",
    "DANGER AHEAD! ",
    "Nerves of steel",
    "Nearly insane!",
    "MAX SPEED!!!  ",
]

# ── Color pair IDs ─────────────────────────────────────────────
CP_RED     = 1
CP_GREEN   = 2
CP_YELLOW  = 3
CP_BLUE    = 4
CP_CYAN    = 5
CP_MAGENTA = 6
CP_WHITE   = 7

# ── Car artwork (7 wide × 3 tall, box-drawing style) ──────────
# Player: top-down rear view with exhaust pipes
PLAYER_ART = [
    "╔══╦══╗",
    "║  ★  ║",
    "╚══╩══╝",
]

# Enemies: front view with headlights (they face us head-on)
ENEMY_ARTS = [
    # Sedan – round headlights
    ["╔═════╗", "║ ● ● ║", "╚══╦══╝"],
    # SUV – grille bar
    ["╔═╦═╦═╗", "╠═════╣", "╚═════╝"],
    # Sports car – block fog lights
    ["╔═════╗", "║█   █║", "╚══╦══╝"],
    # Van – solid front
    ["╔═════╗", "║▓▓▓▓▓║", "╚═════╝"],
    # Racer – low stance with diffuser
    ["╔═════╗", "╠ ● ● ╣", "╚═╦═╦═╝"],
]

ENEMY_COLORS = [CP_RED, CP_MAGENTA, CP_CYAN, CP_BLUE]


# ── Helpers ────────────────────────────────────────────────────
def setup_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_RED,     curses.COLOR_RED,     -1)
    curses.init_pair(CP_GREEN,   curses.COLOR_GREEN,   -1)
    curses.init_pair(CP_YELLOW,  curses.COLOR_YELLOW,  -1)
    curses.init_pair(CP_BLUE,    curses.COLOR_BLUE,    -1)
    curses.init_pair(CP_CYAN,    curses.COLOR_CYAN,    -1)
    curses.init_pair(CP_MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(CP_WHITE,   curses.COLOR_WHITE,   -1)


def lane_x(lane: int) -> int:
    """Left-edge x position of a car centred in the given lane."""
    return ROAD_LEFT + lane * LANE_WIDTH + (LANE_WIDTH - CAR_W) // 2


# ── Enemy car ──────────────────────────────────────────────────
class Enemy:
    __slots__ = ("lane", "y", "art", "color", "passed")

    def __init__(self, lane: int):
        self.lane   = lane
        self.y      = 1.0
        self.art    = random.choice(ENEMY_ARTS)
        self.color  = random.choice(ENEMY_COLORS)
        self.passed = False

    @property
    def x(self) -> int:
        return lane_x(self.lane)


# ── Renderer ───────────────────────────────────────────────────
class Renderer:
    """All curses drawing lives here."""

    def __init__(self, scr):
        self.scr = scr
        self.h, self.w = scr.getmaxyx()

    # safe wrappers ---------------------------------------------------
    def _put(self, y: int, x: int, text: str, attr: int = 0):
        if 0 <= y < self.h and 0 <= x < self.w:
            try:
                self.scr.addstr(y, x, text[: self.w - x], attr)
            except curses.error:
                pass

    def _ch(self, y: int, x: int, ch: str, attr: int = 0):
        if 0 <= y < self.h - 1 and 0 <= x < self.w - 1:
            try:
                self.scr.addch(y, x, ch, attr)
            except curses.error:
                pass

    # road -----------------------------------------------------------
    def road(self, scroll: float):
        road_right = ROAD_LEFT + ROAD_WIDTH
        offset     = int(scroll) % 4

        for y in range(1, self.h - 1):
            # Textured grass (░ shade blocks look like grass)
            self._put(y, 0,              "░░░░  ", curses.color_pair(CP_GREEN))
            self._put(y, road_right + 2, "░" * GRASS_EXTRA_W, curses.color_pair(CP_GREEN))

            # Solid highway barriers (yellow concrete style)
            self._put(y, ROAD_LEFT - 2, "██", curses.color_pair(CP_YELLOW) | curses.A_BOLD)
            self._put(y, road_right,    "██", curses.color_pair(CP_YELLOW) | curses.A_BOLD)

            # Scrolling dashed lane dividers (yellow road markings)
            for lane in range(1, NUM_LANES):
                lx = ROAD_LEFT + lane * LANE_WIDTH
                if (y + offset) % 4 < 2:
                    self._ch(y, lx, "|", curses.color_pair(CP_YELLOW) | curses.A_DIM)

    # scrolling right-side scenery -----------------------------------
    def scenery(self, scroll: float):
        road_right = ROAD_LEFT + ROAD_WIDTH
        tx1 = road_right + TREE_COL_1
        tx2 = road_right + TREE_COL_2

        # Trees scroll at road speed. cycle = 3 (tree) + 6 (gap) = 9
        CYCLE = 9
        off = int(scroll * 1.5) % CYCLE

        for y in range(1, self.h - 1):
            # Tree column 1
            self._draw_tree_row(y, tx1, (y + off) % CYCLE)
            # Tree column 2 (staggered by half cycle)
            self._draw_tree_row(y, tx2, (y + off + CYCLE // 2) % CYCLE)

    def _draw_tree_row(self, y: int, x: int, ty: int):
        # Triangle tree: tip ▲, canopy ▲▲▲, trunk █
        if ty == 0:
            self._put(y, x, " ▲ ", curses.color_pair(CP_GREEN) | curses.A_BOLD)
        elif ty == 1:
            self._put(y, x, "▲▲▲", curses.color_pair(CP_GREEN))
        elif ty == 2:
            self._put(y, x, " █ ", curses.color_pair(CP_YELLOW) | curses.A_DIM)

    # stats sidebar --------------------------------------------------
    def sidebar(self, score: int, best: int, level: int, speed: float):
        road_right = ROAD_LEFT + ROAD_WIDTH
        sx = road_right + SIDEBAR_X_OFF
        if sx + SIDEBAR_IW + 2 > self.w:
            return   # terminal not wide enough

        iw = SIDEBAR_IW
        sy = max(1, self.h // 2 - SIDEBAR_H // 2)

        # Speed gauge
        MAX_SPEED  = 0.25 + 14 * 0.12
        speed_pct  = min((speed - 0.25) / max(MAX_SPEED - 0.25, 0.01), 1.0)
        bar_len    = iw - 4   # leave room for " [...]"
        bar_filled = int(speed_pct * bar_len)
        bar_str    = "|" * bar_filled + "." * (bar_len - bar_filled)
        bar_color  = CP_RED if speed_pct > 0.65 else CP_YELLOW

        # Tip based on level
        tip = LEVEL_TIPS[min(level - 1, len(LEVEL_TIPS) - 1)]

        cars_to_next = 5 - (score % 5)

        sep  = "+" + "-" * iw + "+"
        top  = "+" + "=" * iw + "+"

        def row(content: str) -> str:
            return f"|{content:<{iw}}|"

        lines = [
            (top,                                       CP_YELLOW, curses.A_BOLD),
            (row(f"{'  CAR  DODGE':^{iw}}"),            CP_YELLOW, curses.A_BOLD),
            (top,                                       CP_YELLOW, curses.A_BOLD),
            (row(f" SCORE  {score:05d}   "),            CP_WHITE,  curses.A_BOLD),
            (row(f" BEST   {best:05d}   "),             CP_CYAN,   0),
            (sep,                                       CP_WHITE,  curses.A_DIM),
            (row(f" LEVEL  {level:02d}       "),        CP_GREEN,  curses.A_BOLD),
            (row(f" NEXT   {cars_to_next} car{'s' if cars_to_next != 1 else ' '}  "), CP_WHITE, curses.A_DIM),
            (sep,                                       CP_WHITE,  curses.A_DIM),
            (row(f" SPEED          "),                  CP_WHITE,  0),
            (row(f" [{bar_str}] "),                     bar_color, curses.A_BOLD),
            (sep,                                       CP_WHITE,  curses.A_DIM),
            (row(f" {tip}"),                            CP_RED if speed_pct > 0.65 else CP_GREEN,
                                                        curses.A_BOLD | (curses.A_BLINK if speed_pct > 0.85 else 0)),
            (sep,                                       CP_WHITE,  curses.A_DIM),
            (row(f" [</A] left      "),                 CP_WHITE,  curses.A_DIM),
            (row(f" [>/D] right     "),                 CP_WHITE,  curses.A_DIM),
            (top,                                       CP_YELLOW, curses.A_BOLD),
        ]

        for i, (text, color, extra) in enumerate(lines):
            self._put(sy + i, sx, text, curses.color_pair(color) | extra)

    # cars -----------------------------------------------------------
    def car(self, art, x: int, y: float, color: int, bold: bool = False):
        attr = curses.color_pair(color) | (curses.A_BOLD if bold else 0)
        iy   = int(y)
        for i, line in enumerate(art):
            self._put(iy + i, x, line, attr)

    # HUD ------------------------------------------------------------
    def hud(self, score: int, level: int):
        filled  = min(level, 15)
        bar     = "|" * filled + "." * (15 - filled)
        text    = f" SCORE:{score:05d}  LVL:{level:02d}  SPEED:[{bar}]  "
        self._put(0, 0, text.ljust(self.w - 1),
                  curses.color_pair(CP_YELLOW) | curses.A_BOLD | curses.A_REVERSE)

        hint = " [</A] Left   [>/D] Right   [Q] Quit "
        self._put(self.h - 1, 0, hint.ljust(self.w - 1),
                  curses.color_pair(CP_WHITE) | curses.A_REVERSE)

    # game-over overlay ----------------------------------------------
    def game_over_box(self, score: int, level: int):
        mid_y, mid_x = self.h // 2, self.w // 2
        box = [
            "+------------------------------------+",
            "|                                    |",
            "|         *** GAME OVER ***           |",
            "|                                    |",
            f"|   Final Score  : {score:<5d}               |",
            f"|   Level Reached: {level:<3d}                 |",
            "|                                    |",
            "|   [R] Play Again     [Q] Quit       |",
            "|                                    |",
            "+------------------------------------+",
        ]
        bh = len(box)
        bw = len(box[0])
        sy = mid_y - bh // 2
        sx = mid_x - bw // 2

        for i, line in enumerate(box):
            color = CP_RED if i in (0, 2, bh - 1) else CP_WHITE
            self._put(sy + i, sx, line,
                      curses.color_pair(color) | curses.A_BOLD)

    # speed streaks behind player ------------------------------------
    def speed_streaks(self, player_x: int, player_y: int, level: int):
        """Vertical motion-blur streaks trailing below the player car."""
        if level < 2:
            return
        streak_len = min(level * 2, 10)
        attr = curses.color_pair(CP_CYAN) | curses.A_DIM
        for i in range(1, streak_len + 1):
            row = player_y + CAR_H + i - 1
            if 1 <= row < self.h - 1:
                self._put(row, player_x,         "│     │", attr)

    # road particles at high speed -----------------------------------
    def road_particles(self, scroll: float, level: int):
        """Fast-moving road specks that appear above level 4."""
        if level < 4:
            return
        # Particles scroll at 3× road speed
        fast = (scroll * 3) % (self.h - 2)
        xs   = [ROAD_LEFT + 2, ROAD_LEFT + 9, ROAD_LEFT + 18,
                ROAD_LEFT + 27, ROAD_LEFT + 33]
        attr = curses.color_pair(CP_WHITE) | curses.A_DIM
        for px in xs:
            for gap in range(0, self.h, 7):
                py = int(fast + gap) % (self.h - 2) + 1
                self._ch(py, px, "·", attr)

    # crash flash -----------------------------------------------------
    def flash(self, color: int, count: int = 4):
        attr = curses.color_pair(color) | curses.A_REVERSE
        for _ in range(count):
            self.scr.bkgd(" ", attr)
            self.scr.refresh()
            time.sleep(0.08)
            self.scr.bkgd(" ", 0)
            self.scr.refresh()
            time.sleep(0.06)


# ── Game logic ─────────────────────────────────────────────────
class Game:
    FPS        = 20
    FRAME_TIME = 1.0 / FPS

    def __init__(self, scr):
        self.scr       = scr
        self.r         = Renderer(scr)
        self.best_score = 0

    # ------------------------------------------------------------------
    def _reset(self):
        h = self.r.h
        self.player_lane = 1
        self.player_y    = h - CAR_H - 2
        self.enemies: list[Enemy] = []
        self.score       = 0
        self.level       = 1
        self.scroll      = 0.0
        self.spawn_cd    = 14   # frames until first spawn

    # ------------------------------------------------------------------
    @property
    def _speed(self) -> float:
        return 0.25 + (self.level - 1) * 0.12

    @property
    def _spawn_interval(self) -> int:
        return max(8, 28 - self.level * 2)

    # ------------------------------------------------------------------
    def _update(self):
        spd = self._speed
        self.scroll = (self.scroll + spd) % 4

        # Spawn logic
        self.spawn_cd -= 1
        if self.spawn_cd <= 0:
            self._spawn()
            self.spawn_cd = self._spawn_interval

        # Move enemies & award score
        for e in self.enemies:
            e.y += spd
            if not e.passed and e.y > self.player_y + CAR_H:
                e.passed = True
                self.score += 1
                self.level  = 1 + self.score // 5

        # Prune off-screen
        self.enemies = [e for e in self.enemies if e.y < self.r.h + CAR_H]

    def _spawn(self):
        taken = {e.lane for e in self.enemies if e.y < CAR_H + 4}
        free  = [l for l in range(NUM_LANES) if l not in taken]
        if free:
            self.enemies.append(Enemy(random.choice(free)))

    # ------------------------------------------------------------------
    def _collide(self) -> bool:
        px, py = lane_x(self.player_lane), self.player_y
        for e in self.enemies:
            if abs(px - e.x) < CAR_W - 1 and abs(py - e.y) < CAR_H:
                return True
        return False

    # ------------------------------------------------------------------
    def _input(self) -> bool:
        """Handle key input.  Returns False if player pressed Q."""
        k = self.scr.getch()
        if k in (curses.KEY_LEFT, ord("a"), ord("A")):
            self.player_lane = max(0, self.player_lane - 1)
        elif k in (curses.KEY_RIGHT, ord("d"), ord("D")):
            self.player_lane = min(NUM_LANES - 1, self.player_lane + 1)
        elif k in (ord("q"), ord("Q")):
            return False
        return True

    # ------------------------------------------------------------------
    def _draw(self):
        self.scr.erase()
        self.r.road(self.scroll)
        self.r.road_particles(self.scroll, self.level)
        self.r.scenery(self.scroll)
        for e in self.enemies:
            self.r.car(e.art, e.x, e.y, e.color)
        px = lane_x(self.player_lane)
        self.r.speed_streaks(px, self.player_y, self.level)
        self.r.car(PLAYER_ART, px, self.player_y, CP_YELLOW, bold=True)
        self.r.hud(self.score, self.level)
        self.r.sidebar(self.score, self.best_score, self.level, self._speed)
        self.scr.refresh()

    # ------------------------------------------------------------------
    def play(self) -> bool:
        """
        Run one game session.
        Returns True  → player wants to restart.
        Returns False → player wants to quit.
        """
        self._reset()
        self.scr.nodelay(True)

        while True:
            t0 = time.monotonic()

            if not self._input():
                return False        # quit

            self._update()
            self._draw()

            if self._collide():
                break               # crash!

            elapsed = time.monotonic() - t0
            gap     = self.FRAME_TIME - elapsed
            if gap > 0:
                time.sleep(gap)

        # ── Crash sequence ──────────────────────────────────────────
        if self.score > self.best_score:
            self.best_score = self.score

        self.r.flash(CP_RED)

        self.scr.erase()
        self.r.road(self.scroll)
        self.r.scenery(self.scroll)
        # Draw player in red at crash position
        self.r.car(PLAYER_ART, lane_x(self.player_lane),
                   self.player_y, CP_RED, bold=True)
        self.r.game_over_box(self.score, self.level)
        self.scr.refresh()

        self.scr.nodelay(False)
        while True:
            k = self.scr.getch()
            if k in (ord("r"), ord("R")):
                return True
            elif k in (ord("q"), ord("Q")):
                return False


# ── Splash screen ──────────────────────────────────────────────
def splash(stdscr) -> bool:
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
        elif k in (ord("q"), ord("Q")):
            return False


# ── Size check ─────────────────────────────────────────────────
def size_ok(stdscr) -> bool:
    h, w = stdscr.getmaxyx()
    if w < MIN_COLS or h < MIN_ROWS:
        stdscr.erase()
        msg  = f"Terminal too small! Need {MIN_COLS}x{MIN_ROWS}, got {w}x{h}."
        hint = "Please resize and restart."
        try:
            stdscr.addstr(0, 0, msg,  curses.color_pair(CP_RED) | curses.A_BOLD)
            stdscr.addstr(1, 0, hint, curses.color_pair(CP_WHITE))
        except curses.error:
            pass
        stdscr.refresh()
        time.sleep(3)
        return False
    return True


# ── Entry point ────────────────────────────────────────────────
def main(stdscr):
    setup_colors()
    curses.curs_set(0)

    if not size_ok(stdscr):
        return

    if not splash(stdscr):
        return

    game = Game(stdscr)
    while game.play():
        pass   # keep looping until player chooses quit


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\nThanks for playing Car Dodge!  Drive safe. 🚗")
