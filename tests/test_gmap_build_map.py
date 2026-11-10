"""Build a small gameplay-shaped map with gmap ops and prove it loads like a real one.

Modeled on fredhouse / inhouse room 0 conventions:
- 21×15 house interior
- floor + overlay tiles, walkable wall quads
- entry spawn, door teleport (cross-map), NPC enemy
- second linked room (like forest_fall room hops)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lynn.gmap import ops
from lynn.map.loader import load_mapV
from lynn.map.saver import save_mapV
from lynn.map.types import MapType
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import chdir_project_root, data_root, resolve_map_path


HOUSE_TILESET = "data/pictures/tiles/House.spr"
FLOOR_TILE = 6
WALL_TILE = 215
NPC_ID = "data/object/roamer.xml"
SAVEPOINT_ID = "data/object/savepoint.xml"


def _paint_floor(room, tile: int) -> None:
    ops.layer_fill(room, 0, tile)


def _paint_border_walls(room, tile: int) -> None:
    """Put wall graphics on layer 1 around the rim and mark walk quads solid."""
    layout1 = room.layout[1]
    for x in range(room.x):
        for y in (0, room.y - 1):
            idx = y * room.x + x
            layout1[idx] = (layout1[idx] & 0xFF00) | (tile & 0xFF)
            # All four quads blocked.
            layout1[idx] |= (
                ops.UPPER_LEFT | ops.UPPER_RIGHT | ops.LOWER_LEFT | ops.LOWER_RIGHT
            )
    for y in range(room.y):
        for x in (0, room.x - 1):
            idx = y * room.x + x
            layout1[idx] = (layout1[idx] & 0xFF00) | (tile & 0xFF)
            layout1[idx] |= (
                ops.UPPER_LEFT | ops.UPPER_RIGHT | ops.LOWER_LEFT | ops.LOWER_RIGHT
            )


def _build_cottage_map() -> MapType:
    """Assemble a two-room cottage similar to inhouse/fredhouse + an inner hall."""
    m = MapType()
    m.filename = "data/map/test_cottage.map"
    m.tileset_filename = HOUSE_TILESET

    # Room 0: main interior (fredhouse / inhouse size).
    r0 = ops.add_room(m, x=21, y=15, fill_tile=0)
    r0.song = 10
    _paint_floor(r0, FLOOR_TILE)
    _paint_border_walls(r0, WALL_TILE)
    # Doorway gap at bottom center (clear walk on that tile).
    door_x, door_y = 10, 14
    door_idx = door_y * r0.x + door_x
    r0.layout[1][door_idx] = 0
    # A little ice puddle for the ice bit path.
    ops.toggle_ice(r0, 5, 5)
    ops.toggle_ice(r0, 6, 5)

    ops.add_enemy(r0, NPC_ID, x=256, y=144)
    r0.enemy[0].direction = 2
    ops.add_enemy(r0, SAVEPOINT_ID, x=160, y=120)

    # Door tele out to forest_fall style overworld (like inhouse → forest_fall).
    tp = ops.add_teleport(r0)
    tp.x, tp.y, tp.w, tp.h = 160, 216, 16, 1
    tp.to_map = "forest_fall.map"
    tp.to_room = 4
    tp.dx, tp.dy, tp.dd = 104, 80, 0
    tp.to_song = 13

    # Side tele into room 1.
    tp2 = ops.add_teleport(r0)
    tp2.x, tp2.y, tp2.w, tp2.h = 320, 100, 2, 32
    tp2.to_room = 1
    tp2.dx, tp2.dy, tp2.dd = 24, 112, 1

    entry = ops.add_entry(m, room_i=0)
    entry.x, entry.y, entry.direction = 256, 168, 0
    # Entry sequence with a one-liner (fredhouse/inhouse often have seq_here=1).
    seq = ops.add_sequence(entry)
    cmd = ops.add_command(seq)
    block = cmd.ent[0]
    block.text = "Welcome home."
    block.chap = 1

    # Room 1: linked hall.
    r1 = ops.add_room(m, x=21, y=15, fill_tile=FLOOR_TILE)
    r1.song = 10
    _paint_border_walls(r1, WALL_TILE)
    ops.add_enemy(r1, "data/object/statue.xml", x=200, y=100)
    r1.enemy[0].direction = 2
    back = ops.add_teleport(r1)
    back.x, back.y, back.w, back.h = 0, 100, 2, 32
    back.to_room = 0
    back.dx, back.dy, back.dd = 300, 112, 3

    entry2 = ops.add_entry(m, room_i=1)
    entry2.x, entry2.y, entry2.direction = 32, 112, 1

    m.rooms = len(m.room)
    m.entries = len(m.entry)
    return m


def test_built_cottage_matches_gameplay_shape():
    chdir_project_root()
    ref = load_mapV(str(resolve_map_path("fredhouse.map")), load_tileset=False)
    m = _build_cottage_map()

    assert m.rooms == 2
    assert m.entries == 2
    assert m.tileset_filename.replace("\\", "/").lower().endswith("house.spr")

    r0 = m.room[0]
    assert (r0.x, r0.y) == (ref.room[0].x, ref.room[0].y) == (21, 15)
    assert r0.song == ref.room[0].song == 10
    assert r0.enemies >= 2
    assert r0.teleports >= 2
    assert (r0.layout[0][0] & 0xFF) == FLOOR_TILE
    assert r0.layout[0][5 * 21 + 5] & ops.TILE_ICE
    # Wall rim has walk bits.
    assert r0.layout[1][0] & ops.UPPER_LEFT
    assert r0.layout[1][door_idx := 14 * 21 + 10] == 0  # doorway gap

    # NPC facing down like frederic.
    npc = next(e for e in r0.enemy if "roamer" in e.id.replace("\\", "/"))
    assert npc.direction == 2
    assert npc.x_origin == 256 and npc.y_origin == 144

    # Cross-map door like inhouse/fredhouse.
    door = next(t for t in r0.teleport if t.to_map)
    assert "forest_fall" in door.to_map.replace("\\", "/")
    assert door.w == 16 and door.h == 1

    # Entry sequence present.
    assert m.entry[0].seq_here == 1
    assert m.entry[0].seq[0].Command[0].ent[0].text == "Welcome home."


def test_built_cottage_roundtrip_and_spawn(tmp_path: Path):
    chdir_project_root()
    m = _build_cottage_map()
    out = tmp_path / "test_cottage.map"
    save_mapV(out, m)

    again = load_mapV(str(out), load_tileset=True)
    assert again.tileset is not None
    assert again.rooms == 2
    assert again.entries == 2
    assert again.room[0].enemies == 2
    assert again.room[1].enemies == 1
    assert again.room[0].teleports == 2
    assert again.entry[0].seq_here == 1
    assert again.entry[0].seq[0].Command[0].ent[0].text == "Welcome home."
    assert again.room[0].enemy[0].direction == 2

    # Stubs must resolve to live objects the way real maps do.
    for stub in again.room[0].enemy:
        obj = spawn_from_stub(stub, load_images=False)
        assert obj is not None
        assert obj.id or obj.unique_id is not None
    statue = spawn_from_stub(again.room[1].enemy[0], load_images=False)
    assert "statue" in str(getattr(statue, "id", "")).lower() or statue.unique_id != 0


def test_built_cottage_loads_in_map_demo(tmp_path: Path):
    """Gameplay demo path must accept an editor-built map."""
    pygame = pytest.importorskip("pygame")
    chdir_project_root()
    # Display needed for convert_alpha when loading tiles/objects.
    pygame.display.init()
    try:
        pygame.display.set_mode((1, 1))
    except pygame.error:
        pytest.skip("no display for map demo load")

    m = _build_cottage_map()
    # Drop into data/map so resolve_map_path finds it by stem like real maps.
    dest = data_root() / "map" / "_test_cottage_built.map"
    try:
        save_mapV(dest, m)
        from lynn.demos import load_map_demo

        demo = load_map_demo(with_objects=True, map_path="_test_cottage_built")
        assert demo.game_map.rooms == 2
        assert len(demo.tile_surfs) > 0
        assert demo.hero is not None
        assert demo.hero_room == 0
        assert len(demo.objects_by_room[0]) == 2
        assert len(demo.objects_by_room[1]) == 1
    finally:
        if dest.exists():
            dest.unlink()
        pygame.display.quit()


def test_rebuild_fredhouse_skeleton_with_ops(tmp_path: Path):
    """Reproduce fredhouse's skeleton (1 room, 1 entry, 1 tele, 1 enemy) via ops."""
    chdir_project_root()
    ref = load_mapV(str(resolve_map_path("fredhouse.map")), load_tileset=False)
    rr = ref.room[0]
    re = ref.entry[0]
    rt = rr.teleport[0]
    ren = rr.enemy[0]

    m = MapType()
    m.tileset_filename = ref.tileset_filename
    room = ops.add_room(m, x=rr.x, y=rr.y, fill_tile=FLOOR_TILE)
    room.song = rr.song
    stub = ops.add_enemy(room, ren.id, ren.x_origin, ren.y_origin)
    stub.direction = ren.direction
    tp = ops.add_teleport(room)
    tp.x, tp.y, tp.w, tp.h = rt.x, rt.y, rt.w, rt.h
    tp.to_map, tp.to_room = rt.to_map, rt.to_room
    tp.dx, tp.dy, tp.dd = rt.dx, rt.dy, rt.dd
    entry = ops.add_entry(m, room_i=re.room)
    entry.x, entry.y, entry.direction = re.x, re.y, re.direction
    if re.seq_here:
        ops.add_sequence(entry)

    out = tmp_path / "fredhouse_skel.map"
    save_mapV(out, m)
    again = load_mapV(str(out), load_tileset=False)

    assert again.rooms == 1 and again.entries == 1
    assert again.room[0].x == rr.x and again.room[0].y == rr.y
    assert again.room[0].song == rr.song
    assert again.room[0].enemies == 1
    assert again.room[0].teleports == 1
    assert again.room[0].enemy[0].direction == ren.direction
    assert again.room[0].enemy[0].x_origin == ren.x_origin
    assert again.entry[0].x == re.x and again.entry[0].y == re.y
    assert again.entry[0].seq_here == 1
    assert "island" in again.room[0].teleport[0].to_map.replace("\\", "/")
