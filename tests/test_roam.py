import lynn.object  # noqa: F401

from lynn import clock
from lynn.events import bind_room
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.move_ai import __randomize_path
from lynn.object.tick import tick_objects
from lynn.object.time_procs import __second_pause
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import resolve_map_path


def test_second_pause_elapses():
    o = CharType()
    clock.timer = 10.0
    assert __second_pause(o) == 0
    clock.timer = 10.5
    assert __second_pause(o) == 0
    clock.timer = 11.0
    assert __second_pause(o) == 1


def test_randomize_path_sets_cardinal_dir():
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    room = m.room[1]
    o = CharType()
    o.walk_length = 40
    o.perimeter_x = 16
    o.perimeter_y = 8
    o.coords_x = 160
    o.coords_y = 280
    bind_room(room, [o])
    assert __randomize_path(o) == 1
    assert o.direction in (0, 1, 2, 3)
    assert o.walk_buffer > 0


def test_room1_roamer_changes_coords():
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    room = m.room[1]
    roamers = []
    for stub in room.enemy:
        if not stub.id.replace("\\", "/").endswith("roamer.xml"):
            continue
        obj = spawn_from_stub(stub, load_images=False)
        roamers.append(obj)
    assert roamers
    bind_room(room, roamers)
    start = [(o.coords_x, o.coords_y) for o in roamers]
    for i in range(400):
        clock.timer = i * 0.06
        tick_objects(roamers)
    end = [(o.coords_x, o.coords_y) for o in roamers]
    assert start != end


def test_moenia_bats_change_coords():
    from lynn.object.dispatch import lookup_func

    m = load_mapV(str(resolve_map_path("moenia")), load_tileset=False)
    room = m.room[0]
    bats = []
    for stub in room.enemy:
        if not stub.id.replace("\\", "/").endswith("bat.xml"):
            continue
        obj = spawn_from_stub(stub, load_images=False)
        bats.append(obj)
    assert bats
    assert lookup_func("__bat_path") is not lookup_func("__noop")
    bind_room(room, bats)
    start = [(o.coords_x, o.coords_y) for o in bats]
    for i in range(800):
        clock.timer = i * 0.05
        tick_objects(bats)
    end = [(o.coords_x, o.coords_y) for o in bats]
    assert start != end


def test_offscreen_enemy_stays_frozen_until_the_camera_reaches_it():
    from lynn.map.types import RoomType

    room = RoomType()
    room.x = 200
    room.y = 200
    room.layout = [[0] * (room.x * (room.y + 1) + 2) for _ in range(3)]
    near = spawn_from_stub(
        type("S", (), {"id": "data/object/roamer.xml", "x_origin": 160, "y_origin": 100, "direction": 1})(),
        load_images=False,
    )
    far = spawn_from_stub(
        type("S", (), {"id": "data/object/roamer.xml", "x_origin": 2000, "y_origin": 2000, "direction": 1})(),
        load_images=False,
    )
    boss = spawn_from_stub(
        type("S", (), {"id": "data/object/roamer.xml", "x_origin": 2000, "y_origin": 1800, "direction": 1})(),
        load_images=False,
    )
    boss.isBoss = -1
    shooter = spawn_from_stub(
        type("S", (), {"id": "data/object/roamer.xml", "x_origin": 2000, "y_origin": 1600, "direction": 1})(),
        load_images=False,
    )
    shooter.proj_style = 1
    bind_room(room, [near, far, boss, shooter])
    clock.timer = 0.0
    for i in range(80):
        clock.timer = i * 0.06
        tick_objects([near, far, boss, shooter], (0, 0))
    assert (near.coords_x, near.coords_y) != (160, 100)
    assert (far.coords_x, far.coords_y) == (2000, 2000)
    assert (boss.coords_x, boss.coords_y) != (2000, 1800)
    assert (shooter.coords_x, shooter.coords_y) != (2000, 1600)


def test_trigger_projectile_sets_active():
    from lynn.constants import PROJECTILE_ORB
    from lynn.object.dispatch import lookup_func

    ghost = CharType()
    ghost.id = "data/object/poltergeist.xml"
    from lynn.object.xml_load import LLSystem_ObjectFromXML

    LLSystem_ObjectFromXML(ghost, load_images=False)
    ghost.direction = 1
    ghost.coords_x = 80
    ghost.coords_y = 80
    lookup_func("__trigger_projectile")(ghost)
    assert ghost.projectile is not None
    assert ghost.projectile.active == PROJECTILE_ORB
    lookup_func("__do_proj")(ghost)
    assert ghost.projectile.travelled >= 1
    assert ghost.projectile.coords[0] != [0, 0]
