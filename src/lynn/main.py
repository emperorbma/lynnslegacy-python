"""Window loop. `python -m lynn [objects|map|palette|test]`."""

from __future__ import annotations

import sys
import time

import pygame

from lynn import clock as ll_clock
from lynn.constants import SCREEN_H, SCREEN_W
from lynn.demos import (
    MODES,
    draw_map_demo,
    draw_palette_demo,
    load_map_demo,
    load_palette_demo,
    tick_map_demo,
)
from lynn.hero import DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP, hero_walk_step, update_cam
from lynn.paths import DEFAULT_MAP, chdir_project_root

PAN_SPEED = 4


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    mode, map_spec, rest = parse_cli(args)
    if mode in ("-h", "--help", "help", "/?"):
        print(_usage())
        return 0
    if mode in ("test", "--test", "-t"):
        return _run_tests(rest)
    if mode not in MODES:
        print(f"unknown mode {mode!r}\n{_usage()}", file=sys.stderr)
        return 2

    chdir_project_root()
    pygame.init()
    pygame.mouse.set_visible(False)
    pygame.display.set_caption(_caption_for(mode, map_spec))
    _open_window()
    frame_clock = pygame.time.Clock()
    canvas = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    scale_option = 0

    if mode == "palette":
        code = _run_palette(canvas, frame_clock, scale_option)
    else:
        code = _run_map(
            canvas, frame_clock, scale_option,
            with_objects=(mode == "objects"),
            map_path=map_spec,
        )
    pygame.quit()
    return code


def parse_cli(argv: list[str]) -> tuple[str, str | None, list[str]]:
    if not argv:
        return "objects", None, []
    mode = argv[0].lower()
    rest = argv[1:]
    if mode in ("test", "--test", "-t"):
        return "test", None, rest
    if mode in ("map", "objects") and rest:
        return mode, rest[0], rest[1:]
    return mode, None, rest


def _usage() -> str:
    return (
        "Usage: python -m lynn [objects|map|palette|test] [map]\n"
        f"  objects [map]  idle XML entities (default map: {DEFAULT_MAP})\n"
        "  map [map]      tiles only\n"
        "  palette        256-color ramp + lynn24.spr\n"
        "  test           pytest (extra args forwarded, including --map)\n"
        "  help           this text\n"
        "Map may be a stem (valley), file (valley.map), or path."
    )


def _run_tests(pytest_args: list[str]) -> int:
    chdir_project_root()
    import pytest

    return int(pytest.main(["-q", *pytest_args]))


def _caption_for(mode: str, map_spec: str | None = None) -> str:
    if mode == "palette":
        return "Lynn's Legacy - palette / lynn24.spr"
    label = map_spec or DEFAULT_MAP
    if mode == "map":
        return f"Lynn's Legacy - {label} (tiles only)"
    return f"Lynn's Legacy - {label}"


def _run_palette(canvas, frame_clock, scale_option: int) -> int:
    palette, sprite_surfs = load_palette_demo()
    start = pygame.time.get_ticks()
    running = True
    while running:
        scale_option, running = _common_events(scale_option, running)
        elapsed = (pygame.time.get_ticks() - start) / 1000.0
        draw_palette_demo(canvas, palette, sprite_surfs, elapsed)
        _present(canvas, scale_option)
        frame_clock.tick(60)
    return 0


def _run_map(canvas, frame_clock, scale_option: int, with_objects: bool, map_path: str | None = None) -> int:
    demo = load_map_demo(with_objects=with_objects, map_path=map_path)
    room_i = demo.hero_room if demo.hero is not None else 0
    if demo.hero is not None:
        cam_x, cam_y = update_cam(demo.hero, demo.game_map.room[room_i])
    else:
        cam_x, cam_y = _cam_for_room(demo.game_map, room_i)
    shown = None
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F11 or (
                    event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
                ):
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_F12:
                    scale_option = (scale_option + 1) % 7
                elif event.key in (pygame.K_LEFTBRACKET, pygame.K_PAGEUP):
                    room_i = (room_i - 1) % demo.game_map.rooms
                    cam_x, cam_y = _cam_for_room(demo.game_map, room_i)
                elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_PAGEDOWN):
                    room_i = (room_i + 1) % demo.game_map.rooms
                    cam_x, cam_y = _cam_for_room(demo.game_map, room_i)
        room = demo.game_map.room[room_i]
        keys = pygame.key.get_pressed()
        if demo.hero is not None:
            keys_dir = None
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                keys_dir = DIR_LEFT
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                keys_dir = DIR_RIGHT
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                keys_dir = DIR_DOWN
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                keys_dir = DIR_UP
            others = demo.objects_by_room[room_i] if room_i < len(demo.objects_by_room) else []
            hero_walk_step(demo.hero, room, keys_dir, others)
            cam_x, cam_y = update_cam(demo.hero, room)
            room_i = demo.hero_room
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                cam_x -= PAN_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                cam_x += PAN_SPEED
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                cam_y -= PAN_SPEED
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                cam_y += PAN_SPEED
            cam_x, cam_y = _clamp_cam(room, cam_x, cam_y)
        shown = _map_caption(
            demo.game_map.filename, room_i, demo.game_map.rooms, cam_x, cam_y, shown,
            demo.objects_by_room[room_i] if room_i < len(demo.objects_by_room) else (),
            demo.hero,
        )
        ll_clock.timer = time.perf_counter()
        tick_map_demo(demo, room_i)
        draw_map_demo(canvas, demo, room_i, cam_x, cam_y)
        _present(canvas, scale_option)
        frame_clock.tick(60)
    return 0


def _common_events(scale_option: int, running: bool) -> tuple[int, bool]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_F11 or (
                event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
            ):
                pygame.display.toggle_fullscreen()
            elif event.key == pygame.K_F12:
                scale_option = (scale_option + 1) % 7
    return scale_option, running


def _map_caption(filename, room_i, rooms, cam_x, cam_y, previous, objs=(), hero=None):
    from pathlib import Path

    bits = [f"{Path(o.id).stem}:{o.frame}" for o in objs]
    extra = ("  " + " ".join(bits)) if bits else ""
    if hero is not None:
        extra = f"  lynn {int(hero.coords_x)},{int(hero.coords_y)} d{hero.direction}" + extra
    text = (
        f"Lynn's Legacy - {filename}  room {room_i}/{rooms - 1}  "
        f"cam {cam_x},{cam_y}{extra}"
    )
    if text != previous:
        pygame.display.set_caption(text)
    return text


def _cam_for_room(game_map, room_i: int) -> tuple[int, int]:
    room = game_map.room[room_i]
    for entry in game_map.entry:
        if entry.room == room_i:
            return _clamp_cam(room, entry.x - SCREEN_W // 2, entry.y - SCREEN_H // 2)
    return 0, 0


def _clamp_cam(room, cam_x: int, cam_y: int) -> tuple[int, int]:
    max_x = max(0, room.x * 16 - SCREEN_W)
    max_y = max(0, room.y * 16 - SCREEN_H)
    return max(0, min(cam_x, max_x)), max(0, min(cam_y, max_y))


def _open_window() -> pygame.Surface:
    return pygame.display.set_mode(
        (SCREEN_W * 2, SCREEN_H * 2),
        pygame.RESIZABLE,
        vsync=1,
    )


def _present(canvas: pygame.Surface, scale_option: int) -> None:
    window = pygame.display.get_surface()
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
    x = (win_w - dest_w) // 2
    y = (win_h - dest_h) // 2
    scaled = pygame.transform.scale(canvas.convert(), (dest_w, dest_h))
    window.fill((0, 0, 0))
    window.blit(scaled, (x, y))
    pygame.display.flip()


if __name__ == "__main__":
    sys.exit(main())
