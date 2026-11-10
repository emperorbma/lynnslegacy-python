"""FB ll_build.bas save_mapV / save_seqV.

Writes the uncompressed map blob the Python loader expects (shipped `data/map`
files are already decompressed). FB's on-disk save zlib-wraps the same payload.
"""

from __future__ import annotations

from pathlib import Path

from lynn.map.types import MapType, SequenceType
from lynn.vfile import VFileWriter


def _disk_path(path: str | Path) -> str:
    return str(path).replace("/", "\\")


def save_seqV(vf: VFileWriter, seqs: list[SequenceType]) -> None:
    for sequence in seqs:
        vf.i32(sequence.ents)
        for code in sequence.ent_code[: sequence.ents]:
            vf.i32(code)
        # Pad if ent_code shorter than ents (corrupt/partial edits).
        for _ in range(max(0, sequence.ents - len(sequence.ent_code))):
            vf.i32(0)

        vf.i32(sequence.commands)
        for command in sequence.Command[: sequence.commands]:
            vf.i32(command.ents)
            for cd in command.ent[: command.ents]:
                vf.i32(cd.active_ent)
                vf.i32(cd.ent_state)
                vf.hstring(cd.text)
                vf.f64(cd.walk_speed)
                vf.s16(cd.dest_y)
                vf.s16(cd.dest_x)
                vf.s16(cd.abs_x)
                vf.s16(cd.abs_y)
                vf.s16(cd.mod_y)
                vf.s16(cd.mod_x)
                vf.hstring(cd.to_map)
                vf.i32(cd.to_entry)
                vf.i32(cd.jump_count)
                vf.i32(cd.water_align)
                vf.i32(cd.chap)
                vf.i32(cd.carries_all)
                vf.i32(cd.nocam)
                vf.i32(cd.modify_direction)
                vf.i32(cd.seq_pause)
                vf.i32(cd.reserved_3)
                vf.i32(cd.reserved_4)
                vf.i32(cd.free_to_move)
                vf.i32(cd.display_hud)
                vf.f64(cd.fadeTime)
                vf.i32(cd.reserved_9)
                vf.i32(cd.reserved_10)
            for _ in range(max(0, command.ents - len(command.ent))):
                # Minimal empty command_data block.
                vf.i32(0)
                vf.i32(0)
                vf.hstring("")
                vf.f64(0.0)
                for _s in range(6):
                    vf.s16(0)
                vf.hstring("")
                for _i in range(11):
                    vf.i32(0)
                vf.f64(0.0)
                vf.i32(0)
                vf.i32(0)


def map_to_bytes(m: MapType, filename: str | None = None) -> bytes:
    """Serialize to the uncompressed load_mapV payload."""
    vf = VFileWriter()
    cover = filename if filename is not None else m.filename
    vf.hstring(_disk_path(cover))
    vf.i32(m.entries)
    vf.i32(m.rooms)
    vf.hstring(_disk_path(m.tileset_filename))

    for room in m.room[: m.rooms]:
        vf.i32(room.x)
        vf.i32(room.y)
        vf.i32(room.parallax)
        if room.parallax != 0:
            vf.hstring(_disk_path(room.para_filename))
        vf.i32(room.dark)
        vf.i32(room.teleports)
        vf.i32(room.song)
        vf.i32(room.song_changes)
        vf.i32(room.changes_to)
        reserved = list(room.reserved) + [0] * 18
        for i in range(18):
            vf.i32(reserved[i])

        for tp in room.teleport[: room.teleports]:
            vf.i32(tp.x)
            vf.i32(tp.y)
            vf.i32(tp.w)
            vf.i32(tp.h)
            vf.i32(tp.to_room)
            vf.hstring(_disk_path(tp.to_map))
            vf.i32(tp.dx)
            vf.i32(tp.dy)
            vf.i32(tp.dd)
            vf.i32(tp.to_song)
            tp_res = list(tp.reserved) + [0] * 20
            for i in range(20):
                vf.i32(tp_res[i])

        vf.i32(room.seq_here)
        save_seqV(vf, room.seq[: room.seq_here])

        vf.i32(room.enemies)
        for enemy in room.enemy[: room.enemies]:
            vf.i32(enemy.x_origin)
            vf.i32(enemy.y_origin)
            vf.hstring(_disk_path(enemy.id))
            vf.i32(enemy.direction)
            vf.i32(enemy.seq_here)
            vf.s16(enemy.spawn_h)
            vf.s16(enemy.is_h_set)
            vf.i32(enemy.chap)
            vf.i32(enemy.spawn_d)
            vf.i32(enemy.is_d_set)
            vf.i32(enemy.reserved_5)
            save_seqV(vf, enemy.seq[: enemy.seq_here])
            vf.i32(enemy.spawn_cond)
            if enemy.spawn_cond != 0 and enemy.spawn_info is not None:
                info = enemy.spawn_info
                vf.i32(info.wait_n)
                for pair in info.wait_spawn[: info.wait_n]:
                    vf.u16(pair.code_index)
                    vf.i32(pair.code_state)
                vf.i32(info.kill_n)
                for pair in info.kill_spawn[: info.kill_n]:
                    vf.u16(pair.code_index)
                    vf.i32(pair.code_state)
                vf.i32(info.active_n)
                for pair in info.active_spawn[: info.active_n]:
                    vf.u16(pair.code_index)
                    vf.i32(pair.code_state)

        # FB: Redim uShort (x*(y+1)+1) → x*(y+1)+2 values per layer.
        layer_len = room.x * (room.y + 1) + 2
        for layer in range(3):
            layout = room.layout[layer] if layer < len(room.layout) else []
            for i in range(layer_len):
                val = layout[i] if i < len(layout) else 0
                # FB quickbuf is uShort; walk/ice bits live in the high nibble.
                vf.u16(val & 0xFFFF)

    for entry in m.entry[: m.entries]:
        vf.i32(entry.x)
        vf.i32(entry.y)
        vf.i32(entry.room)
        vf.u8(entry.direction)
        vf.i32(entry.seq_here)
        reserved = entry.reserved if entry.reserved else b"\x00" * 84
        if len(reserved) < 84:
            reserved = reserved + b"\x00" * (84 - len(reserved))
        vf.raw(reserved[:84])
        save_seqV(vf, entry.seq[: entry.seq_here])

    return vf.getvalue()


def save_mapV(filename: str | Path, smap: MapType) -> None:
    """FB save_mapV without the final zlib wrap (matches shipped Python maps)."""
    path = Path(filename)
    # Prefer a data\-relative cover string when under the project data tree.
    try:
        from lynn.paths import project_root

        rel = path.resolve().relative_to(project_root().resolve())
        cover = str(rel).replace("/", "\\")
    except Exception:
        cover = str(path).replace("/", "\\")
    path.write_bytes(map_to_bytes(smap, cover))
