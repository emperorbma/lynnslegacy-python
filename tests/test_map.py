import pytest

from lynn.map.loader import load_mapV
from lynn.paths import DEFAULT_MAP, resolve_map_path, project_root

DATA = project_root() / "data" / "map"
PARSE_MAPS = ["island3.map", "title.map", "inhouse.map", "valley.map"]


def test_resolve_map_default_is_current():
    assert resolve_map_path(None).name.lower() == DEFAULT_MAP
    assert resolve_map_path("island3").name.lower() == "island3.map"


@pytest.mark.parametrize("name", PARSE_MAPS)
def test_map_parses_three_layers(name):
    path = DATA / name
    if not path.is_file():
        pytest.skip(f"{name} missing")
    m = load_mapV(str(path), load_tileset=False)
    assert m.rooms >= 1
    assert m.entries >= 1
    assert m.bytes_remaining in (0, 2)
    room = m.room[0]
    assert len(room.layout) == 3
    assert room.room_elem == room.x * (room.y + 1) + 1
    for layer in room.layout:
        assert len(layer) == room.room_elem + 1


def test_selected_map_parses(map_path):
    m = load_mapV(str(map_path), load_tileset=False)
    assert m.rooms >= 1
    assert len(m.room[0].layout) == 3


def test_island3_header_and_spawn():
    path = resolve_map_path("island3")
    if not path.is_file():
        pytest.skip("island3.map missing")
    m = load_mapV(str(path), load_tileset=False)
    assert m.tileset_filename.replace("\\", "/").lower().endswith("tiles/island.spr")
    entry = m.entry[0]
    assert entry.room == 0
    assert entry.x > 160
    assert entry.y > 100
