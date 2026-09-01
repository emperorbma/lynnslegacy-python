import lynn.object  # noqa: F401
from lynn.events import bind_room
from lynn.map.collision import move_object
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.move_ai import __copter_path
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import resolve_map_path


def test_gcopter_xml_binds_copter_path():
    obj = CharType()
    obj.id = "data/object/gcopter.xml"
    LLSystem_ObjectFromXML(obj, load_images=False)
    assert obj.hp == 2
    assert obj.strength == 2
    assert obj.uni_directional == 1
    assert obj.walk_length == 80
    assert lookup_func("__copter_path") is __copter_path
    assert obj.funcs.func[0][7] is __copter_path


def test_copter_path_picks_8_dir():
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    room = m.room[2]
    o = CharType()
    o.walk_length = 80
    o.perimeter_x = 32
    o.perimeter_y = 24
    o.coords_x = 200
    o.coords_y = 200
    o.unstoppable_by_tile = -1
    o.unstoppable_by_screen = -1
    bind_room(room, [o])
    assert __copter_path(o) == 1
    assert 0 <= o.direction <= 7
    assert o.walk_buffer == 80


def test_move_object_diagonal_up_right():
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    room = m.room[2]
    o = CharType()
    o.perimeter_x = 16
    o.perimeter_y = 16
    o.coords_x = 200
    o.coords_y = 200
    o.direction = 5
    o.unstoppable_by_tile = -1
    x0, y0 = o.coords_x, o.coords_y
    result = move_object(o, room, only_looking=0, moment=1)
    assert result != 0
    assert o.coords_x == x0 + 1
    assert o.coords_y == y0 - 1
