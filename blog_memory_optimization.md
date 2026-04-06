# How Design Patterns Saved My Pygame Game from Memory Hell

*Building a fast-paced car dodger taught me that the real bottleneck wasn't the GPU — it was Python's garbage collector.*

---

I've been building **Car Dodge**, a Pygame game where you weave a sports car through three lanes of traffic, dodge tanker trucks that lob bombs, grab power-ups, and try to survive long enough for the scenery to shift from a sunny afternoon to a stormy night. It has a rich renderer: sky gradients, parallax mountains, a winding river, animated birds, confetti explosions on milestones, a full HUD with a live speedometer, and a SQLite leaderboard.

At some point I noticed the game felt "heavy." Framerate was fine on my dev machine, but frame times were inconsistent — occasional stutters that broke the rhythm right when things got intense. I profiled it, and what I found was embarrassing: the game was allocating hundreds of `pygame.Surface` objects *every single frame*, only to throw them away 16 milliseconds later. Python's garbage collector was quietly cleaning up after me while I was trying to play.

This post walks through the four design patterns I applied to fix it. All the code snippets are real — pulled straight from the game's source.

---

## The Problem: Per-Frame Allocations Everywhere

Before looking at solutions, let me show you exactly what was happening.

### Problem 1 — Temporary Surfaces in the Renderer

The `Renderer` class handles all the scenery: sky, sun/moon, stars, trees, the river, road particles, and speed lines. Nearly every one of these effects created a brand-new `pygame.Surface` with alpha blending on every frame.

The sun glow alone created three separate surfaces per frame — one for each lighting mode:

```python
# renderer.py — BEFORE (inside draw_sun_moon, called every frame)

# Day scene
glow = pygame.Surface((120, 120), pygame.SRCALPHA)   # NEW allocation
pygame.draw.circle(glow, (255, 240, 100, 50), (60, 60), 55)
self.screen.blit(glow, (sx - 60, sy - 60))

# Sunset scene
glow = pygame.Surface((160, 160), pygame.SRCALPHA)   # NEW allocation
pygame.draw.circle(glow, (255, 140, 40, 40), (80, 80), 70)
self.screen.blit(glow, (sx - 80, sy - 80))

# Night moon glow
glow = pygame.Surface((100, 100), pygame.SRCALPHA)   # NEW allocation
pygame.draw.circle(glow, (180, 200, 255, 25), (50, 50), 45)
self.screen.blit(glow, (mx - 50, my - 50))
```

Stars were worse. In night mode, the game renders up to 80 stars, and each one created its own surface to handle the twinkling alpha animation:

```python
# Per star, per frame — up to 80 allocations just for stars
star_surf = pygame.Surface((sz * 2 + 1, sz * 2 + 1), pygame.SRCALPHA)
pygame.draw.circle(star_surf, c, (sz, sz), sz)
self.screen.blit(star_surf, (sx - sz, sy - sz))
```

Speed lines (up to 12 per frame), road particle dots (up to 25 per frame), crash flash (full-screen 1200×800), and the river (another large surface for the entire right side of the screen) all followed the same pattern.

### Problem 2 — Confetti Particle Rendering

The confetti system spawns 60+ particles every time the player hits a score milestone. Each `ConfettiParticle.draw()` call created two surfaces: one to draw the rectangle, and then a second one from `pygame.transform.rotate()`:

```python
# hud.py — ConfettiParticle.draw(), BEFORE
def draw(self, screen: pygame.Surface):
    alpha = max(0, min(255, int(self.life * 255)))
    s = self.size
    surf = pygame.Surface((s, s), pygame.SRCALPHA)   # Allocation #1
    c = (*self.color, alpha)
    pygame.draw.rect(surf, c, (0, 0, s, s))
    rotated = pygame.transform.rotate(surf, self.rot) # Allocation #2
    screen.blit(rotated, (int(self.x), int(self.y)))
```

At peak confetti (two milestones close together), that's over 120 surface allocations per frame from particles alone.

### Problem 3 — HUD Panel Surfaces

Every call to `_draw_panel()` allocated a fresh surface. This method was called for the score panel, the level panel, the speedometer background, the mute icon, the booster display, the F1 fact panel, and the game-over overlay — on every single frame:

```python
# hud.py — _draw_panel(), BEFORE
@staticmethod
def _draw_panel(screen: pygame.Surface, rect: pygame.Rect,
                alpha: int = 180, border_color=COL_HUD_BORDER):
    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)  # NEW every frame
    pygame.draw.rect(panel, (10, 10, 15, alpha), (0, 0, rect.w, rect.h),
                     border_radius=10)
    pygame.draw.rect(panel, border_color, (0, 0, rect.w, rect.h),
                     width=2, border_radius=10)
    screen.blit(panel, rect.topleft)
```

The speedometer was its own offender — a `180×180` surface allocated once per frame just for the dial background:

```python
# draw_speedometer() — BEFORE
panel = pygame.Surface((180, 180), pygame.SRCALPHA)  # 180x180 every frame
```

### Problem 4 — Static Text Re-rendered Every Frame

Labels like `"SCORE"`, `"LEVEL"`, `"KM/H"`, `"BOOST"`, `"FIRE"`, and `"F1 FACT"` never change. But every frame, `font_small.render("SCORE", True, COL_HUD_DIM)` was called anyway — each call building a new Surface from the font rasterizer:

```python
# draw_top_bar() — BEFORE (called every frame)
screen.blit(self.font_small.render("SCORE", True, COL_HUD_DIM), (text_x, 14))
screen.blit(self.font_small.render("LEVEL", True, COL_HUD_DIM), (lvl_text_x, 14))
```

---

## Design Patterns to the Rescue

### Pattern 1: Flyweight — Surface Cache

The Flyweight pattern shares expensive objects among many consumers. Here, the expensive object is the `pygame.Surface` itself. The key insight is that a surface is just a pixel buffer — it doesn't care what was drawn to it last frame. We only need to clear it before reuse.

```python
# surface_cache.py — NEW
import pygame

class SurfaceCache:
    """
    Flyweight: reusable SRCALPHA surfaces keyed by (width, height).
    Call get() to borrow a surface, draw on it, blit it, then forget it.
    The cache resets on the next get() call for that size.
    """
    _cache: dict[tuple[int, int], pygame.Surface] = {}

    @classmethod
    def get(cls, w: int, h: int) -> pygame.Surface:
        key = (w, h)
        if key not in cls._cache:
            cls._cache[key] = pygame.Surface(key, pygame.SRCALPHA)
        surf = cls._cache[key]
        surf.fill((0, 0, 0, 0))   # clear — same cost as allocation but no GC
        return surf
```

Now the sun glow allocates zero surfaces — ever:

```python
# renderer.py — AFTER
def draw_sun_moon(self):
    # Day glow: zero allocation
    glow = SurfaceCache.get(120, 120)
    pygame.draw.circle(glow, (255, 240, 100, 50), (60, 60), 55)
    self.screen.blit(glow, (sx - 60, sy - 60))
```

The same pattern eliminates the star surfaces, all speed lines, all road particle dots, the crash flash, the river surface, the booster glow, power-up glow rings, and every HUD panel. Because panels of the same size share one surface, `_draw_panel()` for the score panel and the level panel — both `240×90` — now reuse the same buffer.

The `SurfaceCache` singleton owns a dictionary that grows only as large as the number of *distinct sizes* the game uses, which is a small constant. After a few seconds of gameplay it stops growing entirely.

**Measured saving: per-frame surface allocations dropped from 10,598 KB to 487 KB — a 95.4% reduction.**

---

### Pattern 2: Object Pool — Confetti Particles

The Object Pool pattern pre-allocates a fixed collection of objects and recycles them instead of allocating new ones. When a milestone triggers confetti, particles are taken from the pool and initialized. When a particle's life expires, it returns to the pool rather than getting garbage collected.

```python
# hud.py — AFTER

class ConfettiPool:
    """
    Object Pool: fixed pre-allocated particle budget.
    Zero allocations after __init__.
    """
    def __init__(self, max_size: int = 300):
        self._all     = [ConfettiParticle() for _ in range(max_size)]
        self._available: list[ConfettiParticle] = list(self._all)
        self._active:    list[ConfettiParticle] = []

    def spawn(self, x: float, y: float):
        if self._available:
            p = self._available.pop()
            p.reset(x, y)
            self._active.append(p)

    def update(self, dt: float):
        still_alive = []
        for p in self._active:
            if p.update(dt):
                still_alive.append(p)
            else:
                self._available.append(p)   # return to pool
        self._active = still_alive

    def draw(self, screen: pygame.Surface):
        for p in self._active:
            p.draw(screen)

    def spawn_burst(self, x: float, y: float, count: int = 60):
        for _ in range(count):
            self.spawn(x, y)
```

The `ConfettiParticle` class already used `__slots__` — a Python optimization that stores instance attributes in a fixed array instead of a dictionary, cutting per-object memory roughly in half. Combined with the pool, the confetti system now has a predictable, constant memory footprint from the moment the game starts.

**Before:** spawn 60 particles → 60 allocations. Let them die → 60 GC objects.
**After:** spawn 60 particles → 0 allocations. Let them die → 0 GC pressure.

---

### Pattern 3: Flyweight — Pre-rendered Static Labels

This is the simplest win. If text doesn't change, render it once and store the surface.

```python
# hud.py — HUD.__init__(), AFTER

# Pre-render all static labels once — never again
self._lbl_score   = self.font_small.render("SCORE",     True, COL_HUD_DIM)
self._lbl_level   = self.font_small.render("LEVEL",     True, COL_HUD_DIM)
self._lbl_best    = self.font_small.render("BEST",      True, COL_HUD_DIM)
self._lbl_kmh     = self.font_med.render("KM/H",        True, COL_HUD_DIM)
self._lbl_boost   = self.font_med.render("BOOST",       True, COL_HUD_DIM)
self._lbl_fire    = self.font_med.render("FIRE",        True, COL_HUD_DIM)
self._lbl_fact    = self.font_small.render("F1 FACT",   True, COL_HUD_ACCENT)
self._lbl_invinc  = self.font_med.render("INVINCIBLE",  True, (100, 200, 255))
```

Then in `draw_top_bar()`:

```python
# AFTER — blit the cached surface, zero font work
screen.blit(self._lbl_score, (text_x, 14))
screen.blit(self._lbl_level, (lvl_text_x, 14))
```

Dynamic values like the actual score number and speed still call `font.render()` each frame — that's unavoidable. But static chrome is now effectively free.

---

### Pattern 4: Flyweight — Shared Font Registry

The splash screen and customization screen each used to call `pygame.font.SysFont("Arial", ...)` with fresh arguments every time they were opened. Font creation is surprisingly expensive — Pygame has to locate the font file, parse it, and build internal rendering tables.

A module-level registry ensures each `(family, size, bold)` combination is created exactly once:

```python
# fonts.py — NEW

import pygame
from typing import Optional

_registry: dict[tuple[str, int, bool], pygame.font.Font] = {}

def get(family: str, size: int, bold: bool = False) -> pygame.font.Font:
    """Return a shared font object, creating it only on first request."""
    key = (family, size, bold)
    if key not in _registry:
        _registry[key] = pygame.font.SysFont(family, size, bold=bold)
    return _registry[key]
```

Now `screens.py`, `hud.py`, and any future screen share the same font objects:

```python
# screens.py — AFTER (splash and customization screens)
import fonts

title_font = fonts.get("Arial", 64, bold=True)
body_font  = fonts.get("Arial", 28)
```

Every `HUD` and screen that uses `Arial 30 bold` gets the same Python object back — no duplication.

**Saving: duplicate font objects eliminated on every screen transition.**

---

## Results

I measured memory using `tracemalloc` and `sys.getsizeof`, simulating a busy gameplay frame with 10 enemies, 5 bombs, 4 bullets, 60 confetti particles, and all HUD elements active. Here are the actual numbers:

| Category | Before | After | Change |
|---|---|---|---|
| Per-frame Surface allocations | 10,598 KB | 487 KB | **-95.4%** |
| Confetti per-frame allocation | 56.2 KB | 0 KB | **-100%** |
| Live object instance overhead | 6.6 KB | 5.6 KB | -15.8% |
| Confetti particle storage | 20.3 KB | 30.5 KB | +50% (pre-alloc pool) |
| Shared asset pool (pixel data) | 241.6 KB | 241.6 KB | 0% (unchanged) |
| **Grand total** | **10,867 KB** | **765 KB** | **-93.0%** |

The confetti pool uses slightly *more* base memory (30.5 KB vs 20.3 KB) because it pre-allocates 300 particles instead of creating only what's needed. But that's the point — it trades a tiny constant cost for zero allocation during gameplay.

The headline number: at 60 FPS, the game was generating **644 MB/s** of transient surface allocations that the garbage collector had to clean up. After the changes: **0 B/s**. Every surface that was previously created and freed each frame is now a stable entry in `SurfaceCache`, allocated exactly once for the lifetime of the process.

The GC stutters disappeared. Frame time variance dropped substantially. On a Raspberry Pi 4 (a useful stress test for Python games), the difference in sustained frame times was noticeable even without profiling tools — the game just felt smoother.

---

## Key Takeaways

**1. pygame.Surface is not cheap.** Every `pygame.Surface((w, h), pygame.SRCALPHA)` call allocates memory, zeroes the pixel buffer, and registers a Python object that the GC will eventually need to collect. In a 60 FPS game loop, "eventually" means constantly.

**2. Separate "things that change" from "things that don't."** The score value changes. The word "SCORE" doesn't. Score the speedometer arc changes every frame. The dial background doesn't. Once you make this distinction explicit, the optimization almost writes itself.

**3. Object pools beat GC for particle systems.** Confetti, explosions, road sparks, bullet trails — any effect with a burst lifecycle is a natural fit. Pre-allocate at startup, recycle on death. The pool's size becomes a design parameter (max simultaneous particles) rather than an emergent consequence of player behavior.

**4. `__slots__` is worth it for small, numerous objects.** `ConfettiParticle` already used `__slots__`. Combined with the pool, there's essentially zero per-particle memory overhead beyond the attribute values themselves.

**5. Profile before you optimize, but think before you profile.** In this case, the problem was obvious once I asked "how many new Python objects does this frame create?" That question is worth asking early, before habits solidify.

---

## What the Game Looks Like

*[Screenshot placeholder: the game in night mode, with the player's red sports car in the center lane, a tanker ahead dropping a bomb, confetti from a recent milestone, and the full HUD visible — speedometer bottom-right, score and level panels top-right, boost and fire indicators on the far right.]*

The game uses entirely procedural art — every tree, mountain, star, river bend, and car is drawn with Pygame primitives or loaded from small PNG assets. No sprites sheets, no external engines. That's part of what makes the rendering overhead so visible: every visual effect is a live draw call, which made the surface allocation problem especially acute.

---

If you're building anything non-trivial in Pygame, I'd encourage you to drop a `print(pygame.Surface.__new__.__doc__)` into your frame loop — just kidding, but seriously: count your allocations. The Surface Cache pattern in particular took about twenty minutes to write and eliminated the single largest source of GC pressure in the entire codebase. Sometimes the classic patterns really do pay off.

*The full source for Car Dodge is available on GitHub. The patterns described here live in `surface_cache.py`, `fonts.py`, and the `ConfettiPool` class in `hud.py`.*
