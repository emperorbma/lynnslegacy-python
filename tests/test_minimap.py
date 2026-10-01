"""Dungeon minimap: .mni load, visits, door colors, camera. No display."""

import pytest

from lynn.constants import TRUE
from lynn.events import reset_events
from lynn.gfx.palette import load_pal
from lynn.map.loader import load_mapV
from lynn.map.minimap import (
    DOOR_BARRED,
    DOOR_FKEYLOCKED,
    DOOR_LOCKED,
    DOOR_OPEN,
    DOOR_STAIR,
    MiniDoor,
    MiniMap,
    MiniRoom,
    _palette_color,
    attach_minimap,
    close_minimap,
    door_color,
    floor_label,
    load_minimap,
    mark_visited,
    open_minimap,
    pan_minimap,
    step_floor,
    update_minimap_cam,
    visited_bytes,
)
from lynn.map.types import MapType, RoomType, TeleportType
from lynn.object.char import CharType
from lynn.object.save import SaveData, sequence_LoadGame, snapshot_save
from lynn.paths import resolve_data_path, resolve_map_path
import lynn.events as events


def _map(name: str):
    return load_mapV(str(resolve_map_path(name)), load_tileset=False)


def _box(name: str):
    box = type("Box", (), {})()
    box.game_map = _map(name)
    box.hero_room = 0
    box.minimap = None
    return box


@pytest.mark.parametrize("name", ["ignia", "gelidus", "moenia", "arx", "nerme", "divius"])
def test_mni_matches_map_rooms(name):
    game = _map(name)
    path = resolve_data_path(f"data/map/{name}.mni")
    assert path is not None
    mm = load_minimap(path, game.rooms)
    assert mm is not None
    assert len(mm.rooms) == game.rooms == len(game.room)
    floors = {room.floor for room in mm.rooms}
    assert floors
    assert min(floors) >= -8
    assert max(floors) <= 16
    ids = {door.id for room in mm.rooms for door in room.doors}
    assert ids
    assert ids <= {DOOR_OPEN, DOOR_LOCKED, DOOR_BARRED, DOOR_FKEYLOCKED, DOOR_STAIR}
    assert any(room.doors for room in mm.rooms)


def test_missing_mni_stays_closed():
    reset_events()
    try:
        assert load_minimap("data/map/icefield.mni", 1) is None
        ice = _box("icefield")
        assert ice.game_map.isDungeon != 0
        assert attach_minimap(ice, None) is None
        assert ice.minimap is None
        assert events.minimap is None
        forest = _box("forest_fall")
        assert forest.game_map.isDungeon == 0
        assert attach_minimap(forest, None) is None
    finally:
        reset_events()


def test_attach_restores_visits_and_marks_the_current_room():
    reset_events()
    try:
        box = _box("ignia")
        n = box.game_map.rooms
        visited = [0] * n
        visited[1] = 255
        box.hero_room = 4
        mm = attach_minimap(box, visited)
        assert mm is not None
        assert mm.rooms[1].has_visited
        assert mm.rooms[4].has_visited
        assert not mm.rooms[0].has_visited
        raw = visited_bytes(mm)
        assert raw[0] == 0
        assert raw[1] == 255
        assert raw[4] == 255
        assert events.minimap is mm

        short = _box("ignia")
        short.hero_room = 2
        mismatched = attach_minimap(short, [255])
        assert mismatched is not None
        assert mismatched.rooms[2].has_visited
        assert not mismatched.rooms[1].has_visited
    finally:
        reset_events()


def test_snapshot_writes_visits_only_while_a_minimap_is_attached(tmp_path, monkeypatch):
    from lynn.object.save import LLSystem_ReadSaveFile, LLSystem_WriteSaveFile

    reset_events()
    try:
        bare = snapshot_save(0)
        assert bare.rooms == 0
        assert bare.hasVisited == []
        box = _box("moenia")
        attach_minimap(box, None)
        mark_visited(box.minimap, 3)
        data = snapshot_save(1)
        assert data.rooms == box.game_map.rooms
        assert data.hasVisited[0] == 255
        assert data.hasVisited[3] == 255
        assert all(v in (0, 255) for v in data.hasVisited)
        monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
        LLSystem_WriteSaveFile("ll_save1.sav", 1)
        back = LLSystem_ReadSaveFile(str(tmp_path / "ll_save1.sav"))
        assert back is not None
        assert back.rooms == data.rooms
        assert back.hasVisited == data.hasVisited
    finally:
        reset_events()


def test_load_stashes_visits_for_the_next_map():
    reset_events()
    try:
        box = _box("gelidus")
        n = box.game_map.rooms
        save = SaveData(map="gelidus.map", rooms=n, hasVisited=[0] * n)
        save.hasVisited[5] = 255
        sequence_LoadGame(save)
        assert events.pending_visited == save.hasVisited
        box.hero_room = 1
        mm = attach_minimap(box, events.pending_visited)
        events.pending_visited = None
        assert mm.rooms[5].has_visited
        assert mm.rooms[1].has_visited
        assert not mm.rooms[0].has_visited
    finally:
        reset_events()


def test_door_color_follows_happen_flags():
    reset_events()
    try:
        assert door_color(MiniDoor(0, 0, (), DOOR_OPEN)) == 36
        assert door_color(MiniDoor(0, 0, (), DOOR_STAIR)) == 170
        assert door_color(MiniDoor(0, 0, (), 9)) is None
        locked = MiniDoor(0, 0, (3,), DOOR_LOCKED)
        assert door_color(locked) == 15
        events.now[3] = TRUE
        assert door_color(locked) == 36
        barred = MiniDoor(0, 0, (3, -1), DOOR_BARRED)
        assert door_color(barred) == 245
        both = MiniDoor(0, 0, (3, 4), DOOR_LOCKED)
        assert door_color(both) == 15
        events.now[4] = TRUE
        assert door_color(both) == 36
        assert door_color(MiniDoor(0, 0, (8,), DOOR_FKEYLOCKED)) == 27
    finally:
        reset_events()


def test_floor_label_matches_fb_str():
    assert floor_label(0) == "F 1"
    assert floor_label(2) == "F 3"
    assert floor_label(-1) == "B 1"
    assert floor_label(-2) == "B 2"


def test_camera_clamps_and_floors_step_through_gaps():
    small = MiniMap(rooms=(MiniRoom(0, 0, 0, ()),))
    game = MapType(room=[RoomType(x=20, y=20)], rooms=1)
    open_minimap(small, game, 0)
    assert small.open
    assert small.floor == 0
    assert small.focus == 0
    assert small.camera_x == 0
    assert small.camera_y == 0
    close_minimap(small, 0)
    assert not small.open

    wide = MiniMap(rooms=(MiniRoom(100, 50, 1, ()),))
    wide_map = MapType(room=[RoomType(x=400, y=300)], rooms=1)
    open_minimap(wide, wide_map, 0)
    assert wide.camera_x == 140
    assert wide.camera_y == 120
    wide.camera_x = 999
    wide.camera_y = 999
    update_minimap_cam(wide, wide_map)
    assert wide.camera_x == 180
    assert wide.camera_y == 190

    floors = MiniMap(
        rooms=(
            MiniRoom(0, 0, -1, ()),
            MiniRoom(0, 0, 0, ()),
            MiniRoom(0, 0, 2, ()),
        )
    )
    floors.floor = 2
    step_floor(floors, -1)
    assert floors.floor == 1
    step_floor(floors, -1)
    assert floors.floor == 0
    step_floor(floors, -1)
    assert floors.floor == -1
    step_floor(floors, -1)
    assert floors.floor == -1
    step_floor(floors, 1)
    step_floor(floors, 1)
    step_floor(floors, 1)
    assert floors.floor == 2
    step_floor(floors, 1)
    assert floors.floor == 2


def test_pan_is_gated_and_opposite_arrows_cancel():
    mm = MiniMap(rooms=(MiniRoom(0, 0, 0, ()),))
    mm.camera_x = 10
    mm.camera_y = 10
    mm.move_delay = 0
    pan_minimap(mm, 5.0, True, True, True, True)
    assert mm.camera_x == 10
    assert mm.camera_y == 10
    assert mm.move_delay == pytest.approx(5.023)
    pan_minimap(mm, 5.022, True, False, False, False)
    assert mm.camera_y == 10
    pan_minimap(mm, 5.024, True, False, False, False)
    assert mm.camera_y == 9


def test_same_map_teleport_marks_the_dest_room():
    from lynn.demos import try_hero_teleport

    reset_events()
    try:
        hero = CharType()
        hero.coords_x = 0
        hero.coords_y = 0
        hero.perimeter_x = 16
        hero.perimeter_y = 16
        room0 = RoomType(
            x=20,
            y=20,
            teleports=1,
            teleport=[TeleportType(x=0, y=0, w=32, h=32, to_room=1, to_map="", dx=8, dy=9)],
        )
        room1 = RoomType(x=20, y=20)
        game = MapType(rooms=2, room=[room0, room1])
        mm = MiniMap(rooms=(MiniRoom(0, 0, 0, ()), MiniRoom(10, 0, 0, ())))
        mm.rooms[0].has_visited = -1
        demo = type("Box", (), {})()
        demo.hero = hero
        demo.hero_room = 0
        demo.game_map = game
        demo.load_images = 0
        demo.load_tileset = 0
        demo.objects_by_room = [[], []]
        demo.minimap = mm
        try_hero_teleport(demo)
        assert demo.hero_room == 1
        assert hero.coords_x == 8
        assert hero.coords_y == 9
        assert mm.rooms[1].has_visited
    finally:
        reset_events()


def test_palette_zero_is_the_map_background():
    pal = load_pal("data/palette/ll.pal")
    assert _palette_color(pal, 0, 0) == pal.colors[0]
    assert max(pal.colors[0]) <= 32
