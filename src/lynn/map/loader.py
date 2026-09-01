"""FB ll_build.bas load_mapV / load_seqV. Uncompressed maps only."""

from __future__ import annotations

from pathlib import Path

from lynn.gfx.image import LLSystem_ImageLoad
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
from lynn.vfile import VFile

_DUNGEONS = (
    ("moenia", "Moenia"),
    ("gelidus", "Gelidus"),
    ("icefield", "Ice Field"),
    ("ignia", "Ignia"),
    ("arx", "Arx"),
    ("nerme", "Nerme"),
    ("divius", "Divius"),
)


def load_seqV(vf: VFile, num_seqs: int, seq_type: str, seq_index: int) -> list[SequenceType]:
    seqs: list[SequenceType] = []
    if num_seqs == 0:
        return seqs
    for grab_seq in range(num_seqs):
        sequence = SequenceType(seq_type=seq_type, seq_index=seq_index)
        sequence.ents = vf.i32()
        sequence.ent_code = [vf.i32() for _ in range(sequence.ents)]
        sequence.commands = vf.i32()
        for _ in range(sequence.commands):
            command = CommandType()
            command.ents = vf.i32()
            for _ in range(command.ents):
                cd = CommandData()
                cd.active_ent = vf.i32()
                cd.ent_state = vf.i32()
                cd.hold_state = cd.ent_state
                cd.text = vf.hstring()
                cd.walk_speed = vf.f64()
                cd.dest_y = vf.s16()
                cd.dest_x = vf.s16()
                cd.abs_x = vf.s16()
                cd.abs_y = vf.s16()
                cd.mod_y = vf.s16()
                cd.mod_x = vf.s16()
                cd.to_map = vf.hstring()
                cd.to_entry = vf.i32()
                cd.jump_count = vf.i32()
                cd.water_align = vf.i32()
                cd.chap = vf.i32()
                cd.carries_all = vf.i32()
                cd.nocam = vf.i32()
                cd.modify_direction = vf.i32()
                cd.seq_pause = vf.i32()
                cd.reserved_3 = vf.i32()
                cd.reserved_4 = vf.i32()
                cd.free_to_move = vf.i32()
                cd.display_hud = vf.i32()
                cd.fadeTime = vf.f64()
                cd.reserved_9 = vf.i32()
                cd.reserved_10 = vf.i32()
                command.ent.append(cd)
            sequence.Command.append(command)
        seqs.append(sequence)
    return seqs


def _mark_dungeon(m: MapType) -> None:
    name = m.filename.lower()
    for needle, label in _DUNGEONS:
        if needle in name:
            m.isDungeon = -1
            m.dungeonName = label
            return


def load_mapV(file_name: str, load_tileset: bool = True) -> MapType:
    path = Path(file_name)
    vf = VFile(path.read_bytes())
    m = MapType()
    m.filename = vf.hstring()
    _mark_dungeon(m)
    m.entries = vf.i32()
    m.rooms = vf.i32()
    m.tileset_filename = vf.hstring()
    if load_tileset and m.tileset_filename:
        m.tileset = LLSystem_ImageLoad(m.tileset_filename)

    for room_index in range(m.rooms):
        room = RoomType()
        room.x = vf.i32()
        room.y = vf.i32()
        room.parallax = vf.i32()
        if room.parallax != 0:
            room.para_filename = vf.hstring()
            if load_tileset and room.para_filename:
                room.para_img = LLSystem_ImageLoad(room.para_filename)
        room.dark = vf.i32()
        room.teleports = vf.i32()
        room.song = vf.i32()
        room.song_changes = vf.i32()
        room.changes_to = vf.i32()
        room.reserved = [vf.i32() for _ in range(18)]

        for _ in range(room.teleports):
            tp = TeleportType()
            tp.x = vf.i32()
            tp.y = vf.i32()
            tp.w = vf.i32()
            tp.h = vf.i32()
            tp.to_room = vf.i32()
            tp.to_map = vf.hstring()
            tp.dx = vf.i32()
            tp.dy = vf.i32()
            tp.dd = vf.i32()
            tp.to_song = vf.i32()
            tp.reserved = [vf.i32() for _ in range(20)]
            room.teleport.append(tp)

        room.seq_here = vf.i32()
        room.seq = load_seqV(vf, room.seq_here, "room", room_index)

        room.enemies = vf.i32()
        for _ in range(room.enemies):
            enemy = MapEnemyStub()
            enemy.x_origin = vf.i32()
            enemy.y_origin = vf.i32()
            enemy.id = vf.hstring()
            enemy.direction = vf.i32()
            enemy.seq_here = vf.i32()
            enemy.spawn_h = vf.s16()
            enemy.is_h_set = vf.s16()
            enemy.chap = vf.i32()
            enemy.spawn_d = vf.i32()
            enemy.is_d_set = vf.i32()
            enemy.reserved_5 = vf.i32()
            enemy.seq = load_seqV(vf, enemy.seq_here, "enemy", len(room.enemy))
            enemy.spawn_cond = vf.i32()
            if enemy.spawn_cond != 0:
                info = ConditionalSpawn()
                info.wait_n = vf.i32()
                info.wait_spawn = [SpawnPair(vf.u16(), vf.i32()) for _ in range(info.wait_n)]
                info.kill_n = vf.i32()
                info.kill_spawn = [SpawnPair(vf.u16(), vf.i32()) for _ in range(info.kill_n)]
                info.active_n = vf.i32()
                info.active_spawn = [SpawnPair(vf.u16(), vf.i32()) for _ in range(info.active_n)]
                enemy.spawn_info = info
            room.enemy.append(enemy)

        # FB: Redim uShort (x*(y+1)+1) → ubound+1 values per layer.
        room.room_elem = room.x * (room.y + 1) + 1
        layer_len = room.room_elem + 1
        room.layout = []
        for _layer in range(3):
            room.layout.append([vf.s16() & 0xFFFF for _ in range(layer_len)])
        m.room.append(room)

    for entry_index in range(m.entries):
        entry = MapEntryType()
        entry.x = vf.i32()
        entry.y = vf.i32()
        entry.room = vf.i32()
        entry.direction = vf.u8()
        entry.seq_here = vf.i32()
        entry.reserved = vf.raw(84)
        entry.seq = load_seqV(vf, entry.seq_here, "entry", entry_index)
        m.entry.append(entry)

    m.bytes_remaining = vf.remaining()
    m.bytes_total = len(vf.data)
    return m


def LLSystem_LoadMap(file_name: str, load_tileset: bool = True) -> MapType:
    return load_mapV(file_name, load_tileset=load_tileset)
