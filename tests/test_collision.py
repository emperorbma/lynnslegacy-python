from lynn.hero import ctor_hero, place_hero
from lynn.macros import quad_calc
from lynn.macros import testbit as ll_testbit
from lynn.map.collision import check_against, check_walk, move_object
from lynn.map.loader import load_mapV
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
    dummy = CharType()
    assert dummy.walk_speed == 0.009


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
