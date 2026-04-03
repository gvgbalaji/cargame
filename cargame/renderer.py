"""All curses drawing lives here. No game logic."""

import curses
import random
import time

from .constants import (
    CAR_H, CP_CYAN, CP_GREEN, CP_MAGENTA, CP_RED, CP_WHITE, CP_YELLOW,
    GRASS_EXTRA_W, LEVEL_TIPS, NUM_LANES, ROAD_LEFT, ROAD_WIDTH,
    SIDEBAR_H, SIDEBAR_IW, SIDEBAR_X_OFF, TREE_COL_1, TREE_COL_2,
    LANE_WIDTH,
)

_CONFETTI_CHARS  = list("*+·✦★°╋●◆▲")
_CONFETTI_COLORS = [CP_RED, CP_YELLOW, CP_CYAN, CP_MAGENTA, CP_GREEN, CP_WHITE]


class Renderer:

    def __init__(self, scr):
        self.scr = scr
        self.h, self.w = scr.getmaxyx()

    # ── safe draw helpers ────────────────────────────────────────

    def _put(self, y: int, x: int, text: str, attr: int = 0) -> None:
        if 0 <= y < self.h and 0 <= x < self.w:
            try:
                self.scr.addstr(y, x, text[: self.w - x], attr)
            except curses.error:
                pass

    def _ch(self, y: int, x: int, ch: str, attr: int = 0) -> None:
        if 0 <= y < self.h - 1 and 0 <= x < self.w - 1:
            try:
                self.scr.addch(y, x, ch, attr)
            except curses.error:
                pass

    # ── road ─────────────────────────────────────────────────────

    def road(self, scroll: float) -> None:
        road_right = ROAD_LEFT + ROAD_WIDTH
        offset     = int(scroll) % 4

        for y in range(1, self.h - 1):
            self._put(y, 0,              "░░░░  ",          curses.color_pair(CP_GREEN))
            self._put(y, road_right + 2, "░" * GRASS_EXTRA_W, curses.color_pair(CP_GREEN))
            self._put(y, ROAD_LEFT - 2,  "██",              curses.color_pair(CP_YELLOW) | curses.A_BOLD)
            self._put(y, road_right,     "██",              curses.color_pair(CP_YELLOW) | curses.A_BOLD)
            for lane in range(1, NUM_LANES):
                lx = ROAD_LEFT + lane * LANE_WIDTH
                if (y + offset) % 4 < 2:
                    self._ch(y, lx, "|", curses.color_pair(CP_YELLOW) | curses.A_DIM)

    # ── scenery ──────────────────────────────────────────────────

    def scenery(self, scroll: float) -> None:
        road_right = ROAD_LEFT + ROAD_WIDTH
        tx1   = road_right + TREE_COL_1
        tx2   = road_right + TREE_COL_2
        CYCLE = 9
        off   = int(scroll) % CYCLE

        for y in range(1, self.h - 1):
            self._draw_tree_row(y, tx1, (y + off) % CYCLE)
            self._draw_tree_row(y, tx2, (y + off + CYCLE // 2) % CYCLE)

    def _draw_tree_row(self, y: int, x: int, ty: int) -> None:
        if ty == 0:
            self._put(y, x, " ▲ ", curses.color_pair(CP_GREEN) | curses.A_BOLD)
        elif ty == 1:
            self._put(y, x, "▲▲▲", curses.color_pair(CP_GREEN))
        elif ty == 2:
            self._put(y, x, " █ ", curses.color_pair(CP_YELLOW) | curses.A_DIM)

    # ── sidebar ──────────────────────────────────────────────────

    def sidebar(self, score: int, best: int, level: int, speed: float) -> None:
        road_right = ROAD_LEFT + ROAD_WIDTH
        sx = road_right + SIDEBAR_X_OFF
        if sx + SIDEBAR_IW + 2 > self.w:
            return

        iw          = SIDEBAR_IW
        sy          = max(1, self.h // 2 - SIDEBAR_H // 2)
        BASE_SPEED  = 0.37
        MAX_SPEED   = BASE_SPEED + 14 * 0.12
        speed_pct   = min((speed - BASE_SPEED) / max(MAX_SPEED - BASE_SPEED, 0.01), 1.0)
        bar_len     = iw - 4
        bar_str     = "|" * int(speed_pct * bar_len) + "." * (bar_len - int(speed_pct * bar_len))
        bar_color   = CP_RED if speed_pct > 0.65 else CP_YELLOW
        tip         = LEVEL_TIPS[min(level - 1, len(LEVEL_TIPS) - 1)]
        cars_to_next = 5 - (score % 5)

        sep = "+" + "-" * iw + "+"
        top = "+" + "=" * iw + "+"

        def row(content: str) -> str:
            return f"|{content:<{iw}}|"

        lines = [
            (top,                                        CP_YELLOW, curses.A_BOLD),
            (row(f"{'  CAR  DODGE':^{iw}}"),             CP_YELLOW, curses.A_BOLD),
            (top,                                        CP_YELLOW, curses.A_BOLD),
            (row(f" SCORE  {score:05d}   "),             CP_WHITE,  curses.A_BOLD),
            (row(f" BEST   {best:05d}   "),              CP_CYAN,   0),
            (sep,                                        CP_WHITE,  curses.A_DIM),
            (row(f" LEVEL  {level:02d}       "),         CP_GREEN,  curses.A_BOLD),
            (row(f" NEXT   {cars_to_next} car{'s' if cars_to_next != 1 else ' '}  "),
                                                         CP_WHITE,  curses.A_DIM),
            (sep,                                        CP_WHITE,  curses.A_DIM),
            (row(" SPEED          "),                    CP_WHITE,  0),
            (row(f" [{bar_str}] "),                      bar_color, curses.A_BOLD),
            (sep,                                        CP_WHITE,  curses.A_DIM),
            (row(f" {tip}"),
             CP_RED if speed_pct > 0.65 else CP_GREEN,
             curses.A_BOLD | (curses.A_BLINK if speed_pct > 0.85 else 0)),
            (sep,                                        CP_WHITE,  curses.A_DIM),
            (row(" [</A] left      "),                   CP_WHITE,  curses.A_DIM),
            (row(" [>/D] right     "),                   CP_WHITE,  curses.A_DIM),
            (top,                                        CP_YELLOW, curses.A_BOLD),
        ]

        for i, (text, color, extra) in enumerate(lines):
            self._put(sy + i, sx, text, curses.color_pair(color) | extra)

    # ── cars ─────────────────────────────────────────────────────

    def car(self, art: list[str], x: int, y: float,
            color: int, bold: bool = False) -> None:
        attr = curses.color_pair(color) | (curses.A_BOLD if bold else 0)
        iy   = int(y)
        for i, line in enumerate(art):
            self._put(iy + i, x, line, attr)

    # ── HUD ──────────────────────────────────────────────────────

    def hud(self, score: int, level: int) -> None:
        filled = min(level, 15)
        bar    = "|" * filled + "." * (15 - filled)
        self._put(0, 0,
                  f" SCORE:{score:05d}  LVL:{level:02d}  SPEED:[{bar}]  ".ljust(self.w - 1),
                  curses.color_pair(CP_YELLOW) | curses.A_BOLD | curses.A_REVERSE)
        self._put(self.h - 1, 0,
                  " [</A] Left   [>/D] Right   [Q] Quit ".ljust(self.w - 1),
                  curses.color_pair(CP_WHITE) | curses.A_REVERSE)

    # ── game-over overlay ────────────────────────────────────────

    def game_over_box(self, score: int, level: int,
                      player_color: int = CP_WHITE) -> None:
        box = [
            "+--------------------------------------+",
            "|                                      |",
            "|          *** GAME OVER ***            |",
            "|                                      |",
            f"|   Final Score  : {score:<5d}                 |",
            f"|   Level Reached: {level:<3d}                   |",
            "|                                      |",
            "|  [R] Again   [C] Colour   [Q] Quit   |",
            "|                                      |",
            "+--------------------------------------+",
        ]
        bh = len(box)
        sy = self.h // 2 - bh // 2
        sx = self.w // 2 - len(box[0]) // 2

        for i, line in enumerate(box):
            if i in (0, 2, bh - 1):
                color, extra = CP_RED, curses.A_BOLD
            elif i == 7:
                color, extra = player_color, curses.A_BOLD
            else:
                color, extra = CP_WHITE, curses.A_BOLD
            self._put(sy + i, sx, line, curses.color_pair(color) | extra)

    # ── speed effects ────────────────────────────────────────────

    def speed_streaks(self, player_x: int, player_y: int, level: int) -> None:
        if level < 2:
            return
        streak_len = min(level * 2, 10)
        attr = curses.color_pair(CP_CYAN) | curses.A_DIM
        for i in range(1, streak_len + 1):
            row = player_y + CAR_H + i - 1
            if 1 <= row < self.h - 1:
                self._put(row, player_x, "│     │", attr)

    def road_particles(self, scroll: float, level: int) -> None:
        if level < 4:
            return
        fast = (scroll * 3) % (self.h - 2)
        xs   = [ROAD_LEFT + 2, ROAD_LEFT + 9, ROAD_LEFT + 18,
                ROAD_LEFT + 27, ROAD_LEFT + 33]
        attr = curses.color_pair(CP_WHITE) | curses.A_DIM
        for px in xs:
            for gap in range(0, self.h, 7):
                py = int(fast + gap) % (self.h - 2) + 1
                self._ch(py, px, "·", attr)

    # ── party poppers ────────────────────────────────────────────

    def party_poppers(self, party_frame: int) -> None:
        road_right = ROAD_LEFT + ROAD_WIDTH
        x_start    = road_right + 2
        x_end      = min(self.w - 1, road_right + SIDEBAR_X_OFF - 1)
        if x_end <= x_start:
            return

        rng     = random.Random(party_frame // 3)
        density = max(4, 18 - party_frame // 2)

        for _ in range(density):
            y  = rng.randint(1, self.h - 2)
            x  = rng.randint(x_start, x_end - 1)
            ch = rng.choice(_CONFETTI_CHARS)
            cp = rng.choice(_CONFETTI_COLORS)
            self._ch(y, x, ch, curses.color_pair(cp) | curses.A_BOLD)

        if party_frame < 20:
            battr = (curses.color_pair(CP_YELLOW) | curses.A_BOLD
                     | (curses.A_BLINK if party_frame < 10 else 0))
            self._put(self.h // 2, road_right + 2, " MILESTONE! ", battr)

    # ── crash flash ──────────────────────────────────────────────

    def flash(self, color: int, count: int = 4) -> None:
        attr = curses.color_pair(color) | curses.A_REVERSE
        for _ in range(count):
            self.scr.bkgd(" ", attr)
            self.scr.refresh()
            time.sleep(0.08)
            self.scr.bkgd(" ", 0)
            self.scr.refresh()
            time.sleep(0.06)
