"""Draw car shapes as Pygame surfaces with polygon art."""

import pygame
from .constants import CAR_W, CAR_H


def _draw_car_body(surf: pygame.Surface, color: tuple, is_player: bool = False):
    """Draw a detailed top-down car onto the given surface."""
    w, h = surf.get_size()
    r, g, b = color[:3]

    # Darker shade for shadow areas
    dark = (max(0, r - 60), max(0, g - 60), max(0, b - 60))
    light = (min(255, r + 40), min(255, g + 40), min(255, b + 40))
    glass = (80, 180, 220, 200)

    # Main body (rounded rectangle)
    body_rect = pygame.Rect(6, 12, w - 12, h - 24)
    pygame.draw.rect(surf, color, body_rect, border_radius=8)

    # Body highlights
    highlight_rect = pygame.Rect(10, 16, w - 20, h // 3)
    pygame.draw.rect(surf, light, highlight_rect, border_radius=5)

    # Windshield (front for player = bottom, for enemy = top)
    if is_player:
        # Rear window (top)
        pygame.draw.rect(surf, glass, (14, 16, w - 28, 18), border_radius=4)
        # Front windshield (bottom part)
        pygame.draw.rect(surf, glass, (12, h - 42, w - 24, 22), border_radius=4)
    else:
        # Front windshield (top for enemy - they face us)
        pygame.draw.rect(surf, glass, (12, 16, w - 24, 22), border_radius=4)
        # Rear window
        pygame.draw.rect(surf, glass, (14, h - 34, w - 28, 18), border_radius=4)

    # Side mirrors
    pygame.draw.rect(surf, dark, (1, h // 3, 6, 10), border_radius=2)
    pygame.draw.rect(surf, dark, (w - 7, h // 3, 6, 10), border_radius=2)

    # Wheels (4 dark rectangles at corners)
    wheel_color = (30, 30, 35)
    wheel_w, wheel_h = 8, 20
    # Front-left, front-right
    pygame.draw.rect(surf, wheel_color, (2, h - 30, wheel_w, wheel_h), border_radius=3)
    pygame.draw.rect(surf, wheel_color, (w - wheel_w - 2, h - 30, wheel_w, wheel_h), border_radius=3)
    # Rear-left, rear-right
    pygame.draw.rect(surf, wheel_color, (2, 12, wheel_w, wheel_h), border_radius=3)
    pygame.draw.rect(surf, wheel_color, (w - wheel_w - 2, 12, wheel_w, wheel_h), border_radius=3)

    if is_player:
        # Tail lights (red at the top since we see the back)
        pygame.draw.rect(surf, (255, 40, 40), (10, 8, 12, 6), border_radius=2)
        pygame.draw.rect(surf, (255, 40, 40), (w - 22, 8, 12, 6), border_radius=2)
        # Headlights at bottom
        pygame.draw.rect(surf, (255, 255, 200), (10, h - 16, 12, 6), border_radius=2)
        pygame.draw.rect(surf, (255, 255, 200), (w - 22, h - 16, 12, 6), border_radius=2)
    else:
        # Headlights (top for enemy)
        pygame.draw.rect(surf, (255, 255, 200), (10, 6, 12, 6), border_radius=2)
        pygame.draw.rect(surf, (255, 255, 200), (w - 22, 6, 12, 6), border_radius=2)
        # Tail lights (bottom for enemy)
        pygame.draw.rect(surf, (255, 40, 40), (10, h - 14, 12, 6), border_radius=2)
        pygame.draw.rect(surf, (255, 40, 40), (w - 22, h - 14, 12, 6), border_radius=2)

    # Center stripe / racing detail
    if is_player:
        stripe_color = (min(255, r + 80), min(255, g + 80), min(255, b + 80))
        pygame.draw.line(surf, stripe_color, (w // 2, 38), (w // 2, h - 44), 2)


def make_car_surface(color: tuple, is_player: bool = False) -> pygame.Surface:
    """Create and return a car surface with transparency."""
    surf = pygame.Surface((CAR_W, CAR_H), pygame.SRCALPHA)
    _draw_car_body(surf, color, is_player)
    return surf
