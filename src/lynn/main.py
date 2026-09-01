"""Window loop. `python -m lynn [objects|map|palette|test]`."""

from __future__ import annotations

import sys
import time

import pygame

from lynn import clock as ll_clock
from lynn.constants import SCREEN_H, SCREEN_W, TRUE
from lynn.demos import (
    MODES,
    draw_map_demo,
    draw_palette_demo,
    load_map_demo,
    load_palette_demo,
    tick_map_demo,
)
from lynn.gfx.menu import handleKeybSelected, keyboardSelected, menu_Blit
from lynn.object.combat import (
    LLObject_MAINAttack,
    LLObject_MAINDamage,
    hero_attack,
    hero_death_tick,
    hero_hurt_tick,
    start_hero_attack,
)
from lynn.object.combat_funcs import __flashy
import lynn.events as events
from lynn.object.tick import LLObject_CheckSpawn
from lynn.sequence import play_sequence, try_action_sequence
from lynn.hero import (
    DIR_DOWN,
    DIR_LEFT,
    DIR_RIGHT,
    DIR_UP,
    hero_walk_step,
    try_same_map_room_teleport,
    update_cam,
)
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
    from lynn.audio import init_mixer, init_snd

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    init_mixer()
    init_snd()
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
        f"  objects [map]  walk Lynn (default map: {DEFAULT_MAP})\n"
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
        menu_up = menu_right = menu_down = menu_left = 0
        menu_confirm = False
        action_pulse = 0
        events.keys.enter_pulse = 0
        seq_busy = demo.seq is not None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save_open = demo.hero is not None and demo.hero.menu_sel != 0
                    if save_open:
                        pass
                    elif with_objects and demo.hero is not None and demo.menu is not None and not seq_busy:
                        if demo.menu_open != 0:
                            demo.menu_open = 0
                            demo.menu_backdrop = None
                        else:
                            demo.menu_open = TRUE
                            demo.menu.selectedItem = 18
                            demo.menu_backdrop = None
                    elif not with_objects:
                        running = False
                elif event.key == pygame.K_F11 or (
                    event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
                ):
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_F12:
                    scale_option = (scale_option + 1) % 7
                elif demo.menu_open != 0:
                    if event.key == pygame.K_UP:
                        menu_up = TRUE
                    elif event.key == pygame.K_RIGHT:
                        menu_right = TRUE
                    elif event.key == pygame.K_DOWN:
                        menu_down = TRUE
                    elif event.key == pygame.K_LEFT:
                        menu_left = TRUE
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and not (
                        event.mod & pygame.KMOD_ALT
                    ):
                        menu_confirm = True
                        events.keys.enter_pulse = TRUE
                elif event.key == pygame.K_RETURN and not (event.mod & pygame.KMOD_ALT):
                    events.keys.enter_pulse = TRUE
                elif event.key == pygame.K_SPACE:
                    action_pulse = TRUE
                elif event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    if demo.hero is not None and demo.hero_only is not None:
                        start_hero_attack(demo.hero)
                elif event.key in (pygame.K_LEFTBRACKET, pygame.K_PAGEUP):
                    room_i = (room_i - 1) % demo.game_map.rooms
                    cam_x, cam_y = _cam_for_room(demo.game_map, room_i)
                elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_PAGEDOWN):
                    room_i = (room_i + 1) % demo.game_map.rooms
                    cam_x, cam_y = _cam_for_room(demo.game_map, room_i)
        if demo.hero_only is not None:
            demo.hero_only.action = action_pulse
        if demo.menu_open != 0 and demo.menu is not None and demo.hero_only is not None:
            keyboardSelected(demo.menu, menu_up, menu_right, menu_down, menu_left)
            if menu_confirm and handleKeybSelected(demo.menu, demo.hero_only) != 0:
                demo.menu_open = 0
                demo.menu_backdrop = None
        room = demo.game_map.room[room_i]
        keys = pygame.key.get_pressed()
        events.keys.up = TRUE if keys[pygame.K_UP] else 0
        events.keys.down = TRUE if keys[pygame.K_DOWN] else 0
        events.keys.left = TRUE if keys[pygame.K_LEFT] else 0
        events.keys.right = TRUE if keys[pygame.K_RIGHT] else 0
        events.keys.enter = TRUE if keys[pygame.K_RETURN] else 0
        events.keys.escape = TRUE if keys[pygame.K_ESCAPE] else 0
        others = demo.objects_by_room[room_i] if room_i < len(demo.objects_by_room) else []
        locked = (
            (demo.hero_only is not None and demo.hero_only.action_lock != 0)
            or (demo.hero is not None and demo.hero.menu_sel != 0)
            or (demo.hero is not None and demo.hero.dead != 0)
        )
        if (
            demo.seq is None
            and demo.menu_open == 0
            and not locked
            and demo.hero is not None
            and demo.hero_only is not None
        ):
            started = try_action_sequence(demo.hero, demo.hero_only, others)
            if started is not None:
                demo.seq = started
                demo.do_hud = 0
                events.do_hud = 0
        attacking = demo.hero_only is not None and demo.hero_only.attacking != 0
        if demo.menu_open == 0 and demo.seq is None and not attacking and not locked:
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
                hero_walk_step(demo.hero, room, keys_dir, others)
                demo.hero_room = try_same_map_room_teleport(
                    demo.hero, demo.game_map, demo.hero_room
                )
                room_i = demo.hero_room
                room = demo.game_map.room[room_i]
                cam_x, cam_y = update_cam(demo.hero, room)
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
        others = demo.objects_by_room[room_i] if room_i < len(demo.objects_by_room) else []
        shown = _map_caption(
            demo.game_map.filename, room_i, demo.game_map.rooms, cam_x, cam_y, shown,
            demo.objects_by_room[room_i] if room_i < len(demo.objects_by_room) else (),
            demo.hero,
        )
        ll_clock.timer = time.perf_counter()
        if (
            demo.hero is not None
            and demo.hero_only is not None
            and demo.hero_only.attacking != 0
            and demo.seq is None
            and demo.menu_open == 0
        ):
            hero_attack(demo.hero)
            LLObject_MAINAttack(others, demo.hero)
        if (
            demo.hero is not None
            and demo.seq is None
            and demo.menu_open == 0
        ):
            if demo.hero.dead == 0:
                LLObject_MAINDamage(demo.hero, others)
                if demo.hero.dmg_id != 0:
                    __flashy(demo.hero)
                if demo.hero.hurt:
                    hero_hurt_tick(demo.hero)
            else:
                if demo.hero_only is not None:
                    demo.hero_only.attacking = 0
                hero_death_tick(demo.hero)
        if demo.seq is not None and demo.hero_only is not None:
            demo.seq = play_sequence(
                demo.seq, demo.box, demo.hero_only, demo.palette, demo.menu
            )
            if demo.seq is None:
                demo.do_hud = TRUE
                events.do_hud = TRUE
            for obj in others:
                LLObject_CheckSpawn(obj)
        if demo.menu_open == 0:
            if demo.seq is None:
                tick_map_demo(demo, room_i)
            draw_map_demo(canvas, demo, room_i, cam_x, cam_y)
            demo.menu_backdrop = None
        else:
            if demo.menu_backdrop is None:
                draw_map_demo(canvas, demo, room_i, cam_x, cam_y)
                demo.menu_backdrop = canvas.copy()
            canvas.blit(demo.menu_backdrop, (0, 0))
            if demo.menu is not None and demo.hero_only is not None:
                menu_Blit(canvas, demo.menu, demo.hero_only)
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
