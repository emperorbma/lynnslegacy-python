import lynn.object  # noqa: F401  registers seq funcs

from lynn import clock
from lynn.constants import TRUE
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
