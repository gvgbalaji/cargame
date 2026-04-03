#!/usr/bin/env python3
"""
CAR DODGE — Terminal Car Dodging Game
Dodge oncoming cars for as long as you can!

Usage:
    python main.py

No external packages required — uses Python stdlib only.
"""

import curses

from cargame.game import Game
from cargame.screens import setup_colors, size_ok, splash


def main(stdscr) -> None:
    setup_colors()
    curses.curs_set(0)

    if not size_ok(stdscr):
        return
    if not splash(stdscr):
        return

    game = Game(stdscr)
    while game.play():
        pass


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\nThanks for playing Car Dodge!  Drive safe. 🚗")
