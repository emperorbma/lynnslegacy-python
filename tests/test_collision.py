from lynn.hero import ctor_hero, place_hero, try_same_map_room_teleport
from lynn.macros import quad_calc
from lynn.macros import testbit as ll_testbit
from lynn.map.collision import (
    check_against,
    check_against_teles,
    check_bounds,
    check_teleports,
    check_walk,
    move_object,
)
from lynn.map.loader import load_mapV
from lynn.map.types import TeleportType
from lynn.object.char import CharType
from lynn.paths import resolve_map_path


def test_quad_calc_corners():
    assert quad_calc(0, 0) == 0
    assert quad_calc(1, 0) == 1
    assert quad_calc(0, 1) == 2
    assert quad_calc(1, 1) == 3


def test_testbit():
    assert ll_testbit(0x8000, 15) != 0
    assert ll_testbit(0x4000, 14) != 0
    assert ll_testbit(0x0100, 8) != 0
    assert ll_testbit(1, 0) != 0
    assert ll_testbit(0, 15) == 0


def _hero_at_entry():
    m = load_mapV(str(resolve_map_path("island3")), load_tileset=False)
    hero = ctor_hero(load_images=False)
    place_hero(hero, m, 0)
    return m, hero, m.room[0]


def test_island3_spawn_has_an_open_direction():
    _m, hero, room = _hero_at_entry()
    open_dirs = [d for d in range(4) if check_walk(hero, d, room) != 0]
    assert open_dirs, "entry 0 should not be boxed in on all four sides"


def test_move_object_stays_put_when_blocked():
    m, hero, room = _hero_at_entry()
    blocked = [d for d in range(4) if check_walk(hero, d, room) == 0]
    if not blocked:
        # Carve a fake solid wall in front of dir 0.
        hero.direction = 0
        xq = int(hero.coords_x) >> 3
        yq = (int(hero.coords_y) >> 3) - 1
        t_index = ((yq << 3) >> 4) * room.x + ((xq << 3) >> 4)
        if 0 <= t_index < len(room.layout[0]):
            room.layout[0][t_index] = 0xFFFF
        blocked = [0]
    d = blocked[0]
    hero.direction = d
    x0, y0 = hero.coords_x, hero.coords_y
    assert move_object(hero, room, only_looking=0, moment=1) == 0
    assert (hero.coords_x, hero.coords_y) == (x0, y0)


def test_move_object_advances_one_pixel_when_open():
    _m, hero, room = _hero_at_entry()
    open_dirs = [d for d in range(4) if check_walk(hero, d, room) != 0]
    assert open_dirs
    d = open_dirs[0]
    hero.direction = d
    x0, y0 = hero.coords_x, hero.coords_y
    result = move_object(hero, room, only_looking=0, moment=1)
    assert result != 0
    if d == 0:
        assert hero.coords_y == y0 - 1
    elif d == 1:
        assert hero.coords_x == x0 + 1
    elif d == 2:
        assert hero.coords_y == y0 + 1
    else:
        assert hero.coords_x == x0 - 1


def test_ctor_hero_perimeter():
    hero = ctor_hero(load_images=False)
    assert hero.id.endswith("lynn.xml")
    assert hero.perimeter_x == 16
    assert hero.perimeter_y == 16
    assert hero.hp == 6
    assert hero.money == 0
    assert hero.switch_room == -1
    dummy = CharType()
    assert dummy.walk_speed == 0.009
    assert dummy.switch_room == -1


def test_impassable_object_blocks_step():
    m, hero, room = _hero_at_entry()
    wall = CharType()
    wall.num = 1
    wall.impassable = 1
    wall.perimeter_x = 16
    wall.perimeter_y = 16
    wall.coords_x = hero.coords_x
    wall.coords_y = hero.coords_y - 16
    hero.direction = 0
    assert check_against(hero, wall, 0) == 1
    x0, y0 = hero.coords_x, hero.coords_y
    assert move_object(hero, room, moment=1, others=[wall]) == 0
    assert (hero.coords_x, hero.coords_y) == (x0, y0)


def test_passable_object_does_not_block():
    m, hero, room = _hero_at_entry()
    moth = CharType()
    moth.num = 2
    moth.impassable = 0
    moth.perimeter_x = 16
    moth.perimeter_y = 16
    moth.coords_x = hero.coords_x
    moth.coords_y = hero.coords_y - 16
    hero.direction = 0
    assert check_against(hero, moth, 0) == 0


def test_rtele_xml_is_impassable():
    from lynn.object.xml_load import spawn_from_stub
    from types import SimpleNamespace

    stub = SimpleNamespace(
        id="data/object/rtele2.xml",
        x_origin=0,
        y_origin=0,
        direction=0,
    )
    obj = spawn_from_stub(stub, load_images=False)
    assert obj.impassable != 0


def test_check_bounds_overlap_and_edge_touch():
    a = (10, 10, 16, 16)
    assert check_bounds(a, (20, 20, 16, 16)) == 0
    assert check_bounds(a, (26, 10, 16, 16)) == -1
    assert check_bounds(a, (25, 10, 16, 16)) == 0
    assert check_bounds(a, (10, 26, 16, 16)) == -1
    assert check_bounds(a, (30, 10, 16, 16)) == -1
    assert check_bounds(a, (18, 18, 0, 0)) == 0
    assert check_bounds(a, (30, 18, 0, 0)) == -1


def test_check_teleports_first_overlap():
    hero = CharType()
    hero.coords_x = 160
    hero.coords_y = 224
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    teles = [
        TeleportType(x=144, y=239, w=48, h=1, to_room=1),
        TeleportType(x=0, y=0, w=16, h=16, to_room=9),
    ]
    assert check_teleports(hero, teles) == 0
    hero.coords_y = 112
    assert check_teleports(hero, teles) == -1
    hero.coords_x = 0
    hero.coords_y = 0
    assert check_teleports(hero, teles) == 1


def _forest_fall():
    path = resolve_map_path("forest_fall")
    if not path.is_file():
        import pytest

        pytest.skip("forest_fall.map missing")
    m = load_mapV(str(path), load_tileset=False)
    hero = ctor_hero(load_images=False)
    place_hero(hero, m, 0)
    return m, hero


def test_forest_fall_spawn_is_not_on_a_tele():
    m, hero = _forest_fall()
    assert check_teleports(hero, m.room[0].teleport) == -1
    assert try_same_map_room_teleport(hero, m, 0) == 0
    assert (hero.coords_x, hero.coords_y) == (m.entry[0].x, m.entry[0].y)


def test_forest_fall_south_strip_warps_to_room_1():
    m, hero = _forest_fall()
    south = m.room[0].teleport[0]
    assert south.to_map == ""
    assert south.to_room == 1
    hero.coords_x = 160
    hero.coords_y = (m.room[0].y << 4) - hero.perimeter_y
    assert check_against_teles(hero, m.room[0]) == 0
    new_room = try_same_map_room_teleport(hero, m, 0)
    assert new_room == 1
    assert (hero.coords_x, hero.coords_y) == (south.dx, south.dy)
    assert try_same_map_room_teleport(hero, m, 1) == 1


def test_forest_fall_room1_north_returns_without_ping_pong():
    m, hero = _forest_fall()
    north = m.room[1].teleport[0]
    assert north.to_map == ""
    assert north.to_room == 0
    hero.coords_x = 160
    hero.coords_y = 0
    new_room = try_same_map_room_teleport(hero, m, 1)
    assert new_room == 0
    assert (hero.coords_x, hero.coords_y) == (north.dx, north.dy)
    assert try_same_map_room_teleport(hero, m, 0) == 0


def test_forest_fall_map_tele_is_ignored():
    m, hero = _forest_fall()
    nerme = m.room[0].teleport[1]
    assert nerme.to_map
    hero.coords_x = nerme.x - 8
    hero.coords_y = nerme.y - 8
    assert check_teleports(hero, m.room[0].teleport) == 1
    assert check_against_teles(hero, m.room[0]) == -1
    x0, y0 = hero.coords_x, hero.coords_y
    assert try_same_map_room_teleport(hero, m, 0) == 0
    assert (hero.coords_x, hero.coords_y) == (x0, y0)
