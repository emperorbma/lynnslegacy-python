"""Preserved proof-of-concept scenes. Select with `python -m lynn <mode>`."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pygame

from lynn.constants import (
    SCREEN_H,
    SCREEN_W,
    TRUE,
    u_bluechest,
    u_bluechestitem,
    u_button,
    u_chest,
    u_gbutton,
    u_ghut,
    u_savepoint,
)
from lynn.gfx.blit import blit_object, blit_room_tiles
from lynn.gfx.hud import blit_hud, load_hud
from lynn.gfx.loot import blit_enemy_loot, load_drop_surfs
from lynn.gfx.menu import load_menu
from lynn.gfx.image import LLSystem_ImageLoad, frame_surface, frame_surfaces
from lynn.gfx.palette import LLPalette, load_pal
import lynn.object  # registers __idle_animate / __return_idle / __reset_frame
import lynn.object.move_ai  # noqa: F401  — after collision is loaded (no circular import)
from lynn.events import bind_hero, bind_hero_only, reset_events
import lynn.events as events
from lynn.gfx.box import BoxControl, blit_box
from lynn.hero import ctor_hero, ctor_hero_only, place_hero
from lynn.map.collision import check_teleports
from lynn.map.loader import load_mapV
from lynn.map.types import MapType
from lynn.object.tick import LLObject_CheckSpawn, tick_objects
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import DEFAULT_MAP, resolve_map_path

POC_MAP = f"data/map/{DEFAULT_MAP}"
PALETTE_CELLS = (16, 16)
PALETTE_CELL = (20, 8)
LYNN_SPR = "data/pictures/char/lynn24.spr"

MODES = ("objects", "map", "palette")


def draw_palette_demo(
    canvas: pygame.Surface,
    palette: LLPalette,
    sprite_surfs: list[pygame.Surface],
    elapsed: float = 0.0,
) -> None:
    canvas.fill((0, 0, 0))
    cell_w, cell_h = PALETTE_CELL
    cols, _rows = PALETTE_CELLS
    for i, rgb in enumerate(palette.colors):
        cx = (i % cols) * cell_w
        cy = (i // cols) * cell_h
        canvas.fill(rgb, pygame.Rect(cx, cy, cell_w, cell_h))
    if sprite_surfs:
        frame = int(elapsed / 0.08) % len(sprite_surfs)
        canvas.blit(sprite_surfs[frame], (32, 140))
        if len(sprite_surfs) > 1:
            canvas.blit(sprite_surfs[0], (80, 140))


@dataclass
class MapDemo:
    palette: LLPalette
    game_map: MapType
    tile_surfs: list
    objects_by_room: list = field(default_factory=list)
    obj_anim_surfs: dict = field(default_factory=dict)
    para_cache: dict = field(default_factory=dict)
    hero: object | None = None
    hero_surfs: list = field(default_factory=list)
    hero_room: int = 0
    hero_only: object | None = None
    hud: object | None = None
    do_hud: int = 0
    menu: object | None = None
    menu_open: int = 0
    menu_backdrop: object | None = None
    seq: object | None = None
    box: object | None = None
    drop_surfs: list = field(default_factory=list)
    load_images: int = TRUE
    load_tileset: int = TRUE


def load_map_demo(with_objects: bool = True, map_path: str | None = None) -> MapDemo:
    palette = load_pal("data/palette/ll.pal")
    path = resolve_map_path(map_path)
    game_map = load_mapV(str(path), load_tileset=True)
    if game_map.tileset is None or game_map.rooms == 0:
        raise FileNotFoundError(path)
    demo = MapDemo(
        palette=palette,
        game_map=game_map,
        tile_surfs=frame_surfaces(game_map.tileset, palette),
    )
    demo.load_images = TRUE if with_objects else 0
    if not with_objects:
        demo.objects_by_room = [[] for _ in game_map.room]
        return demo
    reset_events()
    demo.objects_by_room = [[] for _ in game_map.room]
    for room_i in range(game_map.rooms):
        set_up_room_enemies(demo, room_i)
    hero = ctor_hero(load_images=True)
    demo.hero_room = place_hero(hero, game_map, 0)
    demo.hero = hero
    demo.hero_only = ctor_hero_only()
    bind_hero_only(demo.hero_only)
    bind_hero(hero)
    events.map_filename = Path(path).name
    events.hero_room = demo.hero_room
    events.do_hud = TRUE
    demo.hud = load_hud(palette)
    demo.do_hud = TRUE
    demo.menu = load_menu(palette)
    demo.box = BoxControl()
    demo.drop_surfs = load_drop_surfs(palette)
    demo.hero_surfs = [
        frame_surfaces(anim, palette) if anim.frames else []
        for anim in hero.anim
    ]
    return demo


_SPAWN_KILL_OPEN_ANIM = frozenset(
    {u_chest, u_bluechest, u_bluechestitem, u_ghut, u_button, u_gbutton}
)


def _cache_obj_anims(demo: MapDemo, obj, load_images: bool = True) -> None:
    if obj.id in demo.obj_anim_surfs:
        return
    if not load_images:
        demo.obj_anim_surfs[obj.id] = [[] for _ in obj.anim]
        return
    demo.obj_anim_surfs[obj.id] = [
        frame_surfaces(anim, demo.palette) if anim.frames else []
        for anim in obj.anim
    ]


def del_room_enemies(demo: MapDemo, room_i: int) -> None:
    """FB del_room_enemies: drop live objects for this room."""
    if 0 <= room_i < len(demo.objects_by_room):
        demo.objects_by_room[room_i] = []


def set_up_room_enemies(demo: MapDemo, room_i: int, load_images: bool | None = None) -> None:
    """FB set_up_room_enemies: spawn this room from map stubs, then spawn-kill."""
    if load_images is None:
        load_images = demo.load_images != 0
    if not (0 <= room_i < len(demo.game_map.room)):
        return
    room = demo.game_map.room[room_i]
    spawned = []
    for stub in room.enemy:
        obj = spawn_from_stub(stub, load_images=load_images)
        obj.num = len(spawned)
        spawned.append(obj)
        _cache_obj_anims(demo, obj, load_images=load_images)
        if obj.spawn_cond != 0:
            LLObject_CheckSpawn(obj)
            if obj.spawn_kill_trig != 0:
                if obj.unique_id in _SPAWN_KILL_OPEN_ANIM:
                    obj.current_anim = 1
                if obj.unique_id == u_ghut:
                    from lynn.object.combat import LLObject_ShiftState

                    LLObject_ShiftState(obj, 3)
    while len(demo.objects_by_room) <= room_i:
        demo.objects_by_room.append([])
    demo.objects_by_room[room_i] = spawned


def enter_map(
    demo: MapDemo,
    map_name: str,
    entry_i: int,
    load_images: bool | None = None,
    load_tileset: bool = True,
) -> None:
    """FB enter_map + set_up_room_enemies. Keep the hero; swap the map."""
    if load_images is None:
        load_images = demo.load_images != 0
    path = resolve_map_path(map_name)
    game_map = load_mapV(str(path), load_tileset=load_tileset)
    if load_tileset and (game_map.tileset is None or game_map.rooms == 0):
        raise FileNotFoundError(path)
    demo.game_map = game_map
    demo.tile_surfs = []
    if load_tileset and game_map.tileset is not None:
        demo.tile_surfs = frame_surfaces(game_map.tileset, demo.palette)
    demo.para_cache = {}
    demo.objects_by_room = [[] for _ in game_map.room]
    demo.load_images = TRUE if load_images else 0
    demo.load_tileset = TRUE if load_tileset else 0
    for i in range(game_map.rooms):
        set_up_room_enemies(demo, i, load_images=load_images)
    if demo.hero is not None:
        demo.hero_room = place_hero(demo.hero, game_map, entry_i)
        demo.hero.switch_room = -1
        demo.hero.to_map = ""
        bind_hero(demo.hero)
    events.map_filename = Path(path).name
    events.hero_room = demo.hero_room


def try_hero_teleport(demo: MapDemo) -> None:
    """FB check_against_teles then change_room type 0 (same map) or 1 (enter_map).

    Instant, no fade or song. Same-map dest rooms are deleted and respawned from stubs.
    """
    hero = demo.hero
    if hero is None:
        return
    if hero.switch_room != -1:
        return
    room_i = demo.hero_room
    if not (0 <= room_i < len(demo.game_map.room)):
        return
    room = demo.game_map.room[room_i]
    tele_i = check_teleports(hero, room.teleport, room.teleports)
    if tele_i == -1:
        return
    tele = room.teleport[tele_i]
    load_images = demo.load_images != 0
    if tele.to_map != "":
        hero.to_map = tele.to_map
        hero.to_entry = tele.to_room
        enter_map(
            demo,
            tele.to_map,
            tele.to_room,
            load_images=load_images,
            load_tileset=demo.load_tileset != 0,
        )
        return
    dest_room = tele.to_room
    if dest_room < 0 or dest_room >= demo.game_map.rooms:
        return
    if dest_room != room_i:
        del_room_enemies(demo, room_i)
        demo.hero_room = dest_room
        events.hero_room = dest_room
        set_up_room_enemies(demo, dest_room, load_images=load_images)
    hero.coords_x = tele.dx
    hero.coords_y = tele.dy
    hero.switch_room = -1


def tick_map_demo(demo: MapDemo, room_i: int) -> None:
    if 0 <= room_i < len(demo.objects_by_room):
        from lynn.events import bind_room

        room = demo.game_map.room[room_i] if room_i < len(demo.game_map.room) else None
        objs = demo.objects_by_room[room_i]
        bind_room(room, objs)
        bind_hero(demo.hero)
        events.hero_room = room_i
        tick_objects(objs)
        demo.do_hud = events.do_hud


def draw_map_demo(canvas: pygame.Surface, demo: MapDemo, room_i: int, cam_x: int, cam_y: int) -> None:
    room = demo.game_map.room[room_i]
    para = demo.para_cache.get(room_i)
    if room_i not in demo.para_cache:
        para = None
        if room.para_img is not None and room.para_img.frames:
            para = frame_surface(room.para_img, 0, demo.palette)
        demo.para_cache[room_i] = para
    canvas.fill((0, 0, 0))
    blit_room_tiles(canvas, room, demo.tile_surfs, cam_x, cam_y, para, layers=(0, 1))
    save_open = demo.hero is not None and demo.hero.menu_sel != 0
    _blit_y_sorted(canvas, demo, room_i, cam_x, cam_y, save_open)
    blit_room_tiles(canvas, room, demo.tile_surfs, cam_x, cam_y, layers=(2,))
    if room_i < len(demo.objects_by_room) and demo.drop_surfs:
        blit_enemy_loot(
            canvas,
            demo.objects_by_room[room_i],
            demo.hero,
            cam_x,
            cam_y,
            demo.drop_surfs,
        )
    if events.fade_white:
        fade = pygame.Surface((SCREEN_W, SCREEN_H))
        fade.fill((255, 255, 255))
        fade.set_alpha(max(0, min(255, int(events.fade_white))))
        canvas.blit(fade, (0, 0))
    if demo.do_hud != 0 and demo.hud is not None and demo.hero is not None and demo.hero_only is not None:
        blit_hud(canvas, demo.hero, demo.hero_only, demo.hud)
    if save_open and events.box_entity is not None:
        from lynn.object.save import blit_save_menu

        sp = events.box_entity
        blit_save_menu(canvas, sp, demo.obj_anim_surfs.get(sp.id, []), demo.hud)
    if demo.box is not None:
        blit_box(canvas, demo.box)


def _sort_y(obj) -> tuple:
    """FB mergesort_placed then y: placed first, then mid-y."""
    placed = int(getattr(obj, "placed", 0) or 0)
    mid_y = int(obj.coords_y) + (int(obj.perimeter_y) >> 1)
    return (placed, mid_y)


def _blit_y_sorted(canvas, demo: MapDemo, room_i: int, cam_x: int, cam_y: int, save_open: bool) -> None:
    """FB blit_y_sorted: room enemies + hero, by placed then y-mid."""
    sprites = []
    if 0 <= room_i < len(demo.objects_by_room):
        for obj in demo.objects_by_room[room_i]:
            if save_open and obj.unique_id == u_savepoint:
                continue
            sprites.append(obj)
    if demo.hero is not None:
        sprites.append(demo.hero)
    sprites.sort(key=_sort_y)
    for obj in sprites:
        if obj is demo.hero:
            anims = demo.hero_surfs
        else:
            anims = demo.obj_anim_surfs.get(obj.id)
        if not anims:
            continue
        anim_i = obj.current_anim
        if anim_i < 0 or anim_i >= len(anims) or not anims[anim_i]:
            continue
        blit_object(canvas, obj, cam_x, cam_y, anims[anim_i])


def load_palette_demo() -> tuple[LLPalette, list]:
    palette = load_pal("data/palette/ll.pal")
    sprite = LLSystem_ImageLoad(LYNN_SPR)
    return palette, frame_surfaces(sprite, palette)
