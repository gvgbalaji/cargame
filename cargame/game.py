"""Core game loop and logic."""

import curses
import random
import time

from .constants import CAR_H, CAR_W, NUM_LANES, PLAYER_ART, CP_RED, CAR_SKINS, lane_x
from .enemy import Enemy
from .renderer import Renderer
from .sound import play_crash_sound, play_lane_switch_sound, play_pass_sound, set_sound_config


class Game:
    FPS        = 20
    FRAME_TIME = 1.0 / FPS

    def __init__(self, scr, skin_index: int = 0, sound_theme: str = "engine"):
        self.scr          = scr
        self.r            = Renderer(scr)
        self.best_score   = 0
        # Derive player color from chosen skin
        self.player_color = CAR_SKINS[skin_index][2] if 0 <= skin_index < len(CAR_SKINS) else CAR_SKINS[0][2]
        set_sound_config(enabled=(sound_theme != "silent"), theme=sound_theme)

    def set_skin(self, skin_index: int) -> None:
        self.player_color = CAR_SKINS[skin_index][2] if 0 <= skin_index < len(CAR_SKINS) else CAR_SKINS[0][2]

    # ── session reset ────────────────────────────────────────────

    def _reset(self) -> None:
        self.player_lane = 1
        self.player_y    = self.r.h - CAR_H - 6
        self.enemies: list[Enemy] = []
        self.score       = 0
        self.level       = 1
        self.scroll      = 0.0
        self.spawn_cd    = 14
        self.party_timer = 0

    # ── derived properties ───────────────────────────────────────

    @property
    def _speed(self) -> float:
        return 0.37 + (self.level - 1) * 0.12

    @property
    def _spawn_interval(self) -> int:
        return max(8, 28 - self.level * 2)

    # ── per-frame logic ──────────────────────────────────────────

    def _update(self) -> None:
        spd = self._speed
        self.scroll = (self.scroll + spd) % 4

        self.spawn_cd -= 1
        if self.spawn_cd <= 0:
            self._spawn()
            self.spawn_cd = self._spawn_interval

        for e in self.enemies:
            e.y += spd
            if not e.passed and e.y > self.player_y + CAR_H:
                e.passed     = True
                self.score  += 1
                self.level   = 1 + self.score // 5
                play_pass_sound()
                if self.score % 20 == 0:
                    self.party_timer = 40

        self.enemies = [e for e in self.enemies if e.y < self.r.h + CAR_H]

    def _spawn(self) -> None:
        taken = {e.lane for e in self.enemies if e.y < CAR_H + 4}
        free  = [l for l in range(NUM_LANES) if l not in taken]
        if free:
            self.enemies.append(Enemy(random.choice(free)))

    def _collide(self) -> bool:
        px, py = lane_x(self.player_lane), self.player_y
        return any(
            abs(px - e.x) < CAR_W - 1 and abs(py - e.y) < CAR_H
            for e in self.enemies
        )

    def _handle_input(self) -> bool:
        """Return False if the player pressed Q (quit)."""
        k = self.scr.getch()
        if k in (curses.KEY_LEFT, ord("a"), ord("A")):
            new_lane = max(0, self.player_lane - 1)
            if new_lane != self.player_lane:
                self.player_lane = new_lane
                play_lane_switch_sound()
        elif k in (curses.KEY_RIGHT, ord("d"), ord("D")):
            new_lane = min(NUM_LANES - 1, self.player_lane + 1)
            if new_lane != self.player_lane:
                self.player_lane = new_lane
                play_lane_switch_sound()
        elif k in (ord("q"), ord("Q")):
            return False
        return True

    def _draw(self) -> None:
        self.scr.erase()
        self.r.road(self.scroll)
        self.r.road_particles(self.scroll, self.level)
        self.r.scenery(self.scroll)
        for e in self.enemies:
            self.r.car(e.art, e.x, e.y, e.color)
        px = lane_x(self.player_lane)
        self.r.speed_streaks(px, self.player_y, self.level)
        self.r.car(PLAYER_ART, px, self.player_y, self.player_color, bold=True)
        self.r.hud(self.score, self.level)
        self.r.sidebar(self.score, self.best_score, self.level, self._speed)
        if self.party_timer > 0:
            self.r.party_poppers(40 - self.party_timer)
            self.party_timer -= 1
        self.scr.refresh()

    # ── crash sequence ───────────────────────────────────────────

    def _crash(self) -> None:
        if self.score > self.best_score:
            self.best_score = self.score
        play_crash_sound()
        curses.beep()
        self.r.flash(CP_RED)
        self.scr.erase()
        self.r.road(self.scroll)
        self.r.scenery(self.scroll)
        self.r.car(PLAYER_ART, lane_x(self.player_lane),
                   self.player_y, CP_RED, bold=True)
        self.r.game_over_box(self.score, self.level, self.player_color)
        self.scr.refresh()

    # ── public API ───────────────────────────────────────────────

    def play(self) -> str:
        """
        Run one game session.
        Returns "restart"   → play again with same skin
                "customize" → go back to the customization screen
                "quit"      → exit
        """
        self._reset()
        self.scr.nodelay(True)

        while True:
            t0 = time.monotonic()

            if not self._handle_input():
                return "quit"

            self._update()
            self._draw()

            if self._collide():
                break

            gap = self.FRAME_TIME - (time.monotonic() - t0)
            if gap > 0:
                time.sleep(gap)

        self._crash()

        self.scr.nodelay(False)
        while True:
            k = self.scr.getch()
            if k in (ord("r"), ord("R")):
                return "restart"
            if k in (ord("c"), ord("C")):
                return "customize"
            if k in (ord("q"), ord("Q")):
                return "quit"
