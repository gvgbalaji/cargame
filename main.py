#!/usr/bin/env python3
"""
CAR DODGE — Pygame Car Dodging Game
Dodge oncoming cars for as long as you can!

Usage:
    python main.py
"""

import pygame

from cargame.constants import WIDTH, HEIGHT, TITLE
from cargame.game import Game
from cargame.screens import splash, customization_screen
from cargame.sound import init_mixer, set_sound_config


def main():
    pygame.init()
    init_mixer()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)

    if not splash(screen):
        pygame.quit()
        return

    skin_index, sound_theme = customization_screen(screen)
    game = Game(screen, skin_index, sound_theme)

    while True:
        result = game.play()
        if result == "quit":
            break
        if result == "customize":
            skin_index, sound_theme = customization_screen(screen)
            game.set_skin(skin_index)
            set_sound_config(enabled=(sound_theme != "silent"),
                             theme=sound_theme)

    pygame.quit()
    print("\nThanks for playing Car Dodge!  Drive safe.")


if __name__ == "__main__":
    main()
