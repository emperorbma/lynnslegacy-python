"""Limbo arena: the dimension seed fight (moth shots, seed death hook, shot geometry)."""

from __future__ import annotations

import math

import pygame

import lynn.events as events
from lynn import clock
from lynn.constants import DF_MAIN_CHAR, PROJECTILE_SPIRAL, PROJECTILE_SUN, PROJECTILE_TRACK
from lynn.demos import MapDemo, set_up_room_enemies
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
from lynn.gfx.box import BoxControl
from lynn.gfx.palette import load_pal
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.loader import load_mapV
from lynn.object.char import CharType, EntityProjectile
from lynn.object.combat import LLObject_ProcessHurt
from lynn.object.dispatch import lookup_func
from lynn.object.projectile import LLObject_IncrementProjectiles, LLObject_InitializeProjectiles
from lynn.object.tick import tick_objects
from lynn.paths import data_file, resolve_map_path
from lynn.sequence import bind_sequence_ents, play_sequence


def _arena():
    pygame.display.init()
    pygame.display.set_mode((10, 10))
    reset_events()
    hero, only = ctor_hero(), ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    gm = load_mapV(str(resolve_map_path("limbo_arena")), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=gm,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in gm.room]
    demo.hero, demo.hero_only, demo.box, demo.hero_room = hero, only, BoxControl(), 0
    set_up_room_enemies(demo, 0, load_images=False)
    objs = demo.objects_by_room[0]
    bind_room(gm.room[0], objs)
    hero.coords_x, hero.coords_y = 544, 976
    return demo, hero, only, gm, objs


def _cam(hero):
    return hero.coords_x - 160, hero.coords_y - 100


def _run(seq, demo, hero, only, objs, frames=30000) -> bool:
    for f in range(frames):
        clock.timer += 0.017
        only.action = 1 if (demo.box.activated and f % 20 == 0) else 0
        tick_objects(objs, _cam(hero))
        seq = play_sequence(seq, demo.box, only)
        if seq is None and events.pending_seq is not None:
            seq = events.pending_seq
            events.pending_seq = None
            bind_sequence_ents(seq, hero, objs)
        if seq is None:
            return True
    return False


def test_random_locations_land_on_listed_tiles():
    this = CharType()
    lookup_func("__moth_random_loc")(this)
    assert (this.coords_x >> 4, this.coords_y >> 4) in {(13, 41), (17, 62), (60, 51), (44, 26), (65, 16)}
    lookup_func("__seed_random_loc")(this)
    assert (this.coords_x >> 4, this.coords_y >> 4) in {(2, 47), (2, 61), (68, 46), (33, 19), (66, 2)}


def test_random_proj_picks_one_of_three_styles():
    seen = set()
    for _ in range(100):
        this = CharType()
        this.projectile = EntityProjectile()
        lookup_func("__moth_random_proj")(this)
        seen.add(this.proj_style)
        assert len(this.projectile.coords) >= this.projectile.projectiles
    assert seen == {PROJECTILE_SUN, PROJECTILE_TRACK, PROJECTILE_SPIRAL}


def test_sun_shots_radiate_from_start():
    this = CharType()
    this.proj_style = PROJECTILE_SUN
    this.projectile = EntityProjectile(projectiles=4, coords=[[0, 0] for _ in range(4)])
    this.coords_x = this.coords_y = 100
    LLObject_InitializeProjectiles(this)
    sx, sy = this.projectile.startVector
    this.projectile.travelled = 10
    LLObject_IncrementProjectiles(this)
    for pair in this.projectile.coords:
        assert math.hypot(pair[0] - sx, pair[1] - sy) == 10 or abs(math.hypot(pair[0] - sx, pair[1] - sy) - 10) < 1e-6


def test_track_shot_homes_on_hero():
    reset_events()
    hero = ctor_hero()
    bind_hero(hero)
    hero.coords_x, hero.coords_y = 400, 0
    this = CharType()
    this.proj_style = PROJECTILE_TRACK
    this.projectile = EntityProjectile(projectiles=1, coords=[[0, 0]])
    this.coords_x = this.coords_y = 0
    LLObject_InitializeProjectiles(this)
    this.projectile.travelled = 4
    before = this.projectile.coords[0][0]
    LLObject_IncrementProjectiles(this)
    assert this.projectile.coords[0][0] > before


def test_seed_fight_and_death_scene_finish():
    demo, hero, only, gm, objs = _arena()
    seq = gm.entry[0].seq[0]
    bind_sequence_ents(seq, hero, objs)
    assert _run(seq, demo, hero, only, objs)
    moth, battlemoth, seed = objs[1], objs[2], objs[3]
    fired = set()
    for _ in range(3000):
        clock.timer += 0.017
        tick_objects(objs, _cam(hero))
        if battlemoth.projectile and battlemoth.projectile.active:
            fired.add(battlemoth.proj_style)
    assert fired & {PROJECTILE_SUN, PROJECTILE_TRACK, PROJECTILE_SPIRAL}
    seed.invincible = 0
    seed.hurt = seed.hp
    seed.dmg_id = DF_MAIN_CHAR
    LLObject_ProcessHurt(seed)
    assert seed.dead == 1 and battlemoth.hp == 0
    seq = None
    for _ in range(4000):
        clock.timer += 0.017
        tick_objects(objs, _cam(hero))
        if events.pending_seq is not None:
            seq = events.pending_seq
            events.pending_seq = None
            bind_sequence_ents(seq, hero, objs)
            break
    assert seq is not None and _run(seq, demo, hero, only, objs)
