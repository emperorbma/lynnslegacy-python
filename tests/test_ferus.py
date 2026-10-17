"""Ferus boss (l_arena): intro, both death scenes, volley timer and the red-tint step."""

from __future__ import annotations

import pygame

import lynn.events as events
import lynn.object  # noqa: F401
import lynn.object.seq_funcs  # noqa: F401
from lynn import clock
from lynn.constants import DF_MAIN_CHAR
from lynn.demos import MapDemo, set_up_room_enemies
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
from lynn.gfx.box import BoxControl
from lynn.gfx.palette import load_pal
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.combat import LLObject_ProcessHurt
from lynn.object.dispatch import lookup_func
from lynn.object.tick import tick_objects
from lynn.paths import data_file, resolve_map_path
from lynn.sequence import bind_sequence_ents, play_sequence

CAM = (168, 100)


def _arena():
    pygame.display.init()
    pygame.display.set_mode((10, 10))
    reset_events()
    hero, only = ctor_hero(), ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    gm = load_mapV(str(resolve_map_path("l_arena")), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=gm,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in gm.room]
    demo.hero, demo.hero_only, demo.box, demo.hero_room = hero, only, BoxControl(), 0
    events.palette = demo.palette
    set_up_room_enemies(demo, 0, load_images=False)
    objs = demo.objects_by_room[0]
    bind_room(gm.room[0], objs)
    hero.coords_x, hero.coords_y = 328, 300
    return demo, hero, only, gm, objs


def _run(seq, demo, only, objs, frames=20000) -> bool:
    for f in range(frames):
        clock.timer += 0.017
        only.action = 1 if (demo.box.activated and f % 20 == 0) else 0
        tick_objects(objs, CAM)
        seq = play_sequence(seq, demo.box, only)
        if seq is None and events.pending_seq is not None:
            seq = events.pending_seq
            events.pending_seq = None
        if seq is None:
            return True
    return False


def _kill(obj) -> None:
    obj.invincible = 0
    obj.hurt = obj.hp
    obj.dmg_id = DF_MAIN_CHAR
    LLObject_ProcessHurt(obj)


def _death_seq(objs, obj, hero):
    for _ in range(4000):
        clock.timer += 0.017
        tick_objects(objs, CAM)
        if events.pending_seq is not None:
            seq = events.pending_seq
            events.pending_seq = None
            bind_sequence_ents(seq, hero, objs)
            return seq
    return None


def test_red_tint_sets_and_tints():
    reset_events()
    pal = load_pal(data_file("palette", "ll.pal"))
    events.palette = pal
    this = CharType()
    assert lookup_func("__red_tint")(this) == 1
    # Index 26 is the health red (255, 20, 20). 6-bit red and green collapse to 0.
    assert pal.colors[26] == (0, 0, 20)
    lookup_func("__color_off")(this)
    assert pal.colors[26] == (0, 0, 0)
    lookup_func("__color_on")(this)
    assert pal.colors[26] == pal.master[26]


def test_ferus_intro_completes():
    demo, hero, only, gm, objs = _arena()
    hero.coords_x, hero.coords_y = 64, 408
    seq = gm.entry[0].seq[0]
    seq.current_command = 0
    bind_sequence_ents(seq, hero, objs)
    assert _run(seq, demo, only, objs)


def test_ferus_volley_fires_and_hits_reset_it():
    demo, hero, only, gm, objs = _arena()
    fer = objs[0]
    fired = False
    for _ in range(1000):
        clock.timer += 0.017
        tick_objects(objs, CAM)
        fired = fired or fer.projectile.active != 0
    assert fired


def test_ferus_both_phases_finish():
    demo, hero, only, gm, objs = _arena()
    fer, core = objs[0], objs[4]
    _kill(fer)
    seq = _death_seq(objs, fer, hero)
    assert seq is not None and _run(seq, demo, only, objs)
    assert fer.dead != 0
    _kill(core)
    seq = _death_seq(objs, core, hero)
    assert seq is not None and _run(seq, demo, only, objs), "core death scene stalls"
    assert events.palette.colors[26] == (0, 0, 20)
