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
from cargame.screens import customization_screen, setup_colors, size_ok, splash
from cargame.sound import set_sound_config


def main(stdscr) -> None:
    setup_colors()
    curses.curs_set(0)

    if not size_ok(stdscr):
        return
    if not splash(stdscr):
        return

    skin_index, sound_theme = customization_screen(stdscr)
    game = Game(stdscr, skin_index, sound_theme)

    while True:
        result = game.play()
        if result == "quit":
            break
        if result == "customize":
            skin_index, sound_theme = customization_screen(stdscr)
            game.set_skin(skin_index)
            set_sound_config(enabled=(sound_theme != "silent"), theme=sound_theme)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\nThanks for playing Car Dodge!  Drive safe. 🚗")
