"""Core game loop and logic (Pygame version)."""

import random
import pygame

from .constants import (
    WIDTH, HEIGHT, FPS, CAR_W, CAR_H, NUM_LANES,
    lane_car_x,
)
from .cars import make_player_surface, PLAYER_STYLES
from .enemy import Enemy
from .renderer import Renderer
from .hud import HUD
from .sound import play_crash_sound, play_lane_switch_sound, play_pass_sound, set_sound_config


class Game:
    """One game session: handles logic, rendering, input."""

    BASE_SPEED   = 3.0    # pixels per frame at level 1
    SPEED_STEP   = 0.8    # extra px/frame per level
    INVINCIBLE_DURATION = 3.0   # seconds

    def __init__(self, screen: pygame.Surface, skin_index: int = 0,
                 sound_theme: str = "engine"):
        self.screen     = screen
        self.clock      = pygame.time.Clock()
        self.renderer   = Renderer(screen)
        self.hud        = HUD()
        self.best_score = 0

        self._set_skin(skin_index)
        set_sound_config(enabled=(sound_theme != "silent"), theme=sound_theme)

    def _set_skin(self, skin_index: int):
        idx = skin_index % len(PLAYER_STYLES)
        self.player_surface = make_player_surface(idx)

    def set_skin(self, skin_index: int):
        self._set_skin(skin_index)

    # ── session reset ───────────────────────────────────────────

    def _reset(self):
        self.player_lane    = 1
        self.player_y       = HEIGHT - CAR_H - 60
        self.player_target_x = lane_car_x(self.player_lane)
        self.player_x       = self.player_target_x
        self.enemies: list[Enemy] = []
        self.score          = 0
        self.level          = 1
        self.scroll         = 0.0
        self.spawn_cd       = 60
        self.crash_flash    = 0

        # Invincibility / boost power
        self.boost_powers       = 0   # available boosts
        self.invincible_timer   = 0.0 # seconds remaining
        self._last_power_score  = 0   # track when last power was earned

        # Confetti
        self.hud.confetti.clear()

    # ── derived properties ──────────────────────────────────────

    @property
    def _speed(self) -> float:
        return self.BASE_SPEED + (self.level - 1) * self.SPEED_STEP

    @property
    def _speed_pct(self) -> float:
        max_speed = self.BASE_SPEED + 14 * self.SPEED_STEP
        return min((self._speed - self.BASE_SPEED) /
                   max(max_speed - self.BASE_SPEED, 0.01), 1.0)

    @property
    def _speed_display(self) -> int:
        return int(60 + self._speed_pct * 220)

    @property
    def _spawn_interval(self) -> int:
        return max(30, 90 - self.level * 6)

    @property
    def is_invincible(self) -> bool:
        return self.invincible_timer > 0

    # ── per-frame logic ─────────────────────────────────────────

    def _update(self, dt: float):
        spd = self._speed
        self.scroll += spd

        # Smooth lane transition
        diff = self.player_target_x - self.player_x
        self.player_x += diff * 0.2

        # Tick invincibility
        if self.invincible_timer > 0:
            self.invincible_timer = max(0, self.invincible_timer - dt)

        # Spawn enemies
        self.spawn_cd -= 1
        if self.spawn_cd <= 0:
            self._spawn()
            self.spawn_cd = self._spawn_interval

        # Move enemies
        for e in self.enemies:
            e.y += spd
            if not e.passed and e.y > self.player_y + CAR_H:
                e.passed = True
                self.score += 1
                self.level = 1 + self.score // 5
                play_pass_sound()
                self.hud.add_popup("+1", e.x + e.width // 2, e.y)

                # Award boost power every 50 points
                if self.score >= 50 and self.score // 50 > self._last_power_score // 50:
                    self.boost_powers += 1
                    self._last_power_score = self.score
                    self.hud.add_popup("BOOST +1!", WIDTH // 2 - 40,
                                       HEIGHT // 2, (200, 140, 255))

                # Confetti every 20 points
                if self.score % 20 == 0:
                    self.hud.spawn_confetti(60)

        self.enemies = [e for e in self.enemies if e.y < HEIGHT + e.height]

        # Update popups & confetti
        self.hud.update_popups(dt)
        self.hud.update_confetti(dt)

    def _spawn(self):
        taken = {e.lane for e in self.enemies if e.y < e.height + 30}
        free = [l for l in range(NUM_LANES) if l not in taken]
        if free:
            self.enemies.append(Enemy(random.choice(free)))

    def _collide(self) -> bool:
        if self.is_invincible:
            return False

        px, py = self.player_x, self.player_y
        pw, ph = CAR_W, CAR_H
        for e in self.enemies:
            ex, ew, eh = e.x, e.width, e.height
            overlap_x = (px + pw - 10 > ex + 10) and (ex + ew - 10 > px + 10)
            overlap_y = (py + ph - 10 > e.y + 10) and (e.y + eh - 10 > py + 10)
            if overlap_x and overlap_y:
                return True
        return False

    def _handle_input(self) -> str | None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    new = max(0, self.player_lane - 1)
                    if new != self.player_lane:
                        self.player_lane = new
                        self.player_target_x = lane_car_x(self.player_lane)
                        play_lane_switch_sound()
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    new = min(NUM_LANES - 1, self.player_lane + 1)
                    if new != self.player_lane:
                        self.player_lane = new
                        self.player_target_x = lane_car_x(self.player_lane)
                        play_lane_switch_sound()
                elif event.key == pygame.K_UP:
                    # Activate boost
                    if self.boost_powers > 0 and not self.is_invincible:
                        self.boost_powers -= 1
                        self.invincible_timer = self.INVINCIBLE_DURATION
                        self.hud.spawn_confetti(40)
                elif event.key == pygame.K_q:
                    return "quit"
        return None

    def _draw(self):
        # Background, road, scenery
        self.renderer.draw_background()
        self.renderer.draw_road_grime(self.scroll)
        self.renderer.draw_lane_markings(self.scroll)
        self.renderer.draw_trees(self.scroll)
        self.renderer.draw_road_particles(self.scroll, self.level)

        # Enemy cars
        for e in self.enemies:
            self.renderer.draw_car(e.surface, e.x, e.y)

        # Speed lines behind player
        self.renderer.draw_speed_lines(self.player_x, self.player_y, self.level)

        # Player car (with invincibility glow)
        if self.is_invincible:
            # Draw a pulsing glow around the player
            pulse = abs(pygame.time.get_ticks() % 500 - 250) / 250.0
            glow_alpha = int(60 + pulse * 80)
            glow = pygame.Surface((CAR_W + 20, CAR_H + 20), pygame.SRCALPHA)
            glow.fill((180, 80, 255, glow_alpha))
            self.screen.blit(glow, (int(self.player_x) - 10,
                                     int(self.player_y) - 10))

        self.renderer.draw_car(self.player_surface, self.player_x, self.player_y)

        # HUD
        cars_to_next = 5 - (self.score % 5)
        self.hud.draw_top_bar(self.screen, self.score, self.level,
                              self.best_score, cars_to_next)
        self.hud.draw_speedometer(self.screen, self._speed_pct, self._speed_display)
        self.hud.draw_controls(self.screen, self.boost_powers)
        self.hud.draw_popups(self.screen)

        # Boost power indicator
        self.hud.draw_power_indicator(self.screen, self.boost_powers)

        # Booster active display
        if self.is_invincible:
            self.hud.draw_booster_active(self.screen, self.invincible_timer)

        # Confetti (on top of everything)
        self.hud.draw_confetti(self.screen)

        if self.crash_flash > 0:
            self.renderer.draw_crash_flash()
            self.crash_flash -= 1

        pygame.display.flip()

    # ── crash sequence ──────────────────────────────────────────

    def _crash(self) -> str:
        is_new_best = self.score > self.best_score
        if is_new_best:
            self.best_score = self.score
        play_crash_sound()

        for _ in range(6):
            self.renderer.draw_crash_flash()
            pygame.display.flip()
            pygame.time.delay(60)
            self._draw_static_scene()
            pygame.display.flip()
            pygame.time.delay(40)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return "restart"
                    if event.key == pygame.K_c:
                        return "customize"
                    if event.key == pygame.K_q:
                        return "quit"

            self._draw_static_scene()
            self.hud.draw_game_over(self.screen, self.score, self.level,
                                    self.best_score, is_new_best)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _draw_static_scene(self):
        self.renderer.draw_background()
        self.renderer.draw_lane_markings(self.scroll)
        self.renderer.draw_trees(self.scroll)
        for e in self.enemies:
            self.renderer.draw_car(e.surface, e.x, e.y)
        self.renderer.draw_car(self.player_surface, self.player_x, self.player_y)

    # ── public API ──────────────────────────────────────────────

    def play(self) -> str:
        self._reset()

        while True:
            dt = self.clock.tick(FPS) / 1000.0

            result = self._handle_input()
            if result:
                return result

            self._update(dt)
            self._draw()

            if self._collide():
                return self._crash()
