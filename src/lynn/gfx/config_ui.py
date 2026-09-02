"""FB src/config/config.bas key setup. Invoked as `python -m lynn config`."""

from __future__ import annotations

import pygame

from lynn.constants import SCREEN_H, SCREEN_W, TRUE
from lynn.controls import (
    SC_ESCAPE,
    check_all_codes,
    load_controls,
    load_fullscreen,
    save_controls,
    save_fullscreen,
    scancode_from_pygame,
    scancode_name,
)
from lynn.gfx.image import LLSystem_ImageLoad, frame_surfaces
from lynn.gfx.palette import load_pal

_DIR = "data/pictures/char/lynn24.spr"
_ATK = "data/pictures/char/lynnattack_new.spr"
_POWDER = "data/pictures/char/lynn_flare.spr"
_SPEAK = "data/pictures/char/lynn_cfg.spr"

# (attr, x, y, sprite, frame_index, box_w, box_h)
_SLOTS = (
    ("ukey", 48, 0, "dir", 0, 48, 48),
    ("rkey", 96, 48, "dir", 8 + 1, 48, 48),
    ("dkey", 48, 96, "dir", 16 + 2, 48, 48),
    ("lkey", 0, 48, "dir", 24 + 3, 48, 48),
    ("itmkey", 180, 35, "powder", 15 + 3, 48, 48),
    ("atkkey", 180, 120, "attack", 6 + 3, 48, 48),
    ("actkey", 260, 120, "speak", 0, 48, 48),
)

# FB Draw String / GfxPrint use the runtime font, not llfont and not a BIOS ROM.
# pygame.font.SysFont is the OS face; Lucida Console is 8px-tall and monospace.
_FONT8 = None
_FONT16 = None
_COL15 = (252, 252, 252)
_COL114 = (48, 101, 92)


def _os_font(px: int) -> pygame.font.Font:
    pygame.font.init()
    available = set(pygame.font.get_fonts())
    for name in ("lucidaconsole", "consolas", "couriernew", "monospace"):
        if name in available:
            return pygame.font.SysFont(name, px)
    return pygame.font.Font(None, px)


def _ensure_fonts() -> None:
    global _FONT8, _FONT16
    if _FONT8 is not None:
        return
    _FONT8 = _os_font(8)
    _FONT16 = _os_font(14)


def _load_sprites(palette):
    def _frames(path: str) -> list:
        return frame_surfaces(LLSystem_ImageLoad(path), palette)

    return {
        "dir": _frames(_DIR),
        "attack": _frames(_ATK),
        "powder": _frames(_POWDER),
        "speak": _frames(_SPEAK),
    }


def _blit_frame(canvas, frames: list, index: int, x: int, y: int, x_off: int = 0, y_off: int = 0) -> None:
    if not frames:
        return
    i = index if 0 <= index < len(frames) else 0
    canvas.blit(frames[i], (x - x_off, y - y_off))


def draw_string(canvas, text: str, x: int, y: int, color: tuple[int, int, int] = _COL15) -> None:
    """FB Draw String: OS font via pygame, 8px cell."""
    _ensure_fonts()
    canvas.blit(_FONT8.render(text, False, color), (x, y))


def gfxprint(canvas, text: str, x: int, y: int, color: tuple[int, int, int]) -> None:
    """FB GfxPrint: OS font via pygame, 16px Full/Windowed box."""
    _ensure_fonts()
    canvas.blit(_FONT16.render(text, False, color), (x, y))


def canvas_mouse(scale_option: int) -> tuple[int, int, int]:
    """Window pixel -> 320x200, plus left-button flag."""
    window = pygame.display.get_surface()
    if window is None:
        return 0, 0, 0
    win_w, win_h = window.get_size()
    if scale_option == 0:
        scale = min(win_w / SCREEN_W, win_h / SCREEN_H)
    else:
        scale = float(scale_option)
        scale = min(scale, win_w / SCREEN_W, win_h / SCREEN_H)
        if scale < 1:
            scale = min(win_w / SCREEN_W, win_h / SCREEN_H)
    dest_w = max(1, int(SCREEN_W * scale))
    dest_h = max(1, int(SCREEN_H * scale))
    ox = (win_w - dest_w) // 2
    oy = (win_h - dest_h) // 2
    mx, my = pygame.mouse.get_pos()
    if dest_w <= 0 or dest_h <= 0:
        return 0, 0, 0
    cx = (mx - ox) * SCREEN_W // dest_w
    cy = (my - oy) * SCREEN_H // dest_h
    pressed = pygame.mouse.get_pressed()
    mb = 1 if pressed[0] else 0
    return cx, cy, mb


def _hit(mx: int, my: int, x: int, y: int, w: int, h: int) -> bool:
    return mx > x and my > y and mx < x + w and my < y + h


def _wait_scancode() -> int:
    """FB key_get: next keyboard scancode, or 0."""
    pygame.event.clear()
    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            return -1
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return SC_ESCAPE
            code = scancode_from_pygame(event.key)
            if code != 0:
                return code


def run_config(canvas, present, frame_clock, scale_option: int = 0) -> int:
    """FB config.bas main loop. Esc saves; Backspace / window close discards."""
    palette = load_pal("data/palette/ll.pal")
    spr = _load_sprites(palette)
    col15 = palette.colors[15] if len(palette.colors) > 15 else _COL15
    col114 = palette.colors[114] if len(palette.colors) > 114 else _COL114
    bound = load_controls()
    fullscreen = load_fullscreen()
    waiting = False
    wait_attr = ""
    pygame.mouse.set_visible(True)
    running = True
    save_on_exit = False
    click_armed = TRUE

    while running:
        mx, my, mb = canvas_mouse(scale_option)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                save_on_exit = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    save_on_exit = True
                elif event.key == pygame.K_BACKSPACE:
                    running = False
                    save_on_exit = False
                elif event.key == pygame.K_F11 or (
                    event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
                ):
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_F12:
                    scale_option = (scale_option + 1) % 7
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                click_armed = TRUE
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and click_armed:
                click_armed = 0
                if waiting:
                    continue
                if _hit(mx, my, 240, 10, 32, 16):
                    fullscreen = TRUE
                elif _hit(mx, my, 240, 30, 64, 16):
                    fullscreen = 0
                else:
                    for attr, x, y, _kind, _fi, w, h in _SLOTS:
                        if _hit(mx, my, x, y, w, h):
                            waiting = True
                            wait_attr = attr
                            break

        if waiting:
            code = _wait_scancode()
            waiting = False
            if code == -1:
                running = False
                save_on_exit = False
            elif check_all_codes(code, bound) != 0:
                setattr(bound, wait_attr, code)
            wait_attr = ""
            click_armed = TRUE
            continue

        canvas.fill((0, 0, 0))
        draw_string(canvas, "Lynn's Legacy", 106, 8, col15)
        draw_string(canvas, "Key Setup", 122, 16, col15)
        offs = {
            "dir": (0, 8),
            "attack": (16, 20),
            "powder": (16, 20),
            "speak": (8, 16),
        }
        for attr, x, y, kind, fi, w, h in _SLOTS:
            xo, yo = offs[kind]
            _blit_frame(canvas, spr[kind], fi, x + 16, y + 16, xo, yo)
            label = scancode_name(getattr(bound, attr))
            lx = x + 24 - ((len(label) >> 1) << 3)
            if len(label) & 1:
                lx -= 4
            draw_string(canvas, label, lx, y + 38, col15)
            if _hit(mx, my, x, y, w, h):
                pygame.draw.rect(canvas, col15, (x, y, w, h), 1)

        # gfxprint color is the selected state; Line box is hover only.
        gfxprint(canvas, "Full", 240, 10, col114 if fullscreen != 0 else col15)
        gfxprint(canvas, "Windowed", 240, 30, col15 if fullscreen != 0 else col114)
        if _hit(mx, my, 240, 10, 32, 16):
            pygame.draw.rect(canvas, col15, (240, 10, 32, 16), 1)
        if _hit(mx, my, 240, 30, 64, 16):
            pygame.draw.rect(canvas, col15, (240, 30, 64, 16), 1)

        draw_string(canvas, "Click an action,", 8, 164, col15)
        draw_string(canvas, "then hit a button for that action.", 8, 172, col15)
        draw_string(canvas, "Esc to exit saving changes.", 8, 184, col15)
        draw_string(canvas, "Backspace to exit discarding changes..", 8, 192, col15)
        present()
        frame_clock.tick(60)

    if save_on_exit:
        save_controls(bound)
        save_fullscreen(fullscreen)
    pygame.mouse.set_visible(False)
    return 0
