"""Preserved proof-of-concept scenes. Select with `python -m lynn <mode>`."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from lynn.constants import SCREEN_H, SCREEN_W
from lynn.gfx.blit import blit_object, blit_room_tiles
from lynn.gfx.image import LLSystem_ImageLoad, frame_surface, frame_surfaces
from lynn.gfx.palette import LLPalette, load_pal
import lynn.object  # registers __idle_animate / __return_idle / __reset_frame
from lynn.hero import ctor_hero, place_hero
from lynn.map.loader import load_mapV
from lynn.map.types import MapType
from lynn.object.tick import tick_objects
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
    if not with_objects:
        demo.objects_by_room = [[] for _ in game_map.room]
        return demo
    for room in game_map.room:
        spawned = []
        for stub in room.enemy:
            obj = spawn_from_stub(stub, load_images=True)
            spawned.append(obj)
            if obj.id not in demo.obj_anim_surfs:
                demo.obj_anim_surfs[obj.id] = [
                    frame_surfaces(anim, palette) if anim.frames else []
                    for anim in obj.anim
                ]
        demo.objects_by_room.append(spawned)
    hero = ctor_hero(load_images=True)
    demo.hero_room = place_hero(hero, game_map, 0)
    demo.hero = hero
    demo.hero_surfs = [
        frame_surfaces(anim, palette) if anim.frames else []
        for anim in hero.anim
    ]
    return demo


def tick_map_demo(demo: MapDemo, room_i: int) -> None:
    if 0 <= room_i < len(demo.objects_by_room):
        tick_objects(demo.objects_by_room[room_i])


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
    if room_i < len(demo.objects_by_room):
        for obj in demo.objects_by_room[room_i]:
            anims = demo.obj_anim_surfs.get(obj.id)
            if not anims or obj.current_anim >= len(anims):
                continue
            blit_object(canvas, obj, cam_x, cam_y, anims[obj.current_anim])
    if demo.hero is not None and demo.hero_surfs:
        anim_i = demo.hero.current_anim
        if anim_i < len(demo.hero_surfs):
            blit_object(canvas, demo.hero, cam_x, cam_y, demo.hero_surfs[anim_i])
    blit_room_tiles(canvas, room, demo.tile_surfs, cam_x, cam_y, layers=(2,))


def load_palette_demo() -> tuple[LLPalette, list]:
    palette = load_pal("data/palette/ll.pal")
    sprite = LLSystem_ImageLoad(LYNN_SPR)
    return palette, frame_surfaces(sprite, palette)
