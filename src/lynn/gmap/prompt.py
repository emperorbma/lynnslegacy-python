"""Blocking on-screen prompts for gmap (FB Locate/Input stand-in)."""

from __future__ import annotations

import pygame

GMAP_W = 800
GMAP_H = 600


def prompt_text(
    title: str,
    initial: str = "",
    *,
    numeric: bool = False,
    allow_empty: bool = True,
) -> str | None:
    """Modal text entry. Enter accepts, Esc cancels. Returns None on cancel."""
    font = pygame.font.SysFont("consolas", 16)
    clock = pygame.time.Clock()
    text = str(initial)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_RETURN:
                    if text == "" and not allow_empty:
                        continue
                    if numeric:
                        try:
                            float(text) if "." in text else int(text)
                        except ValueError:
                            continue
                    return text
                if event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if numeric and event.unicode not in "0123456789.-":
                        continue
                    text += event.unicode

        win = pygame.display.get_surface()
        if win is None:
            return None
        overlay = pygame.Surface((GMAP_W, GMAP_H))
        overlay.fill((8, 8, 14))
        overlay.blit(font.render(title, True, (240, 240, 245)), (40, 200))
        overlay.blit(font.render(text + "_", True, (255, 220, 120)), (40, 240))
        overlay.blit(
            font.render("Enter confirm · Esc cancel", True, (160, 160, 180)),
            (40, 280),
        )
        # Scale into window.
        scaled = pygame.transform.smoothscale(overlay, win.get_size())
        win.fill((0, 0, 0))
        win.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(30)


def prompt_int(title: str, initial: int = 0, minimum: int | None = None, maximum: int | None = None) -> int | None:
    raw = prompt_text(title, str(initial), numeric=True, allow_empty=False)
    if raw is None:
        return None
    try:
        value = int(float(raw))
    except ValueError:
        return None
    if minimum is not None and value < minimum:
        value = minimum
    if maximum is not None and value > maximum:
        value = maximum
    return value
