# ── Road layout ────────────────────────────────────────────────
ROAD_LEFT  = 6        # x-column of left road edge
ROAD_WIDTH = 36       # total drivable width
NUM_LANES  = 3
LANE_WIDTH = ROAD_WIDTH // NUM_LANES   # 12 per lane

# ── Car dimensions ─────────────────────────────────────────────
CAR_W = 7
CAR_H = 3

# ── Terminal size floor ────────────────────────────────────────
MIN_COLS = ROAD_LEFT + ROAD_WIDTH + 12
MIN_ROWS = 24

# ── Right-side scenery layout (relative to road_right = 42) ────
GRASS_EXTRA_W = 10
TREE_COL_1    = 14    # offset from road_right
TREE_COL_2    = 19    # offset from road_right (staggered)
SIDEBAR_X_OFF = 24    # offset from road_right where panel starts
SIDEBAR_IW    = 16    # inner width of panel
SIDEBAR_H     = 16    # rows tall

# ── Color pair IDs ─────────────────────────────────────────────
CP_RED     = 1
CP_GREEN   = 2
CP_YELLOW  = 3
CP_BLUE    = 4
CP_CYAN    = 5
CP_MAGENTA = 6
CP_WHITE   = 7

# ── Car artwork (7 wide × 3 tall) ──────────────────────────────
# Player: top-down sedan view — rounded body (╭╮╰╯), windshield (░░), mirror (▴)
# Matches the rounded red car silhouette: curved front/rear, glass panels visible
PLAYER_ART = [
    "╭─░░░─╮",   # rounded front hood + windshield glass
    "│ ─▴─ │",   # cabin roof + rearview mirror stalk
    "╰─░░░─╯",   # rounded rear + rear window glass
]

ENEMY_ARTS = [
    ["╔═════╗", "║ ● ● ║", "╚══╦══╝"],   # Sedan
    ["╔═╦═╦═╗", "╠═════╣", "╚═════╝"],   # SUV
    ["╔═════╗", "║█   █║", "╚══╦══╝"],   # Sports
    ["╔═════╗", "║▓▓▓▓▓║", "╚═════╝"],   # Van
    ["╔═════╗", "╠ ● ● ╣", "╚═╦═╦═╝"],   # Racer
]

ENEMY_COLORS = [CP_RED, CP_MAGENTA, CP_CYAN, CP_BLUE]

# ── Player colour picker options ────────────────────────────────
PLAYER_COLOR_OPTIONS: list[tuple[str, int]] = [
    ("YELLOW",  CP_YELLOW),
    ("CYAN",    CP_CYAN),
    ("GREEN",   CP_GREEN),
    ("MAGENTA", CP_MAGENTA),
    ("WHITE",   CP_WHITE),
    ("RED",     CP_RED),
]

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


def lane_x(lane: int) -> int:
    """Left-edge x position of a car centred in the given lane."""
    return ROAD_LEFT + lane * LANE_WIDTH + (LANE_WIDTH - CAR_W) // 2
