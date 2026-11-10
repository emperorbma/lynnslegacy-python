"""Map-mutation helpers matching FB gmap_states / flood_fill."""

from __future__ import annotations

from lynn.map.types import (
    CommandData,
    CommandType,
    ConditionalSpawn,
    MapEnemyStub,
    MapEntryType,
    MapType,
    RoomType,
    SequenceType,
    SpawnPair,
    TeleportType,
)

# FB gmap_structs.bi
TILE_ICE = 1 << 8  # 256
LOWER_RIGHT = 1 << 12  # 4096
LOWER_LEFT = 1 << 13  # 8192
UPPER_RIGHT = 1 << 14  # 16384
UPPER_LEFT = 1 << 15  # 32768

COMMAND_DATA_FIELDS: tuple[str, ...] = (
    "active_ent",
    "ent_state",
    "text",
    "walk_speed",
    "dest_y",
    "dest_x",
    "abs_x",
    "abs_y",
    "mod_y",
    "mod_x",
    "to_map",
    "to_entry",
    "jump_count",
    "water_align",
    "chap",
    "carries_all",
    "nocam",
    "modify_direction",
    "seq_pause",
    "reserved_3",
    "reserved_4",
    "free_to_move",
    "display_hud",
    "fadeTime",
    "reserved_9",
    "reserved_10",
)


def layer_len(x: int, y: int) -> int:
    # FB: Redim uShort (x*(y+1)+1) → x*(y+1)+2 elements.
    return x * (y + 1) + 2


def flood_fill(room: RoomType, layer: int, tx: int, ty: int, new_tile: int) -> int:
    """FB flood_fill: replace contiguous start_color (full ushort) with brush tile index.

    Preserves high walk/ice bits on each cell; only the low byte becomes new_tile.
    Returns number of tiles changed.
    """
    if layer < 0 or layer >= len(room.layout):
        return 0
    if tx < 0 or ty < 0 or tx >= room.x or ty >= room.y:
        return 0
    layout = room.layout[layer]
    start_idx = ty * room.x + tx
    if start_idx >= len(layout):
        return 0
    start_color = layout[start_idx]
    target_low = new_tile & 0xFF
    # Matching FB: if start == c exactly, no-op. Compare low byte for paint intent
    # but FB compared full ushort to tile index (tile is 0-255). Use low-byte match.
    if (start_color & 0xFF) == target_low:
        return 0

    changed = 0
    stack = [(tx, ty)]
    seen: set[tuple[int, int]] = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen:
            continue
        if x < 0 or y < 0 or x >= room.x or y >= room.y:
            continue
        idx = y * room.x + x
        if idx >= len(layout):
            continue
        if (layout[idx] & 0xFF) != (start_color & 0xFF):
            continue
        seen.add((x, y))
        layout[idx] = (layout[idx] & 0xFF00) | target_low
        changed += 1
        stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    return changed


def layer_fill(room: RoomType, layer: int, tile: int) -> None:
    """FB handle_fill: set low byte of every cell on the active layer."""
    if layer < 0 or layer >= len(room.layout):
        return
    layout = room.layout[layer]
    low = tile & 0xFF
    for i in range(len(layout)):
        layout[i] = (layout[i] & 0xFF00) | low


def redimension_room(room: RoomType, new_x: int, new_y: int, fill_tile: int = 0) -> None:
    """FB redimension_room: resize layouts, fill, then copy overlapping tiles."""
    if new_x <= 0:
        new_x = room.x
    if new_y <= 0:
        new_y = room.y
    old_x, old_y = room.x, room.y
    old_layouts = [list(layer) for layer in room.layout]
    new_len = layer_len(new_x, new_y)
    low = fill_tile & 0xFF
    room.layout = [[low] * new_len for _ in range(3)]
    room.x = new_x
    room.y = new_y
    room.room_elem = new_x * (new_y + 1) + 1

    copy_x = min(old_x, new_x)
    copy_y = min(old_y, new_y)
    for layer in range(3):
        src = old_layouts[layer] if layer < len(old_layouts) else []
        dst = room.layout[layer]
        for ty in range(copy_y):
            for tx in range(copy_x):
                sidx = ty * old_x + tx
                didx = ty * new_x + tx
                if sidx < len(src) and didx < len(dst):
                    dst[didx] = src[sidx]


def stamp_macro(room: RoomType, layer: int, tx: int, ty: int, cells: list[int]) -> None:
    """Stamp a 6×6 macro at tile tx,ty (FB: full cell value; skip zeros)."""
    if len(cells) < 36 or layer < 0 or layer >= len(room.layout):
        return
    layout = room.layout[layer]
    for row in range(6):
        for col in range(6):
            cell = cells[row * 6 + col]
            if cell == 0:
                continue
            x, y = tx + col, ty + row
            if x < 0 or y < 0 or x >= room.x or y >= room.y:
                continue
            idx = y * room.x + x
            if idx >= len(layout):
                continue
            layout[idx] = cell & 0xFFFF


def capture_macro(room: RoomType, layer: int, tx: int, ty: int) -> list[int]:
    """Capture 6×6 including walk/ice high bits (for macro walk editing)."""
    cells = [0] * 36
    if layer < 0 or layer >= len(room.layout):
        return cells
    layout = room.layout[layer]
    for row in range(6):
        for col in range(6):
            x, y = tx + col, ty + row
            if 0 <= x < room.x and 0 <= y < room.y:
                idx = y * room.x + x
                if idx < len(layout):
                    cells[row * 6 + col] = layout[idx] & 0xFFFF
    return cells


def set_macro_cell(cells: list[int], col: int, row: int, tile: int) -> None:
    """Set one macro cell's low tile byte; preserve walk bits."""
    if not (0 <= col < 6 and 0 <= row < 6) or len(cells) < 36:
        return
    i = row * 6 + col
    cells[i] = (cells[i] & 0xFF00) | (tile & 0xFF)


def stamp_macro_block(
    cells: list[int],
    dest_col: int,
    dest_row: int,
    block: list[list[int]],
) -> None:
    """Stamp a 2D tileset block into the 6×6 macro grid (FB blockshift→macro)."""
    if len(cells) < 36 or not block:
        return
    for dy, row_tiles in enumerate(block):
        for dx, tile in enumerate(row_tiles):
            c, r = dest_col + dx, dest_row + dy
            if 0 <= c < 6 and 0 <= r < 6:
                set_macro_cell(cells, c, r, tile)


def toggle_macro_quad(cells: list[int], half_x: int, half_y: int) -> None:
    """FB macro walk edit: half-tile coords (0..11) xor one walk corner bit."""
    if len(cells) < 36:
        return
    if not (0 <= half_x < 12 and 0 <= half_y < 12):
        return
    col, row = half_x // 2, half_y // 2
    qx, qy = half_x & 1, half_y & 1
    bit = 1 << (15 - (qx + qy * 2))
    cells[row * 6 + col] ^= bit


def stamp_tile_block(
    room: RoomType,
    layer: int,
    tx: int,
    ty: int,
    block: list[list[int]],
) -> int:
    """Stamp a rectangular tileset selection onto the map. Returns cells written."""
    if layer < 0 or layer >= len(room.layout) or not block:
        return 0
    layout = room.layout[layer]
    n = 0
    for dy, row_tiles in enumerate(block):
        for dx, tile in enumerate(row_tiles):
            x, y = tx + dx, ty + dy
            if x < 0 or y < 0 or x >= room.x or y >= room.y:
                continue
            idx = y * room.x + x
            if idx >= len(layout):
                continue
            layout[idx] = (layout[idx] & 0xFF00) | (tile & 0xFF)
            n += 1
    return n


def make_null_map(
    tileset_filename: str = "data/pictures/tiles/ruins.spr",
    room_x: int = 20,
    room_y: int = 15,
) -> MapType:
    """FB make_null_map: empty map with one blank room and default tileset."""
    m = MapType(filename="", tileset_filename=tileset_filename)
    add_room(m, room_x, room_y, fill_tile=0)
    return m


def clear_macro(cells: list[int]) -> None:
    """FB Clear Macro — zero all 36 cells of the selected macro."""
    for i in range(min(36, len(cells))):
        cells[i] = 0


def _set_cell(layout: list[int], room: RoomType, x: int, y: int, tile: int, bits: int = 0) -> None:
    if x < 0 or y < 0 or x >= room.x or y >= room.y:
        return
    idx = y * room.x + x
    if idx >= len(layout):
        return
    layout[idx] = (tile & 0xFF) | bits


def wall_macro(room: RoomType, cells: list[int]) -> None:
    """FB macro_wall: stamp selected 6×6 as a room border on layer 1 with walk bits."""
    if len(cells) < 36 or room.x < 2 or room.y < 2 or len(room.layout) < 2:
        return
    layout = room.layout[1]
    # Ensure layer length covers the room.
    need = room.x * room.y
    if len(layout) < need:
        layout.extend([0] * (need - len(layout)))

    for top in range(room.x):
        _set_cell(layout, room, top, 0, cells[2])
        _set_cell(layout, room, top, 1, cells[8], LOWER_LEFT | LOWER_RIGHT)
    for right in range(room.y):
        _set_cell(layout, room, room.x - 2, right, cells[15], UPPER_LEFT | LOWER_LEFT)
        _set_cell(layout, room, room.x - 1, right, cells[16])
    for bottom in range(room.x):
        _set_cell(layout, room, bottom, room.y - 2, cells[20], UPPER_LEFT | UPPER_RIGHT)
        _set_cell(layout, room, bottom, room.y - 1, cells[26])
    for left in range(room.y):
        _set_cell(layout, room, 0, left, cells[12])
        _set_cell(layout, room, 1, left, cells[13], UPPER_RIGHT | LOWER_RIGHT)

    # Corners (FB overwrites after edges).
    _set_cell(layout, room, 0, 0, cells[0])
    _set_cell(layout, room, 1, 0, cells[1])
    _set_cell(layout, room, 0, 1, cells[6])
    _set_cell(layout, room, 1, 1, cells[7], LOWER_RIGHT)

    _set_cell(layout, room, room.x - 2, 0, cells[3])
    _set_cell(layout, room, room.x - 1, 0, cells[4])
    _set_cell(layout, room, room.x - 2, 1, cells[9], LOWER_LEFT)
    _set_cell(layout, room, room.x - 1, 1, cells[10])

    _set_cell(layout, room, 0, room.y - 2, cells[18])
    _set_cell(layout, room, 1, room.y - 2, cells[19], UPPER_RIGHT)
    _set_cell(layout, room, 0, room.y - 1, cells[24])
    _set_cell(layout, room, 1, room.y - 1, cells[25])

    _set_cell(layout, room, room.x - 2, room.y - 2, cells[21], UPPER_LEFT)
    _set_cell(layout, room, room.x - 1, room.y - 2, cells[22])
    _set_cell(layout, room, room.x - 2, room.y - 1, cells[27])
    _set_cell(layout, room, room.x - 1, room.y - 1, cells[28])


def add_teleport(room: RoomType) -> TeleportType:
    tp = TeleportType(x=0, y=0, w=16, h=16, reserved=[0] * 20)
    room.teleport.append(tp)
    room.teleports = len(room.teleport)
    return tp


def delete_teleport(room: RoomType, index: int) -> None:
    if 0 <= index < len(room.teleport):
        del room.teleport[index]
        room.teleports = len(room.teleport)


def seq_list_for(m: MapType, room: RoomType, source: str, enemy_sel: int, entry_sel: int):
    """Return (seq list owner object attribute name path) as (list, setter_count_attr)."""
    if source == "enemy" and 0 <= enemy_sel < len(room.enemy):
        return room.enemy[enemy_sel]
    if source == "entry" and 0 <= entry_sel < len(m.entry):
        return m.entry[entry_sel]
    return room


def add_sequence(owner) -> SequenceType:
    seq = SequenceType()
    owner.seq.append(seq)
    owner.seq_here = len(owner.seq)
    return seq


def delete_sequence(owner, index: int) -> None:
    if 0 <= index < len(owner.seq):
        del owner.seq[index]
        owner.seq_here = len(owner.seq)


def add_command(seq: SequenceType) -> CommandType:
    cmd = CommandType(ents=1, ent=[CommandData()])
    seq.Command.append(cmd)
    seq.commands = len(seq.Command)
    return cmd


def delete_command(seq: SequenceType, index: int) -> None:
    if 0 <= index < len(seq.Command):
        del seq.Command[index]
        seq.commands = len(seq.Command)


def add_command_block(cmd: CommandType) -> CommandData:
    block = CommandData()
    cmd.ent.append(block)
    cmd.ents = len(cmd.ent)
    return block


def delete_command_block(cmd: CommandType, index: int) -> None:
    if 0 <= index < len(cmd.ent):
        del cmd.ent[index]
        cmd.ents = len(cmd.ent)


def add_entry(m: MapType, room_i: int = 0) -> MapEntryType:
    entry = MapEntryType(room=room_i, reserved=b"\x00" * 84)
    m.entry.append(entry)
    m.entries = len(m.entry)
    return entry


def delete_entry(m: MapType, index: int) -> None:
    if 0 <= index < len(m.entry):
        del m.entry[index]
        m.entries = len(m.entry)


def toggle_quad(room: RoomType, layer: int, half_x: int, half_y: int) -> None:
    """FB map_ToggleQuad: half-tile (8px) coords toggle one walkable corner bit."""
    if layer < 0 or layer >= len(room.layout):
        return
    if half_x < 0 or half_y < 0 or half_x >= (room.x << 1) or half_y >= (room.y << 1):
        return
    tx = half_x >> 1
    ty = half_y >> 1
    if (half_y & 1) == 0:
        q = UPPER_RIGHT if (half_x & 1) else UPPER_LEFT
    else:
        q = LOWER_RIGHT if (half_x & 1) else LOWER_LEFT
    idx = ty * room.x + tx
    layout = room.layout[layer]
    if idx < len(layout):
        layout[idx] ^= q


def toggle_ice(room: RoomType, tx: int, ty: int) -> None:
    """FB handle_ice: xor tile_ice on layer 0."""
    if tx < 0 or ty < 0 or tx >= room.x or ty >= room.y or not room.layout:
        return
    idx = ty * room.x + tx
    layout = room.layout[0]
    if idx < len(layout):
        layout[idx] ^= TILE_ICE


def clear_layer_ice(room: RoomType, fill: bool = False) -> None:
    """FB clear_layer_ice: clear (fill=False) or set (fill=True) ice on layer 0."""
    if not room.layout:
        return
    layout = room.layout[0]
    for i in range(len(layout)):
        if fill:
            layout[i] |= TILE_ICE
        else:
            layout[i] &= ~TILE_ICE


def add_enemy(room: RoomType, object_id: str, x: int = 0, y: int = 0) -> MapEnemyStub:
    oid = object_id.replace("/", "\\")
    if not oid.lower().endswith(".xml"):
        oid = f"data\\object\\{oid}.xml"
    elif not oid.lower().startswith("data"):
        oid = f"data\\object\\{oid}"
    stub = MapEnemyStub(x_origin=x, y_origin=y, id=oid)
    room.enemy.append(stub)
    room.enemies = len(room.enemy)
    return stub


def delete_enemy(room: RoomType, index: int) -> None:
    if 0 <= index < len(room.enemy):
        del room.enemy[index]
        room.enemies = len(room.enemy)


def add_room(m: MapType, x: int = 20, y: int = 15, fill_tile: int = 0) -> RoomType:
    room = RoomType(x=x, y=y)
    n = layer_len(x, y)
    low = fill_tile & 0xFF
    room.layout = [[low] * n for _ in range(3)]
    room.room_elem = x * (y + 1) + 1
    room.reserved = [0] * 18
    m.room.append(room)
    m.rooms = len(m.room)
    return room


def delete_room(m: MapType, index: int) -> None:
    """FB handle_rooms delete: drop entries targeting the room, then renumber."""
    if m.rooms <= 1:
        return
    if not (0 <= index < len(m.room)):
        return
    m.entry = [e for e in m.entry if e.room != index]
    m.entries = len(m.entry)
    del m.room[index]
    m.rooms = len(m.room)
    for entry in m.entry:
        if entry.room > index:
            entry.room -= 1


def eyedrop_tile(room: RoomType, layer: int, tx: int, ty: int) -> int | None:
    if layer < 0 or layer >= len(room.layout):
        return None
    if tx < 0 or ty < 0 or tx >= room.x or ty >= room.y:
        return None
    idx = ty * room.x + tx
    layout = room.layout[layer]
    if idx >= len(layout):
        return None
    return layout[idx] & 0xFF


def toggle_walkable_line(
    room: RoomType, layer: int, x0: int, y0: int, x1: int, y1: int
) -> int:
    """FB toggle_walkable_line: toggle quads along a half-tile line (Bresenham)."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    count = 0
    while True:
        toggle_quad(room, layer, x, y)
        count += 1
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return count


def ensure_spawn_info(enemy: MapEnemyStub) -> ConditionalSpawn:
    if enemy.spawn_info is None:
        enemy.spawn_info = ConditionalSpawn()
    enemy.spawn_cond = -1
    return enemy.spawn_info


def clear_spawn_info(enemy: MapEnemyStub) -> None:
    enemy.spawn_cond = 0
    enemy.spawn_info = None


def resize_spawn_list(pairs: list[SpawnPair], n: int) -> list[SpawnPair]:
    n = max(0, n)
    if len(pairs) < n:
        pairs = list(pairs) + [SpawnPair() for _ in range(n - len(pairs))]
    else:
        pairs = list(pairs[:n])
    return pairs


ENEMY_STUB_FIELDS: tuple[str, ...] = (
    "direction",
    "chap",
    "spawn_h",
    "is_h_set",
    "spawn_d",
    "is_d_set",
    "reserved_5",
    "spawn_cond",
)

ROOM_PROP_FIELDS: tuple[str, ...] = (
    "song",
    "dark",
    "song_changes",
    "changes_to",
    "parallax",
)
