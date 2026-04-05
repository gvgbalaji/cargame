"""SQLite-backed top-5 leaderboard."""

import os
import sqlite3
from datetime import datetime

_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scores.db")


def init_db() -> None:
    with sqlite3.connect(_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                score       INTEGER NOT NULL,
                level       INTEGER NOT NULL,
                achieved_at TEXT    NOT NULL
            )
        """)


def save_score(score: int, level: int) -> None:
    """Insert score and prune to keep only top 5."""
    if score <= 0:
        return
    with sqlite3.connect(_DB) as conn:
        conn.execute(
            "INSERT INTO scores (score, level, achieved_at) VALUES (?,?,?)",
            (score, level, datetime.now().strftime("%d %b  %H:%M")),
        )
        conn.execute("""
            DELETE FROM scores
            WHERE id NOT IN (
                SELECT id FROM scores ORDER BY score DESC LIMIT 5
            )
        """)


def get_top5() -> list[tuple[int, int, str]]:
    """Return [(score, level, datetime_str), ...] top 5 by score."""
    with sqlite3.connect(_DB) as conn:
        return conn.execute(
            "SELECT score, level, achieved_at FROM scores ORDER BY score DESC LIMIT 5"
        ).fetchall()
