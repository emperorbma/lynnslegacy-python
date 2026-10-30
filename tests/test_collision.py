from lynn import clock
from lynn.events import bind_room, reset_events
from lynn.hero import DIR_UP, ctor_hero, hero_walk_step, place_hero, try_same_map_room_teleport
from lynn.macros import quad_calc
from lynn.macros import testbit as ll_testbit
from lynn.map.collision import (
    check_against,
    check_against_entities,
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
    hero.unique_id = 0
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


def test_opened_chest_stays_solid():
    """FB check_against: dead chest/bluechest still blocks; other dead props do not."""
    from lynn.constants import u_bluechest, u_chest
    from lynn.object.seq_funcs import __cripple, __make_dead
    from lynn.object.xml_load import LLSystem_ObjectFromXML

    m, hero, room = _hero_at_entry()
    chest = CharType()
    chest.id = "data/object/chest.xml"
    chest = LLSystem_ObjectFromXML(chest, load_images=False)
    assert chest.unique_id == u_chest
    chest.num = 3
    chest.coords_x = hero.coords_x
    chest.coords_y = hero.coords_y - 16
    hero.direction = 0
    assert check_against(hero, chest, 0) == 1
    __make_dead(chest)
    __cripple(chest)
    assert chest.dead != 0
    assert chest.impassable == 0
    assert check_against(hero, chest, 0) == 1
    x0, y0 = hero.coords_x, hero.coords_y
    assert move_object(hero, room, moment=1, others=[chest]) == 0
    assert (hero.coords_x, hero.coords_y) == (x0, y0)

    blue = CharType()
    blue.id = "data/object/bluechest.xml"
    blue = LLSystem_ObjectFromXML(blue, load_images=False)
    assert blue.unique_id == u_bluechest
    blue.num = 4
    blue.coords_x = hero.coords_x
    blue.coords_y = hero.coords_y - 16
    __make_dead(blue)
    __cripple(blue)
    assert check_against(hero, blue, 0) == 1

    corpse = CharType()
    corpse.num = 5
    corpse.dead = 1
    corpse.impassable = 0
    corpse.perimeter_x = 16
    corpse.perimeter_y = 16
    corpse.coords_x = hero.coords_x
    corpse.coords_y = hero.coords_y - 16
    assert check_against(hero, corpse, 0) == 0


def test_npc_cannot_walk_onto_hero():
    from lynn.events import bind_hero, bind_hero_only, reset_events
    from lynn.hero import ctor_hero_only

    reset_events()
    m, hero, room = _hero_at_entry()
    bind_hero(hero)
    bind_hero_only(ctor_hero_only())
    npc = CharType()
    npc.num = 1
    npc.impassable = 1
    npc.perimeter_x = 16
    npc.perimeter_y = 16
    npc.coords_x = hero.coords_x
    npc.coords_y = hero.coords_y - 16
    npc.direction = 2
    assert check_against(npc, hero, 2) == 1
    x0, y0 = npc.coords_x, npc.coords_y
    assert move_object(npc, room, moment=1, others=[]) == 0
    assert (npc.coords_x, npc.coords_y) == (x0, y0)
    assert check_against_entities(npc, 2, []) == 1


def test_unstoppable_object_does_not_stop_an_impassable_mover():
    """FB check_against: either side's unstoppable_by_object cancels the block."""
    mover = CharType()
    mover.num = 1
    mover.impassable = 1
    mover.perimeter_x = 16
    mover.perimeter_y = 16
    mover.coords_x = 3936
    mover.coords_y = 1600
    prop = CharType()
    prop.num = 2
    prop.unstoppable_by_object = 1
    prop.perimeter_x = 16
    prop.perimeter_y = 16
    prop.coords_x = 3920
    prop.coords_y = 1600
    mover.direction = 3
    assert check_against(mover, prop, 3) == 0
    from lynn.map.types import RoomType

    room = RoomType()
    room.x = 400
    room.y = 200
    n = 400 * 201
    room.layout = [[0] * n for _ in range(3)]
    assert move_object(mover, room, moment=1, others=[prop]) != 0
    assert mover.coords_x == 3935


def test_sparkle_does_not_block_impassable_step():
    """FB check_against: u_sparkle never stops a mover (Gelidus pushrocks)."""
    from lynn.constants import u_pushrock, u_sparkle

    rock = CharType()
    rock.num = 1
    rock.unique_id = u_pushrock
    rock.impassable = 1
    rock.perimeter_x = 16
    rock.perimeter_y = 16
    rock.coords_x = 592
    rock.coords_y = 112
    spark = CharType()
    spark.num = 2
    spark.unique_id = u_sparkle
    spark.impassable = 0
    spark.perimeter_x = 16
    spark.perimeter_y = 16
    spark.coords_x = 592
    spark.coords_y = 96
    rock.direction = 0
    assert check_against(rock, spark, 0) == 0


def test_one_pixel_overlap_does_not_walk_through_book():
    """FB tests the stepped box. A 1px clip must not let catch-up steps cross."""
    from lynn.map.types import RoomType

    room = RoomType()
    room.x = 40
    room.y = 40
    n = 40 * 41 + 2
    room.layout = [[0] * n for _ in range(3)]
    hero = CharType()
    hero.num = -1
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.coords_x = 100
    hero.coords_y = 115
    book = CharType()
    book.num = 1
    book.impassable = -1
    book.perimeter_x = 16
    book.perimeter_y = 16
    book.coords_x = 100
    book.coords_y = 100
    hero.direction = 0
    assert check_against(hero, book, 0) == 1
    y0 = hero.coords_y
    for _ in range(8):
        hero.direction = 0
        if move_object(hero, room, moment=1, others=[book]) == 0:
            break
    assert hero.coords_y == y0
    hero.direction = 2
    assert move_object(hero, room, moment=1, others=[book]) != 0
    assert hero.coords_y == y0 + 1


def test_already_overlapping_npc_does_not_pin_hero():
    m, hero, room = _hero_at_entry()
    npc = CharType()
    npc.num = 1
    npc.impassable = 1
    npc.perimeter_x = 16
    npc.perimeter_y = 16
    npc.coords_x = hero.coords_x
    npc.coords_y = hero.coords_y
    hero.direction = 1
    x0 = hero.coords_x
    assert check_against(hero, npc, 1) == 0
    assert move_object(hero, room, moment=1, others=[npc]) != 0
    assert hero.coords_x == x0 + 1


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


def test_ignia_growl_chest_north_pad_does_not_bounce_out_of_backrooms():
    """Ignia r12 north tele (by the growling chest) lands on r17's return strip.

    resolve_landing nudges off that strip so the next frame does not bounce
    Lynn back to r12. That pad is the secret path toward the mace portal.
    """
    path = resolve_map_path("ignia")
    if path is None or not path.is_file():
        import pytest

        pytest.skip("ignia.map missing")
    m = load_mapV(str(path), load_tileset=False)
    hero = ctor_hero(load_images=False)
    north = m.room[12].teleport[2]
    assert north.to_map == ""
    assert north.to_room == 17
    ret = m.room[17].teleport[1]
    assert ret.to_room == 12
    hero.coords_x = north.x + 4
    hero.coords_y = north.y
    assert check_teleports(hero, m.room[12].teleport) == 2
    assert try_same_map_room_teleport(hero, m, 12) == 17
    assert (hero.coords_x, hero.coords_y) != (north.dx, north.dy)
    assert check_teleports(hero, m.room[17].teleport) == -1
    assert try_same_map_room_teleport(hero, m, 17) == 17
    # Exit south still works from the return strip.
    hero.coords_x = ret.x + 4
    hero.coords_y = ret.y - 8
    assert check_teleports(hero, m.room[17].teleport) == 1
    assert try_same_map_room_teleport(hero, m, 17) == 12
    assert check_teleports(hero, m.room[12].teleport) == -1


def test_ignia_maceget_return_clears_static_overlap():
    """Mace portal return (ignia entry 8) sits inside a walk-through static rock."""
    from lynn.demos import MapDemo, enter_map, set_up_room_enemies, try_hero_teleport
    from lynn.events import bind_hero, reset_events
    from lynn.gfx.palette import load_pal
    from lynn.map.collision import check_bounds
    from lynn.map.landing import resolve_landing
    from lynn.paths import data_file
    import lynn.events as events

    path = resolve_map_path("ignia")
    if path is None or not path.is_file():
        import pytest

        pytest.skip("ignia.map missing")
    reset_events()
    try:
        m = load_mapV(str(path), load_tileset=False)
        demo = MapDemo(
            palette=load_pal(data_file("palette", "ll.pal")),
            game_map=m,
            tile_surfs=[],
            load_images=0,
            load_tileset=0,
        )
        demo.objects_by_room = [[] for _ in m.room]
        set_up_room_enemies(demo, 14, load_images=False)
        demo.hero = ctor_hero(load_images=False)
        bind_hero(demo.hero)
        demo.hero_room = 14
        events.hero_room = 14
        events.map_filename = "ignia.map"
        portal = m.room[14].teleport[3]
        assert "maceget" in portal.to_map.replace("\\", "/").lower()
        demo.hero.coords_x = portal.x
        demo.hero.coords_y = portal.y
        try_hero_teleport(demo)
        assert "maceget" in demo.game_map.filename.replace("\\", "/").lower()
        back = demo.game_map.room[0].teleport[0]
        demo.hero.coords_x = back.x
        demo.hero.coords_y = back.y
        try_hero_teleport(demo)
        assert "ignia" in demo.game_map.filename.replace("\\", "/").lower()
        assert demo.hero_room == 14
        entry = m.entry[8]
        assert (entry.x, entry.y) == (248, 416)
        # Raw entry overlaps a static; resolve_landing must have nudged off it.
        assert (demo.hero.coords_x, demo.hero.coords_y) != (entry.x, entry.y)
        hb = (demo.hero.coords_x, demo.hero.coords_y, 16, 16)
        for obj in demo.objects_by_room[14]:
            ob = (obj.coords_x, obj.coords_y, obj.perimeter_x or 16, obj.perimeter_y or 16)
            assert check_bounds(hb, ob) != 0, obj.id
        assert check_teleports(demo.hero, demo.game_map.room[14].teleport) == -1

        # Unit: resolve_landing alone clears the known static at (256,416).
        demo.hero.coords_x = 248
        demo.hero.coords_y = 416
        assert resolve_landing(demo.hero, m.room[14], demo.objects_by_room[14])
        hb = (demo.hero.coords_x, demo.hero.coords_y, 16, 16)
        static = next(o for o in demo.objects_by_room[14] if o.coords_x == 256 and o.coords_y == 416)
        ob = (static.coords_x, static.coords_y, static.perimeter_x, static.perimeter_y)
        assert check_bounds(hb, ob) != 0
    finally:
        reset_events()


def test_forest_fall_map_tele_sets_to_map_and_entry():
    m, hero = _forest_fall()
    nerme = m.room[0].teleport[1]
    assert nerme.to_map
    hero.coords_x = nerme.x - 8
    hero.coords_y = nerme.y - 8
    assert check_teleports(hero, m.room[0].teleport) == 1
    assert check_against_teles(hero, m.room[0]) == 1
    assert hero.to_map == nerme.to_map
    assert hero.to_entry == nerme.to_room
    x0, y0 = hero.coords_x, hero.coords_y
    assert try_same_map_room_teleport(hero, m, 0) == 0
    assert (hero.coords_x, hero.coords_y) == (x0, y0)


def test_town_door_slides_into_the_opening():
    """FB check_psf: 1px off the doorway gap, holding up slides into the tele."""
    reset_events()
    m, hero = _forest_fall()
    room = m.room[4]
    bind_room(room, [])
    door = room.teleport[3]
    assert door.to_map.replace("\\", "/").endswith("inhouse.map")
    hero.coords_x = door.x
    hero.coords_y = door.y + 6
    hero.direction = DIR_UP
    hit = False
    for i in range(40):
        clock.timer = i * 0.02
        hero_walk_step(hero, room, DIR_UP, [])
        if check_teleports(hero, room.teleport) == 3:
            hit = True
            break
    assert hit
    assert hero.coords_x != door.x or hero.coords_y != door.y + 6


def test_gen_frame_randomizes_static_rate():
    import lynn.object  # noqa: F401
    from lynn.object.dispatch import lookup_func
    from lynn.object.tick import tick_object
    from lynn.object.xml_load import spawn_from_stub
    from types import SimpleNamespace

    assert lookup_func("__gen_frame") is not lookup_func("__noop")
    stub = SimpleNamespace(
        id="data/object/static.xml",
        x_origin=0,
        y_origin=0,
        direction=0,
    )
    obj = spawn_from_stub(stub, load_images=False)
    assert obj.low_frame == 0.03
    assert obj.high_frame == 0.08
    tick_object(obj)
    rate = obj.animControl[0].rate
    assert obj.low_frame <= rate <= obj.high_frame
