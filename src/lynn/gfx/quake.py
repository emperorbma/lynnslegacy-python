"""FB gfx_LL.bas screenQuake: jitter the whole frame by quakeViolence pixels."""

from __future__ import annotations

import random

import pygame


def screen_quake(canvas: pygame.Surface, violence: int) -> None:
    if violence == 0:
        return
    dx = int(violence * (random.random() * 3 - 1))
    dy = int(violence * (random.random() * 3 - 1))
    if dx == 0 and dy == 0:
        return
    shot = canvas.copy()
    canvas.fill((0, 0, 0))
    canvas.blit(shot, (dx, dy))
