"""Map-mutation helpers matching FB gmap_states / flood_fill."""

from __future__ import annotations

from lynn.map.types import (
    CommandData,
    CommandType,
    MapEntryType,
    MapType,
    RoomType,
    SequenceType,
    TeleportType,
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
    """Stamp a 6×6 macro (36 cells, row-major) at tile tx,ty on layer."""
    if len(cells) < 36 or layer < 0 or layer >= len(room.layout):
        return
    layout = room.layout[layer]
    for row in range(6):
        for col in range(6):
            x, y = tx + col, ty + row
            if x < 0 or y < 0 or x >= room.x or y >= room.y:
                continue
            idx = y * room.x + x
            if idx >= len(layout):
                continue
            tile = cells[row * 6 + col] & 0xFF
            layout[idx] = (layout[idx] & 0xFF00) | tile


def capture_macro(room: RoomType, layer: int, tx: int, ty: int) -> list[int]:
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
                    cells[row * 6 + col] = layout[idx] & 0xFF
    return cells


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


def add_entry(m: MapType) -> MapEntryType:
    entry = MapEntryType(reserved=b"\x00" * 84)
    m.entry.append(entry)
    m.entries = len(m.entry)
    return entry
