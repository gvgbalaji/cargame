"""Core game loop and logic (Pygame version)."""

import math
import random
import pygame

from .constants import (
    WIDTH, HEIGHT, FPS, CAR_W, CAR_H, NUM_LANES,
    ROAD_LEFT, ROAD_RIGHT,
    lane_car_x,
)
from .cars import make_player_surface, PLAYER_STYLES
from .enemy import (Enemy, Tanker, Bomb, Bullet, PowerUp,
                    _load_vehicles, _load_tanker, _load_bomb, _load_powerup_surfaces)
from .renderer import Renderer
from .hud import HUD
from .surface_cache import SurfaceCache
from .sound import (play_crash_sound, play_lane_switch_sound, play_pass_sound,
                    set_sound_config, toggle_sound, is_sound_enabled,
                    play_background_music, stop_background_music)
from .scores import init_db, save_score, get_top5, get_best_score


class Game:
    """One game session: handles logic, rendering, input."""

    BASE_SPEED   = 3.0    # pixels per frame at level 1
    SPEED_STEP   = 0.8    # extra px/frame per level
    INVINCIBLE_DURATION = 3.0   # seconds
    CURVY_MOVE_SPEED = 5  # px per frame when arrow held in curvy mode

    def __init__(self, screen: pygame.Surface, skin_index: int = 0,
                 sound_theme: str = "engine", curvy: bool = False):
        self.screen      = screen
        self.clock       = pygame.time.Clock()
        self.curvy       = curvy
        self.sound_theme = sound_theme
        self.renderer    = Renderer(screen, curvy=curvy)
        self.hud         = HUD()
        self.best_score  = 0

        self._set_skin(skin_index)
        set_sound_config(enabled=(sound_theme != "silent"), theme=sound_theme)
        init_db()
        self.db_best = get_best_score()

        # Pre-warm asset loading to prevent first-game lag
        _load_vehicles()
        _load_tanker()
        _load_bomb()
        _load_powerup_surfaces()

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
        self.enemies:  list[Enemy]   = []
        self.bombs:    list[Bomb]    = []
        self.bullets:  list[Bullet]  = []
        self.powerups: list[PowerUp] = []
        self.score          = 0
        self.level          = 1
        self.scroll         = 0.0
        self.spawn_cd       = 60
        self.crash_flash    = 0

        # Invincibility / boost power
        self.boost_powers       = 0   # available boosts
        self.invincible_timer   = 0.0 # seconds remaining
        self._last_power_score  = 0   # track when last power was earned

        # Shooting power
        self.shoot_powers       = 0
        self._last_shoot_score  = 0

        # Road power-up pickups
        self._last_powerup_score = 0

        # Confetti & new fact
        self.hud.confetti.clear()
        self.hud.new_fact()

        # Start background music if race theme
        play_background_music(self.sound_theme)

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

        # Update scene mood based on level
        self.renderer.update_scene(self.level)

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

        # Move enemies; fire bombs from Tankers
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

                # Award shoot power every 50 points
                if self.score >= 50 and self.score // 50 > self._last_shoot_score // 50:
                    self.shoot_powers += 1
                    self._last_shoot_score = self.score
                    self.hud.add_popup("FIRE +1!", WIDTH // 2 - 40,
                                       HEIGHT // 2 + 35, (255, 140, 40))

                # Confetti every 20 points
                if self.score % 20 == 0:
                    self.hud.spawn_confetti(60)

            # Tanker fires bombs while in upper half of screen (before crossing midpoint)
            if isinstance(e, Tanker) and 0 < e.y < HEIGHT // 2:
                shots = e.tick(dt)
                for _ in range(shots):
                    if len(self.bombs) < 8:   # cap active bombs
                        bx = e.x + e.width / 2
                        self.bombs.append(Bomb(bx, e.y + e.height))

        self.enemies = [e for e in self.enemies if e.y < HEIGHT + e.height]

        # Move bombs and check pass/dodge
        for b in self.bombs:
            b.y += spd + b.speed_bonus
            if not b.passed and b.y > self.player_y + CAR_H:
                b.passed = True
                self.score += 2
                self.hud.add_popup("+2 DODGE!", int(b.x + b.width / 2),
                                   int(self.player_y), (255, 220, 60))
        self.bombs = [b for b in self.bombs if b.y < HEIGHT + b.height]

        # Move player bullets upward; check hits
        for bl in self.bullets:
            bl.y -= Bullet.SPEED
            if bl.y < -Bullet.H:
                bl.active = False
                continue
            for e in self.enemies:
                if (bl.active
                        and bl.x < e.x + e.width  and bl.x + Bullet.W > e.x
                        and bl.y < e.y + e.height and bl.y + Bullet.H > e.y):
                    bl.active = False
                    e.y = HEIGHT + e.height + 10   # push off-screen → removed next tick
                    self.score += 1
                    self.level = 1 + self.score // 5
                    self.hud.add_popup("+1 HIT!", int(e.x + e.width / 2),
                                       int(e.y - 30), (255, 140, 40))
        self.bullets = [bl for bl in self.bullets if bl.active]

        # Spawn road power-up every 40 points (only when player has no powers)
        if (self.score >= 40
                and self.score // 40 > self._last_powerup_score // 40
                and not self.powerups):
            self._last_powerup_score = self.score
            has_boost = self.boost_powers > 0
            has_fire  = self.shoot_powers > 0
            # Determine which kinds are offerable
            choices = []
            if not has_boost:
                choices.append("boost")
            if not has_fire and not has_boost:   # don't offer fire if already has boost
                choices.append("fire")
            if choices:
                taken = {e.lane for e in self.enemies if e.y > 0}
                taken |= {p.lane for p in self.powerups}
                free = [l for l in range(NUM_LANES) if l not in taken]
                if free:
                    kind = random.choice(choices)
                    lane = random.choice(free)
                    self.powerups.append(PowerUp(lane, kind))

        # Move and tick power-ups; collect on player overlap
        px, py = self.player_x, self.player_y
        pw, ph = CAR_W, CAR_H
        for pu in self.powerups:
            pu.y += spd
            if not pu.collected:
                # Collision with player car
                if (px + pw - 10 > pu.x + 4 and pu.x + pu.width - 4 > px + 10
                        and py + ph - 10 > pu.y + 4 and pu.y + pu.height - 4 > py + 10):
                    pu.collected = True
                    if pu.kind == "fire":
                        self.shoot_powers += 1
                        self.hud.add_popup("FIRE +1!", int(pu.x), int(pu.y),
                                           (100, 180, 255))
                    else:
                        self.boost_powers += 1
                        self.hud.add_popup("BOOST +1!", int(pu.x), int(pu.y),
                                           (200, 140, 255))
        self.powerups = [pu for pu in self.powerups if pu.tick(dt) and pu.y < HEIGHT + pu.height]

        # Update popups & confetti
        self.hud.update_popups(dt)
        self.hud.update_confetti(dt)

    def _spawn(self):
        taken = {e.lane for e in self.enemies if e.y < e.height + 30}
        free = [l for l in range(NUM_LANES) if l not in taken]
        if free:
            lane = random.choice(free)
            # After level 5: ~35% chance to spawn a shooting Tanker
            if self.level > 5 and random.random() < 0.35:
                self.enemies.append(Tanker(lane))
            else:
                self.enemies.append(Enemy(lane))

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
        # Check bomb collisions
        for b in self.bombs:
            if b.passed:
                continue
            overlap_x = (px + pw - 8 > b.x + 6) and (b.x + b.width - 6 > px + 8)
            overlap_y = (py + ph - 8 > b.y + 6) and (b.y + b.height - 6 > py + 8)
            if overlap_x and overlap_y:
                return True
        return False

    def _handle_input(self) -> str | None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if HUD.MUTE_ICON_RECT.collidepoint(event.pos):
                    toggle_sound()
            if event.type == pygame.KEYDOWN:
                if not self.curvy:
                    # Straight mode: discrete lane switching
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
                if event.key == pygame.K_UP:
                    if self.boost_powers > 0 and not self.is_invincible:
                        self.boost_powers -= 1
                        self.invincible_timer = self.INVINCIBLE_DURATION
                        self.hud.spawn_confetti(40)
                elif event.key in (pygame.K_DOWN, pygame.K_SPACE):
                    if self.shoot_powers > 0:
                        self.shoot_powers -= 1
                        cx = self.player_x + CAR_W / 2
                        pcx = self.renderer.road_curve(self.player_y, self.scroll)
                        self.bullets.append(Bullet(cx + pcx, self.player_y))
                elif event.key in (pygame.K_m, pygame.K_F10):
                    toggle_sound()
                elif event.key == pygame.K_q:
                    return "quit"

        # Curvy mode: continuous movement while keys held
        if self.curvy:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player_target_x -= self.CURVY_MOVE_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player_target_x += self.CURVY_MOVE_SPEED
            # Clamp within road bounds
            min_x = ROAD_LEFT + 5
            max_x = ROAD_RIGHT - CAR_W - 5
            self.player_target_x = max(min_x, min(max_x, self.player_target_x))

        return None

    def _draw(self):
        dt = self.clock.get_time() / 1000.0

        # Background, road, scenery
        self.renderer.draw_background()
        self.renderer.draw_mountains(self.level)
        self.renderer.draw_road(self.scroll)
        self.renderer.draw_road_grime(self.scroll)
        self.renderer.draw_lane_markings(self.scroll)
        self.renderer.draw_trees(self.scroll)
        self.renderer.draw_sun_moon()
        self.renderer.draw_river(self.scroll, self.level)
        self.renderer.draw_birds(dt)
        self.renderer.draw_road_particles(self.scroll, self.level)

        # Enemy cars
        for e in self.enemies:
            self.renderer.draw_car(e.surface, e.x, e.y, self.scroll)

        # Bombs — draw with orange warning glow
        for b in self.bombs:
            cx = self.renderer.road_curve(b.y + b.height / 2, self.scroll)
            bx_draw = int(b.x + cx)
            by_draw = int(b.y)
            # Pulsing glow ring — reuse cached surface instead of allocating per bomb
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.008)) * 30 + 20
            glow_r = b.width // 2 + 12
            glow_dim = glow_r * 2
            glow_surf = SurfaceCache.get(glow_dim, glow_dim)
            pygame.draw.circle(glow_surf, (255, 100, 0, int(pulse * 3)),
                               (glow_r, glow_r), glow_r)
            self.screen.blit(glow_surf,
                             (bx_draw + b.width // 2 - glow_r,
                              by_draw + b.height // 2 - glow_r))
            self.screen.blit(b.surface, (bx_draw, by_draw))

        # Road power-up pickups
        ticks = pygame.time.get_ticks()
        for pu in self.powerups:
            if pu.collected:
                continue
            cx = self.renderer.road_curve(pu.y + pu.height / 2, self.scroll)
            px_draw = int(pu.x + cx)
            py_draw = int(pu.y)
            # Blink when timer < 0.7s (last 35% of life)
            if pu.timer_started and pu.timer < 0.7:
                if int(ticks / 120) % 2 == 0:
                    continue   # skip this frame = blink
            # Glow ring behind icon — reuse cached surface
            glow_color = (60, 120, 255, 80) if pu.kind == "fire" else (180, 80, 255, 80)
            glow_r = pu.SIZE // 2 + 10
            glow_dim = glow_r * 2
            glow_surf = SurfaceCache.get(glow_dim, glow_dim)
            pygame.draw.circle(glow_surf, glow_color, (glow_r, glow_r), glow_r)
            self.screen.blit(glow_surf,
                             (px_draw + pu.SIZE // 2 - glow_r,
                              py_draw + pu.SIZE // 2 - glow_r))
            # Icon itself
            if pu.surface:
                self.screen.blit(pu.surface, (px_draw, py_draw))
            else:
                col = (60, 140, 255) if pu.kind == "fire" else (160, 80, 255)
                pygame.draw.circle(self.screen, col,
                                   (px_draw + pu.SIZE // 2, py_draw + pu.SIZE // 2),
                                   pu.SIZE // 2)
            # Timer bar below icon
            if pu.timer_started:
                bar_w = pu.SIZE
                frac  = max(0, pu.timer / PowerUp.LIFETIME)
                bar_col = (80, 200, 80) if frac > 0.5 else (255, 160, 0) if frac > 0.25 else (255, 60, 60)
                pygame.draw.rect(self.screen, (30, 30, 40),
                                 (px_draw, py_draw + pu.SIZE + 3, bar_w, 4), border_radius=2)
                pygame.draw.rect(self.screen, bar_col,
                                 (px_draw, py_draw + pu.SIZE + 3, int(bar_w * frac), 4),
                                 border_radius=2)

        # Player bullets — firepower lightning orbs flying upward
        fp_bullet = self.hud._firepower_bullet
        for bl in self.bullets:
            cx = self.renderer.road_curve(bl.y, self.scroll)
            bx, by = int(bl.x + cx), int(bl.y)
            if fp_bullet:
                self.screen.blit(fp_bullet, (bx, by))
            else:
                # Fallback: electric blue beam
                pygame.draw.rect(self.screen, (80, 160, 255),
                                 (bx, by, Bullet.W, Bullet.H), border_radius=4)
                pygame.draw.rect(self.screen, (200, 230, 255),
                                 (bx + 2, by, Bullet.W - 4, 6), border_radius=2)

        # Speed lines behind player
        self.renderer.draw_speed_lines(self.player_x, self.player_y,
                                       self.level, self.scroll)

        # Headlights at night (shifted by curve)
        pcx = self.renderer.road_curve(self.player_y + CAR_H / 2, self.scroll)
        self.renderer.draw_headlights(self.player_x + pcx, self.player_y)

        # Player car (with invincibility glow) — reuse cached surface
        if self.is_invincible:
            pulse = abs(pygame.time.get_ticks() % 500 - 250) / 250.0
            glow_alpha = int(60 + pulse * 80)
            glow = SurfaceCache.get(CAR_W + 20, CAR_H + 20)
            glow.fill((180, 80, 255, glow_alpha))
            self.screen.blit(glow, (int(self.player_x + pcx) - 10,
                                     int(self.player_y) - 10))

        self.renderer.draw_car(self.player_surface, self.player_x,
                               self.player_y, self.scroll)

        # HUD
        cars_to_next = 5 - (self.score % 5)
        self.hud.draw_top_bar(self.screen, self.score, self.level,
                              self.db_best, cars_to_next)
        self.hud.draw_speedometer(self.screen, self._speed_pct, self._speed_display)
        self.hud.draw_controls(self.screen, self.boost_powers, self.shoot_powers)
        self.hud.draw_mute_icon(self.screen, is_sound_enabled())
        self.hud.draw_popups(self.screen)

        # Fire power indicator — right side column (firepower.png icons)
        self.hud.draw_fire_indicator(self.screen, self.shoot_powers)
        # Boost / invincible power indicator — right side, second column
        self.hud.draw_power_indicator(self.screen, self.boost_powers)
        # F1 fact — bottom right
        self.hud.draw_f1_fact(self.screen, self.level)

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
        stop_background_music()
        is_new_best = self.score > self.db_best
        if is_new_best:
            self.best_score = self.score
        save_score(self.score, self.level)
        self.db_best = get_best_score()   # refresh from DB after saving
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
                                    self.best_score, is_new_best, get_top5())
            pygame.display.flip()
            self.clock.tick(FPS)

    def _draw_static_scene(self):
        self.renderer.draw_background()
        self.renderer.draw_mountains(self.level)
        self.renderer.draw_road(self.scroll)
        self.renderer.draw_lane_markings(self.scroll)
        self.renderer.draw_trees(self.scroll)
        self.renderer.draw_sun_moon()
        self.renderer.draw_river(self.scroll, self.level)
        for e in self.enemies:
            self.renderer.draw_car(e.surface, e.x, e.y, self.scroll)
        for b in self.bombs:
            cx = self.renderer.road_curve(b.y + b.height / 2, self.scroll)
            self.screen.blit(b.surface, (int(b.x + cx), int(b.y)))
        self.renderer.draw_car(self.player_surface, self.player_x,
                               self.player_y, self.scroll)

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
