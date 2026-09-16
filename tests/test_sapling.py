import lynn.object  # noqa: F401  registers seq funcs

from lynn import clock
from lynn.constants import DF_MAIN_CHAR, TRUE, u_bush
from lynn.events import bind_hero_only, now, reset_events
import lynn.events as events
from lynn.gfx.box import BoxControl
from lynn.hero import DIR_UP, ctor_hero, ctor_hero_only
from lynn.map.loader import load_mapV
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import resolve_map_path
from lynn.sequence import (
    LLObject_isTouching,
    is_facing,
    play_sequence,
    try_action_sequence,
    try_touch_sequence,
)


def _room1_sapling():
    reset_events()
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    room = m.room[1]
    objs = []
    sapling = None
    for stub in room.enemy:
        obj = spawn_from_stub(stub, load_images=False)
        obj.num = len(objs)
        objs.append(obj)
        if obj.id.endswith("sapling.xml"):
            sapling = obj
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero_only(only)
    return m, hero, only, objs, sapling


def test_sapling_is_in_room1_center():
    _m, _hero, _only, objs, sapling = _room1_sapling()
    assert sapling is not None
    assert sapling.coords_x == 160
    assert sapling.coords_y == 240
    assert sapling.action_sequence != 0
    assert sapling.seq
    assert sapling.seq[0].ent_code == [-1, 16]


def test_facing_and_touching_from_south():
    _m, hero, _only, _objs, sapling = _room1_sapling()
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    sapling.perimeter_x = 16
    sapling.perimeter_y = 8
    hero.direction = DIR_UP
    hero.coords_x = 160
    hero.coords_y = 247
    assert is_facing(hero, sapling) == 0
    assert LLObject_isTouching(hero, sapling) == 0


def test_action_starts_sapling_seq():
    _m, hero, only, objs, sapling = _room1_sapling()
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    sapling.perimeter_x = 16
    sapling.perimeter_y = 8
    hero.direction = DIR_UP
    hero.coords_x = 160
    hero.coords_y = 247
    only.action = TRUE
    seq = try_action_sequence(hero, only, objs)
    assert seq is not None
    assert seq.ent[0] is hero
    assert seq.ent[1] is sapling


def test_sapling_seq_gives_weapon_and_happen_3():
    _m, hero, only, objs, sapling = _room1_sapling()
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    sapling.perimeter_x = 16
    sapling.perimeter_y = 8
    hero.direction = DIR_UP
    hero.coords_x = 160
    hero.coords_y = 247
    only.action = TRUE
    seq = try_action_sequence(hero, only, objs)
    box = BoxControl()
    only.action = 0
    for i in range(400):
        clock.timer = i * 0.05
        if box.activated != 0:
            only.action = TRUE
        seq = play_sequence(seq, box, only)
        if seq is None:
            break
        only.action = 0
    assert seq is None
    assert only.has_weapon == 0
    assert only.weapon == 0
    assert now[3] != 0
    assert events.do_hud != 0


def test_y_sort_puts_south_sprite_on_top():
    from lynn.demos import _sort_y
    from lynn.object.char import CharType

    north = CharType()
    north.coords_y = 240
    north.perimeter_y = 8
    south = CharType()
    south.coords_y = 247
    south.perimeter_y = 16
    assert _sort_y(north) < _sort_y(south)


def test_r1_bushes_south_of_sapling_have_touch_dialogue():
    m, hero, _only, objs, _sapling = _room1_sapling()
    bushes = [o for o in objs if o.id.endswith("bush.xml") and o.coords_y == 496]
    assert len(bushes) == 3
    bush = bushes[1]
    assert bush.coords_x == 160
    assert bush.touch_sequence != 0
    assert bush.seq
    text = bush.seq[0].Command[0].ent[0].text
    assert "thick bushes" in text
    assert "break" in text


def test_cut_bushes_vanish_this_visit_and_respawn_on_reenter():
    """Cut bushes are gone in this room visit; a fresh spawn brings them back."""
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.gfx.blit import blit_object
    from lynn.gfx.palette import load_pal
    from lynn.object.combat import LLObject_DamageCalc
    from lynn.object.tick import tick_objects
    from lynn.paths import data_file
    import pygame

    reset_events()
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=m,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    demo.hero_only.has_weapon = 0
    demo.hero_only.weapon = 0
    bind_hero_only(demo.hero_only)
    demo.hero_room = 1
    set_up_room_enemies(demo, 1, load_images=False)
    objs = demo.objects_by_room[1]
    bushes = [o for o in objs if o.unique_id == u_bush and int(o.coords_y) == 496]
    assert len(bushes) == 3
    for bush in bushes:
        bush.dmg_id = DF_MAIN_CHAR
        LLObject_DamageCalc(bush)
    for i in range(40):
        clock.timer = i * 0.05
        tick_objects(objs)
        if all(b.invisible != 0 for b in bushes):
            break
    assert all(b.dead != 0 and b.invisible != 0 and b.impassable == 0 for b in bushes)

    pygame.display.set_mode((32, 32))
    canvas = pygame.Surface((32, 32))
    canvas.fill((0, 0, 0))
    tile = pygame.Surface((16, 16))
    tile.fill((0, 180, 0))
    blit_object(canvas, bushes[0], 0, 0, [tile])
    assert canvas.get_at((8, 8))[1] == 0

    set_up_room_enemies(demo, 1, load_images=False)
    fresh = [
        o
        for o in demo.objects_by_room[1]
        if o.unique_id == u_bush and int(o.coords_y) == 496
    ]
    assert len(fresh) == 3
    assert all(b.dead == 0 and b.invisible == 0 and b.impassable != 0 for b in fresh)


def test_touch_sequence_fires_standing_against_the_bush():
    _m, hero, _only, objs, _sapling = _room1_sapling()
    bushes = [o for o in objs if o.id.endswith("bush.xml") and o.coords_y == 496]
    bush = next(o for o in bushes if o.coords_x == 160)
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.coords_x = 160
    hero.coords_y = 480
    assert LLObject_isTouching(hero, bush) == 0
    seq = try_touch_sequence(hero, objs)
    assert seq is not None
    assert "thick bushes" in seq.Command[0].ent[0].text


def test_fade_to_white_reaches_full():
    from lynn.object.seq_funcs import __fade_to_white
    from lynn.object.char import CharType
    from lynn import clock

    reset_events()
    o = CharType()
    o.fade_time = 0.01
    clock.timer = 0.0
    for i in range(200):
        clock.timer = i * 0.02
        if __fade_to_white(o) == 1:
            break
    assert events.fade_white == 255
