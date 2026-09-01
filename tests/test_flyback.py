import lynn.object  # noqa: F401
from lynn import clock
from lynn.events import bind_room
from lynn.map.collision import check_walk
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.combat_funcs import __do_flyback
from lynn.object.move_ai import __chase
from lynn.paths import resolve_map_path


def _room1():
    return load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False).room[1]


def test_flyback_stops_on_solid_tile():
    room = _room1()
    o = CharType()
    o.perimeter_x = 16
    o.perimeter_y = 8
    o.coords_x = 160
    o.coords_y = 280
    o.fly_length = 13
    o.fly_speed = 0.004
    o.fly_y = -1
    o.fly_x = 0
    # Plant a wall immediately north.
    xq = int(o.coords_x) >> 3
    yq = (int(o.coords_y) >> 3) - 1
    t_index = ((yq << 3) >> 4) * room.x + ((xq << 3) >> 4)
    room.layout[0][t_index] = 0xFFFF
    assert check_walk(o, 0, room) == 0
    bind_room(room, [o])
    y0 = o.coords_y
    clock.timer = 0.0
    for i in range(20):
        clock.timer = i * 0.004
        if __do_flyback(o) == 1:
            break
    assert o.coords_y == y0


def test_flyback_moves_in_open_space():
    room = _room1()
    o = CharType()
    o.perimeter_x = 16
    o.perimeter_y = 8
    o.coords_x = 160
    o.coords_y = 280
    o.fly_length = 13
    o.fly_speed = 0.004
    o.fly_x = 1
    o.fly_y = 0
    bind_room(room, [o])
    x0 = o.coords_x
    clock.timer = 0.0
    for i in range(40):
        clock.timer = i * 0.004
        if __do_flyback(o) == 1:
            break
    assert o.coords_x > x0


def test_chase_homes_in_on_hero():
    from lynn.events import bind_hero
    from lynn.hero import ctor_hero

    room = _room1()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 200
    hero.coords_y = 280
    bind_hero(hero)
    o = CharType()
    o.perimeter_x = 16
    o.perimeter_y = 8
    o.coords_x = 160
    o.coords_y = 280
    o.mad_walk_speed = 0.01
    bind_room(room, [o])
    x0 = o.coords_x
    clock.timer = 0.0
    for i in range(40):
        clock.timer = i * 0.01
        __chase(o)
    assert o.coords_x > x0
