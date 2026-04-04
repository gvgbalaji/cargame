"""Convert PNG images to curses colored half-block art."""

from PIL import Image

# We store art as a list of rows, each row is a list of (char, fg_idx, bg_idx) tuples
# where fg_idx and bg_idx are xterm-256 color indices (-1 = terminal default/transparent)

_pair_cache: dict[tuple[int, int], int] = {}
_next_pair = [50]  # start at 50 to avoid collision with existing pairs 1-7


def _rgb_to_xterm256(r: int, g: int, b: int) -> int:
    """Map (r,g,b) 0-255 to nearest xterm-256 color cube index (16-231)."""
    ri = round(r / 255 * 5)
    gi = round(g / 255 * 5)
    bi = round(b / 255 * 5)
    return 16 + 36 * ri + 6 * gi + bi


def png_to_block_art(path: str, char_w: int, char_h: int) -> list[list[tuple[str, int, int]]]:
    """
    Load PNG, resize to (char_w, char_h*2) pixels, return half-block art.
    Returns list of char_h rows, each row is char_w tuples of (char, fg_256, bg_256).
    Transparent pixels map to -1 (terminal default via use_default_colors).
    """
    img = Image.open(path).convert("RGBA")
    pixel_h = char_h * 2
    img = img.resize((char_w, pixel_h), Image.LANCZOS)
    pixels = img.load()

    rows = []
    for cy in range(char_h):
        row = []
        for cx in range(char_w):
            top_r, top_g, top_b, top_a = pixels[cx, cy * 2]
            bot_r, bot_g, bot_b, bot_a = pixels[cx, cy * 2 + 1]
            fg = _rgb_to_xterm256(top_r, top_g, top_b) if top_a > 32 else -1
            bg = _rgb_to_xterm256(bot_r, bot_g, bot_b) if bot_a > 32 else -1
            row.append(("▀", fg, bg))
        rows.append(row)
    return rows


def get_color_pair(fg: int, bg: int) -> int:
    """Get or allocate a curses color pair for (fg, bg) xterm-256 indices."""
    import curses
    key = (fg, bg)
    if key not in _pair_cache:
        pair_id = _next_pair[0]
        _next_pair[0] += 1
        curses.init_pair(pair_id, fg, bg)
        _pair_cache[key] = pair_id
    return _pair_cache[key]


def art_to_curses(block_art: list[list[tuple[str, int, int]]]) -> list[list[tuple[str, int]]]:
    """
    Convert block art to list of rows of (char, curses_attr) pairs.
    Must be called AFTER curses.start_color() and curses.use_default_colors().
    """
    import curses
    result = []
    for row in block_art:
        crow = []
        for (ch, fg, bg) in row:
            pair_id = get_color_pair(fg, bg)
            crow.append((ch, curses.color_pair(pair_id)))
        result.append(crow)
    return result
