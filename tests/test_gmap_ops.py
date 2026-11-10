"""Unit tests for gmap mutation helpers."""

from lynn.gmap import ops
from lynn.map.types import CommandData, CommandType, RoomType, SequenceType, TeleportType


def _room(w=8, h=6, fill=1) -> RoomType:
    room = RoomType(x=w, y=h)
    n = ops.layer_len(w, h)
    room.layout = [[fill] * n for _ in range(3)]
    room.room_elem = w * (h + 1) + 1
    return room


def test_flood_fill_replaces_region():
    room = _room()
    # Checker: paint a 2x2 blob of tile 5.
    for y in range(2):
        for x in range(2):
            room.layout[0][y * room.x + x] = 5
    n = ops.flood_fill(room, 0, 0, 0, 9)
    assert n == 4
    assert room.layout[0][0] & 0xFF == 9
    assert room.layout[0][1] & 0xFF == 9
    assert room.layout[0][room.x] & 0xFF == 9
    # Untouched cell stays 1.
    assert room.layout[0][2] & 0xFF == 1


def test_flood_fill_noop_same_brush():
    room = _room(fill=3)
    assert ops.flood_fill(room, 0, 1, 1, 3) == 0


def test_layer_fill():
    room = _room(fill=0)
    ops.layer_fill(room, 1, 7)
    assert all((v & 0xFF) == 7 for v in room.layout[1])
    assert all((v & 0xFF) == 0 for v in room.layout[0])


def test_redimension_copies_overlap():
    room = _room(4, 4, fill=2)
    room.layout[0][0] = 11
    room.layout[0][1] = 12
    ops.redimension_room(room, 6, 3, fill_tile=0)
    assert room.x == 6 and room.y == 3
    assert room.layout[0][0] == 11
    assert room.layout[0][1] == 12
    # New cells beyond old width on row 0 are fill.
    assert room.layout[0][5] == 0


def test_macro_stamp_and_capture():
    room = _room(10, 10, fill=0)
    cells = [(i % 7) + 1 for i in range(36)]
    ops.stamp_macro(room, 0, 1, 1, cells)
    assert room.layout[0][1 * 10 + 1] & 0xFF == 1
    captured = ops.capture_macro(room, 0, 1, 1)
    assert captured == cells


def test_teleport_add_delete():
    room = _room()
    room.teleport = []
    room.teleports = 0
    tp = ops.add_teleport(room)
    assert isinstance(tp, TeleportType)
    assert room.teleports == 1
    ops.delete_teleport(room, 0)
    assert room.teleports == 0


def test_sequence_add_command_block():
    room = _room()
    room.seq = []
    room.seq_here = 0
    seq = ops.add_sequence(room)
    assert room.seq_here == 1
    cmd = ops.add_command(seq)
    assert seq.commands == 1
    assert isinstance(cmd.ent[0], CommandData)
    ops.add_command_block(cmd)
    assert cmd.ents == 2
    ops.delete_command_block(cmd, 0)
    assert cmd.ents == 1
    ops.delete_command(seq, 0)
    assert seq.commands == 0
    ops.delete_sequence(room, 0)
    assert room.seq_here == 0


def test_toggle_quad_corners():
    room = _room(4, 4, fill=0)
    # Half-tile (0,0) → upper-left of tile 0,0
    ops.toggle_quad(room, 0, 0, 0)
    assert room.layout[0][0] & ops.UPPER_LEFT
    ops.toggle_quad(room, 0, 1, 0)
    assert room.layout[0][0] & ops.UPPER_RIGHT
    ops.toggle_quad(room, 0, 0, 1)
    assert room.layout[0][0] & ops.LOWER_LEFT
    ops.toggle_quad(room, 0, 1, 1)
    assert room.layout[0][0] & ops.LOWER_RIGHT
    # Toggle off.
    ops.toggle_quad(room, 0, 0, 0)
    assert room.layout[0][0] & ops.UPPER_LEFT == 0


def test_toggle_and_clear_ice():
    room = _room(4, 4, fill=3)
    ops.toggle_ice(room, 1, 1)
    assert room.layout[0][1 * 4 + 1] & ops.TILE_ICE
    ops.clear_layer_ice(room, fill=True)
    assert all(v & ops.TILE_ICE for v in room.layout[0][: room.x * room.y])
    ops.clear_layer_ice(room, fill=False)
    assert all(v & ops.TILE_ICE == 0 for v in room.layout[0])


def test_add_enemy_and_room():
    from lynn.map.types import MapType

    room = _room()
    stub = ops.add_enemy(room, "statue", 32, 48)
    assert room.enemies == 1
    assert "statue" in stub.id.replace("\\", "/")
    assert stub.x_origin == 32
    ops.delete_enemy(room, 0)
    assert room.enemies == 0

    m = MapType(rooms=1, room=[room])
    ops.add_room(m, x=10, y=8)
    assert m.rooms == 2
    assert m.room[1].x == 10 and m.room[1].y == 8
    ops.delete_room(m, 1)
    assert m.rooms == 1
