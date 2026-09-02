"""FB engine--LL.bas init_splash: Lynn Productions card before the title map."""

from __future__ import annotations

import time

import pygame

from lynn.constants import SCREEN_H, SCREEN_W
from lynn.paths import data_file

SPLASH_PATH = "pictures/splash_screen.bmp"
SPLASH_HOLD = 3.5
SPLASH_LEAD_IN = 1.0
SPLASH_LEAD_OUT = 0.3
SPLASH_FADE_TIME = 0.01
SPLASH_FADE_STEPS = 64


def load_splash_image() -> pygame.Surface:
    """Load data/pictures/splash_screen.bmp (FB Bload)."""
    path = data_file(*SPLASH_PATH.split("/"))
    if not path.is_file():
        raise FileNotFoundError(path)
    return pygame.image.load(str(path))


def _pump_quit() -> bool:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
    return False


def _hold(seconds: float, canvas: pygame.Surface, present, frame_clock, splash=None, overlay=None) -> bool:
    deadline = time.perf_counter() + max(0.0, seconds)
    while time.perf_counter() < deadline:
        if _pump_quit():
            return False
        if splash is not None:
            canvas.blit(splash, (0, 0))
            if overlay is not None:
                canvas.blit(overlay, (0, 0))
        else:
            canvas.fill((0, 0, 0))
        present()
        frame_clock.tick(60)
    return True


def _fade(canvas, splash, present, frame_clock, incoming: bool) -> bool:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H))
    overlay.fill((0, 0, 0))
    step_deadline = time.perf_counter()
    for i in range(SPLASH_FADE_STEPS):
        if incoming:
            alpha = int(255 * (1.0 - (i + 1) / SPLASH_FADE_STEPS))
        else:
            alpha = int(255 * ((i + 1) / SPLASH_FADE_STEPS))
        overlay.set_alpha(max(0, min(255, alpha)))
        canvas.blit(splash, (0, 0))
        canvas.blit(overlay, (0, 0))
        present()
        if _pump_quit():
            return False
        step_deadline += SPLASH_FADE_TIME
        while time.perf_counter() < step_deadline:
            if _pump_quit():
                return False
            frame_clock.tick(60)
    return True


def init_splash(canvas: pygame.Surface, present, frame_clock, min_hold: float = SPLASH_HOLD) -> bool:
    """FB init_splash. Fade the splash card, hold 3.5s from start, fade out. False on window close."""
    start = time.perf_counter()
    if not _hold(SPLASH_LEAD_IN, canvas, present, frame_clock):
        return False
    try:
        splash = load_splash_image().convert()
    except (pygame.error, FileNotFoundError):
        return True
    if splash.get_size() != (SCREEN_W, SCREEN_H):
        splash = pygame.transform.scale(splash, (SCREEN_W, SCREEN_H)).convert()
    if not _fade(canvas, splash, present, frame_clock, incoming=True):
        return False
    remaining = min_hold - (time.perf_counter() - start)
    if remaining > 0:
        if not _hold(remaining, canvas, present, frame_clock, splash=splash):
            return False
    if not _fade(canvas, splash, present, frame_clock, incoming=False):
        return False
    if not _hold(SPLASH_LEAD_OUT, canvas, present, frame_clock):
        return False
    canvas.fill((0, 0, 0))
    present()
    return True
