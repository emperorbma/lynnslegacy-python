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
