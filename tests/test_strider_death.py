"""Steel Strider death scene (l_restricted room 2) plays through, quake included."""

from __future__ import annotations

import lynn.events as events
import lynn.object  # noqa: F401
import lynn.object.seq_funcs  # noqa: F401
from lynn import clock
from lynn.demos import MapDemo, set_up_room_enemies
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
from lynn.gfx.box import BoxControl
from lynn.gfx.palette import load_pal
from lynn.gfx.quake import screen_quake
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.tick import tick_objects
from lynn.paths import data_file, resolve_map_path
from lynn.sequence import bind_sequence_ents, play_sequence


def test_quake_sets_and_clears_violence():
    reset_events()
    only = ctor_hero_only()
    bind_hero_only(only)
    this = CharType()
    this.chap = 6
    assert lookup_func("__quake")(this) == 1
    assert only.quakeViolence == 6
    this.chap = -1
    lookup_func("__quake")(this)
    assert only.quakeViolence == 0


def test_screen_quake_noop_at_zero():
    import pygame

    surf = pygame.Surface((8, 8))
    surf.fill((9, 9, 9))
    screen_quake(surf, 0)
    assert surf.get_at((0, 0))[:3] == (9, 9, 9)


def test_strider_death_scene_completes():
    reset_events()
    hero, only = ctor_hero(), ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    gm = load_mapV(str(resolve_map_path("l_restricted")), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=gm,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in gm.room]
    demo.hero, demo.hero_only, demo.box, demo.hero_room = hero, only, BoxControl(), 2
    set_up_room_enemies(demo, 2, load_images=False)
    objs = demo.objects_by_room[2]
    bind_room(gm.room[2], objs)
    hero.coords_x, hero.coords_y = 216, 260
    cam = (100, 100)
    boss = objs[1]
    boss.invincible = 0
    boss.hp = 0
    for _ in range(800):
        clock.timer += 0.05
        tick_objects(objs, cam)
        if events.pending_seq is not None:
            break
    seq = events.pending_seq
    assert seq is not None
    events.pending_seq = None
    bind_sequence_ents(seq, hero, objs)
    shook = False
    for _ in range(6000):
        clock.timer += 0.05
        only.action = 1 if demo.box.activated else 0
        tick_objects(objs, cam)
        seq = play_sequence(seq, demo.box, only)
        shook = shook or only.quakeViolence != 0
        if seq is None:
            break
    assert seq is None, "strider death sequence never finished"
    assert shook
