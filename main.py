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

    skin_index, sound_theme, curvy = customization_screen(screen)
    game = Game(screen, skin_index, sound_theme, curvy=curvy)
    best_score = 0

    while True:
        result = game.play()
        best_score = max(best_score, game.best_score)
        if result == "quit":
            break
        if result == "customize":
            skin_index, sound_theme, curvy = customization_screen(screen)
            game = Game(screen, skin_index, sound_theme, curvy=curvy)
            game.best_score = best_score

    pygame.quit()
    print("\nThanks for playing Car Dodge!  Drive safe.")


if __name__ == "__main__":
    main()
