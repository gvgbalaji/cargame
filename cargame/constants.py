# ── Window ────────────────────────────────────────────────────
WIDTH  = 1200
HEIGHT = 800
FPS    = 60
TITLE  = "Car Dodge"

# ── Road layout (pixel coords) ───────────────────────────────
NUM_LANES   = 3
ROAD_LEFT   = 150
ROAD_WIDTH  = 480
ROAD_RIGHT  = ROAD_LEFT + ROAD_WIDTH
LANE_WIDTH  = ROAD_WIDTH // NUM_LANES
ROAD_CENTER = ROAD_LEFT + ROAD_WIDTH // 2

# ── Car dimensions (pixels) ──────────────────────────────────
CAR_W = 110
CAR_H = 150

# ── Colors ────────────────────────────────────────────────────
# Road / environment
COL_ASPHALT     = (45, 45, 50)
COL_ASPHALT_L   = (55, 55, 60)
COL_SHOULDER    = (70, 70, 75)
COL_LANE_MARK   = (220, 200, 60)
COL_EDGE_MARK   = (255, 255, 255)
COL_GRASS       = (34, 120, 34)
COL_GRASS_DARK  = (28, 95, 28)
COL_GRASS_LIGHT = (45, 145, 45)
COL_SKY_TOP     = (15, 15, 35)
COL_SKY_BOT     = (40, 40, 80)

# HUD
COL_HUD_BG      = (10, 10, 15, 180)
COL_HUD_BORDER  = (80, 200, 255)
COL_HUD_TEXT    = (255, 255, 255)
COL_HUD_ACCENT  = (0, 200, 255)
COL_HUD_WARN    = (255, 80, 60)
COL_HUD_GOOD    = (80, 255, 120)
COL_HUD_GOLD    = (255, 215, 0)
COL_HUD_DIM     = (140, 140, 160)

# Cars
COL_PLAYER_COLORS = [
    ("BLUE",    (30, 120, 255)),
    ("RED",     (220, 40, 40)),
    ("GREEN",   (40, 200, 80)),
    ("ORANGE",  (255, 140, 20)),
    ("PURPLE",  (160, 60, 220)),
    ("WHITE",   (230, 230, 240)),
]

COL_ENEMY_COLORS = [
    (220, 40, 40),
    (40, 200, 80),
    (255, 140, 20),
    (160, 60, 220),
    (230, 230, 240),
    (255, 200, 60),
]

# ── Sound themes ──────────────────────────────────────────────
SOUND_THEMES = [
    ("ENGINE",  "engine",  "Realistic engine buzz"),
    ("RETRO",   "retro",   "Arcade beeps & booms"),
    ("MINIMAL", "minimal", "Whoosh & screech"),
    ("RACE",    "race",    "Race track music (MP3)"),
    ("SILENT",  "silent",  "No sound"),
]

# ── Level tips ────────────────────────────────────────────────
LEVEL_TIPS = [
    "Trust the RNG",
    "It ends badly",
    "Buckle up, fam",
    "Mom's watching",
    "The road wins",
    "YOLO activated",
    "No brakes club",
    "Just a sim bro",
    "RIP, my palms",
    "Touch grass? No",
    "Goodbye, world",
    "404 skill lost",
    "Speed = fate",
    "Why am I here?",
]


def lane_center_x(lane: int) -> float:
    """Return the center x-pixel of the given lane."""
    return ROAD_LEFT + lane * LANE_WIDTH + LANE_WIDTH / 2


def lane_car_x(lane: int) -> float:
    """Return the left x-pixel to center a car in the given lane."""
    return lane_center_x(lane) - CAR_W / 2
