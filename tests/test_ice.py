"""FB ice tiles (layer 0 bit 8): momentum build, slide after release, land snap."""

from lynn import clock
from lynn.constants import TRUE
from lynn.events import bind_room, reset_events
from lynn.hero import DIR_RIGHT, DIR_UP, ctor_hero, hero_walk_step
from lynn.macros import check_ice
from lynn.macros import testbit as ice_bit
from lynn.map.loader import load_mapV
from lynn.map.types import RoomType
from lynn.paths import resolve_map_path


def _ice_room(tiles=20) -> RoomType:
    room = RoomType()
    room.x = tiles
    room.y = tiles
    n = tiles * (tiles + 1) + 2
    ice = 1 << 8
    room.layout = [[ice] * n, [0] * n, [0] * n]
    return room


def _land_room(tiles=40) -> RoomType:
    room = RoomType()
    room.x = tiles
    room.y = tiles
    n = tiles * (tiles + 1) + 2
    room.layout = [[0] * n for _ in range(3)]
    return room


def test_check_ice_sets_on_ice_from_bit_8():
    room = _ice_room()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 32
    hero.coords_y = 32
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    check_ice(hero, room)
    assert hero.on_ice == TRUE
    room.layout[0] = [0] * len(room.layout[0])
    check_ice(hero, room)
    assert hero.on_ice == 0


def test_gelidus_r0_has_ice_tiles():
    m = load_mapV(str(resolve_map_path("gelidus")), load_tileset=False)
    ice = sum(1 for t in m.room[0].layout[0] if ice_bit(t, 8))
    assert ice > 0


def test_ice_keeps_sliding_after_keys_released():
    reset_events()
    room = _ice_room()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 32
    hero.coords_y = 32
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.walk_speed = 0.009
    bind_room(room, [])
    clock.timer = 0.0
    hero_walk_step(hero, room, DIR_RIGHT, [])
    for i in range(1, 31):
        clock.timer = i / 60.0
        hero_walk_step(hero, room, DIR_RIGHT, [])
    charged = hero.coords_x
    assert charged > 32
    assert hero.on_ice == TRUE
    for i in range(31, 51):
        clock.timer = i / 60.0
        hero_walk_step(hero, room, None, [])
    assert hero.coords_x > charged
    assert any(m > 0 for m in hero.momentum)


def test_leaving_ice_snaps_and_stops_without_keys():
    reset_events()
    ice = _ice_room()
    land = _land_room()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 32.7
    hero.coords_y = 32.2
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.momentum[DIR_RIGHT] = 1.0
    bind_room(land, [])
    clock.timer = 0.0
    hero_walk_step(hero, land, None, [])
    assert hero.on_ice == 0
    assert hero.coords_x == 32
    assert hero.coords_y == 32
    assert hero.momentum[DIR_RIGHT] == 0.0
    del ice


def test_ice_diagonal_builds_both_axes():
    reset_events()
    room = _ice_room()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 48
    hero.coords_y = 48
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_room(room, [])
    clock.timer = 0.0
    hero_walk_step(hero, room, (DIR_UP, DIR_RIGHT), [])
    for i in range(1, 20):
        clock.timer = i / 60.0
        hero_walk_step(hero, room, (DIR_UP, DIR_RIGHT), [])
    assert hero.coords_x > 48
    assert hero.coords_y < 48
    assert hero.momentum[DIR_RIGHT] > 0
    assert hero.momentum[DIR_UP] > 0
