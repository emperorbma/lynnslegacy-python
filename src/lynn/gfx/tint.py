"""Palette effects from FB gfx_palette: color_off blacks the frame, red_tint drops R and G by 64."""

from __future__ import annotations

import pygame

COLOR_NORMAL = 0
COLOR_OFF = 1
COLOR_RED = 2


def apply_color_mode(canvas: pygame.Surface, mode: int) -> None:
    """Leftover hook. color_off / red_tint now write the palette itself."""
    if mode == COLOR_OFF:
        canvas.fill((0, 0, 0))
    elif mode == COLOR_RED:
        canvas.fill((64, 64, 0), special_flags=pygame.BLEND_RGB_SUB)
