"""Walk/hold catch-up: 60 Hz display vs FB Timer + walk_speed (Lynn 0.009 → ~111 px/s)."""

from lynn import clock
from lynn.events import bind_room, reset_events
from lynn.hero import DIR_RIGHT, ctor_hero, hero_walk_step
from lynn.map.collision import check_walk
from lynn.map.types import RoomType
from lynn.object.char import CharType
from lynn.object.move_ai import __walk


def _open_room(tiles=40) -> RoomType:
    room = RoomType()
    room.x = tiles
    room.y = tiles
    n = tiles * (tiles + 1) + 2
    room.layout = [[0] * n for _ in range(3)]
    return room


def test_pop_due_keeps_leftover_at_60hz():
    clock.timer = 0.0
    n, hold = clock.pop_due(0.0, 0.009)
    assert n == 1
    assert abs(hold - 0.009) < 1e-9
    total = n
    for i in range(1, 61):
        clock.timer = i / 60.0
        n, hold = clock.pop_due(hold, 0.009)
        total += n
    # 1s / 0.009 ≈ 111 steps; leftover-sync would only give 60.
    assert total >= 100
    assert total <= 112


def test_hero_walks_about_111_px_per_second_at_60hz():
    reset_events()
    room = _open_room()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 32
    hero.coords_y = 32
    hero.walk_speed = 0.009
    hero.walk_hold = 0
    bind_room(room, [])
    assert check_walk(hero, DIR_RIGHT, room) != 0
    clock.timer = 0.0
    hero_walk_step(hero, room, DIR_RIGHT, [])
    for i in range(1, 61):
        clock.timer = i / 60.0
        hero_walk_step(hero, room, DIR_RIGHT, [])
    moved = hero.coords_x - 32
    assert moved >= 100
    assert moved <= 112


def test_walk_proc_matches_walk_speed_at_60hz():
    from lynn.object.xml_load import LLSystem_ObjectFromXML

    reset_events()
    room = _open_room()
    o = CharType()
    o.id = "data/object/roamer.xml"
    o = LLSystem_ObjectFromXML(o, load_images=False)
    o.coords_x = 32
    o.coords_y = 32
    o.direction = DIR_RIGHT
    o.walk_speed = 0.009
    o.walk_length = 400
    o.walk_buffer = 400
    o.unstoppable_by_tile = -1
    bind_room(room, [o])
    clock.timer = 0.0
    __walk(o)
    for i in range(1, 61):
        clock.timer = i / 60.0
        __walk(o)
    moved = o.coords_x - 32
    assert moved >= 100
    assert moved <= 112


def test_pop_due_does_not_burst_after_a_pause():
    clock.timer = 0.0
    n, hold = clock.pop_due(0.0, 0.009)
    assert n == 1
    clock.timer = 1.0
    n, hold = clock.pop_due(hold, 0.009)
    assert n == 1
    clock.timer = 1.0 + 1.0 / 60.0
    n, _hold = clock.pop_due(hold, 0.009)
    assert n <= 2
