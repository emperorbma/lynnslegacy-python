"""Action callbacks for the FB-style gmap property panel."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from lynn.gmap import ops
from lynn.gmap.prompt import pick_list, prompt_int, prompt_text

FLOAT_FIELDS = frozenset({"walk_speed", "fadeTime"})
STRING_FIELDS = frozenset({"text", "to_map"})
SEQ_SOURCES = ("room", "enemy", "entry")


def make_actions(ctx: dict[str, Any]) -> dict[str, Callable[[], None]]:
    """ctx keys: st, flash, save, load, pick_object, pick_tileset, pick_parallax,
    open_map helpers already bound into those callables where needed.
    """

    def st():
        return ctx["st"]

    def flash(msg: str) -> None:
        ctx["flash"](msg)

    def dirty() -> None:
        st().dirty = True

    def set_int_field(obj, name: str, title: str | None = None) -> None:
        cur = int(getattr(obj, name))
        val = prompt_int(title or name, cur)
        if val is not None:
            setattr(obj, name, val)
            dirty()

    def edit_block_field(field: str) -> None:
        owner = ops.seq_list_for(
            st().game_map, st().room, st().seq_src, st().enemy_sel, st().entry_sel
        )
        if not owner.seq:
            return
        seq = owner.seq[min(st().seq_sel, len(owner.seq) - 1)]
        if not seq.Command:
            return
        cmd = seq.Command[min(st().seq_cmd_sel, len(seq.Command) - 1)]
        if not cmd.ent:
            return
        block = cmd.ent[min(st().seq_block_sel, len(cmd.ent) - 1)]
        cur = getattr(block, field)
        if field in STRING_FIELDS:
            val = prompt_text(field, str(cur), allow_empty=True)
            if val is not None:
                setattr(block, field, val)
                dirty()
        elif field in FLOAT_FIELDS:
            raw = prompt_text(field, str(cur), numeric=True, allow_empty=False)
            if raw is not None:
                try:
                    setattr(block, field, float(raw))
                    dirty()
                except ValueError:
                    flash(f"Bad float for {field}")
        else:
            val = prompt_int(field, int(cur))
            if val is not None:
                setattr(block, field, val)
                dirty()

    def edit_spawn_pair(attr: str) -> None:
        if not st().room.enemy:
            return
        enemy = st().room.enemy[st().enemy_sel]
        info = ops.ensure_spawn_info(enemy)
        pairs = getattr(info, attr)
        if not pairs:
            flash(f"{attr} empty — set count first")
            return
        pi = prompt_int(f"{attr} index", 0, minimum=0, maximum=len(pairs) - 1)
        if pi is None:
            return
        pair = pairs[pi]
        ci = prompt_int("code_index", pair.code_index)
        if ci is None:
            return
        cs = prompt_int("code_state", pair.code_state)
        if cs is None:
            return
        pair.code_index = ci & 0xFFFF
        pair.code_state = cs
        dirty()

    def resize_spawn(attr_n: str, attr_list: str) -> None:
        if not st().room.enemy:
            return
        enemy = st().room.enemy[st().enemy_sel]
        info = ops.ensure_spawn_info(enemy)
        n = prompt_int(attr_n, getattr(info, attr_n), minimum=0, maximum=64)
        if n is None:
            return
        setattr(info, attr_list, ops.resize_spawn_list(getattr(info, attr_list), n))
        setattr(info, attr_n, n)
        dirty()

    def do_layer_fill() -> None:
        ops.layer_fill(st().room, st().layer, st().brush)
        dirty()
        flash(f"Layer {st().layer} filled")

    def do_ice_clear() -> None:
        ops.clear_layer_ice(st().room, False)
        dirty()
        flash("Ice cleared")

    def do_ice_fill() -> None:
        ops.clear_layer_ice(st().room, True)
        dirty()
        flash("Ice filled")

    def enemy_field(name: str) -> None:
        if st().room.enemy:
            set_int_field(st().room.enemy[st().enemy_sel], name)

    def tele_field(name: str) -> None:
        if st().room.teleport:
            set_int_field(st().room.teleport[st().tele_sel], name)

    def do_entry_add() -> None:
        ops.add_entry(st().game_map, st().room_i)
        st().entry_sel = st().game_map.entries - 1
        dirty()
        flash("Entry added")

    def do_tele_add() -> None:
        ops.add_teleport(st().room)
        st().tele_sel = st().room.teleports - 1
        dirty()
        flash("Teleport added")

    def do_seq_add() -> None:
        owner = ops.seq_list_for(
            st().game_map, st().room, st().seq_src, st().enemy_sel, st().entry_sel
        )
        ops.add_sequence(owner)
        st().seq_sel = owner.seq_here - 1
        dirty()

    def do_macro_add() -> None:
        st().macros.append([st().brush & 0xFF] * 36)
        st().macro_sel = len(st().macros) - 1
        flash("Macro added")

    def do_macro_clear() -> None:
        if not st().macros:
            flash("No macros")
            return
        ops.clear_macro(st().macros[st().macro_sel])
        flash(f"Macro {st().macro_sel} cleared")

    def do_macro_wall() -> None:
        if not st().macros:
            flash("No macros")
            return
        ops.wall_macro(st().room, st().macros[st().macro_sel])
        dirty()
        flash("Wall macro applied (layer 1)")

    def do_room_add() -> None:
        ops.add_room(st().game_map)
        st().room_i = st().game_map.rooms - 1
        dirty()
        flash(f"Room {st().room_i} added")

    def do_layer_cycle() -> None:
        st().layer = (st().layer + 1) % 3
        flash(f"Layer {st().layer}")

    def do_toggle_zoom() -> None:
        st().zoom = 2 if st().zoom == 1 else 1
        flash(f"Zoom {st().zoom}x")

    def do_toggle_grid() -> None:
        st().show_grid = not st().show_grid

    def do_toggle_walk() -> None:
        st().show_walk = not st().show_walk

    def do_toggle_solo() -> None:
        st().solo = not st().solo

    actions: dict[str, Callable[[], None]] = {
        "jump_room": lambda: _jump_room(st(), flash),
        "room_song": lambda: set_int_field(st().room, "song"),
        "room_dark": lambda: set_int_field(st().room, "dark"),
        "room_song_changes": lambda: set_int_field(st().room, "song_changes"),
        "room_changes_to": lambda: set_int_field(st().room, "changes_to"),
        "room_parallax": lambda: ctx["pick_parallax"](),
        "layer_cycle": do_layer_cycle,
        "toggle_zoom": do_toggle_zoom,
        "toggle_grid": do_toggle_grid,
        "toggle_walk": do_toggle_walk,
        "toggle_solo": do_toggle_solo,
        "layer_fill": do_layer_fill,
        "load_tileset": lambda: ctx["pick_tileset"](),
        "redim": lambda: ctx["redim"](),
        "ice_clear": do_ice_clear,
        "ice_fill": do_ice_fill,
        "enemy_cycle": lambda: _cycle_enemy(st()),
        "enemy_id": lambda: _enemy_id(st(), ctx["pick_object"], dirty),
        "enemy_dir": lambda: _enemy_dir(st(), dirty),
        "enemy_chap": lambda: enemy_field("chap"),
        "enemy_spawn_h": lambda: enemy_field("spawn_h"),
        "enemy_is_h_set": lambda: enemy_field("is_h_set"),
        "enemy_spawn_d": lambda: enemy_field("spawn_d"),
        "enemy_is_d_set": lambda: enemy_field("is_d_set"),
        "enemy_spawn_cond": lambda: _toggle_spawn(st(), flash, dirty),
        "spawn_wait_n": lambda: resize_spawn("wait_n", "wait_spawn"),
        "spawn_kill_n": lambda: resize_spawn("kill_n", "kill_spawn"),
        "spawn_active_n": lambda: resize_spawn("active_n", "active_spawn"),
        "spawn_edit_wait": lambda: edit_spawn_pair("wait_spawn"),
        "spawn_edit_kill": lambda: edit_spawn_pair("kill_spawn"),
        "spawn_edit_active": lambda: edit_spawn_pair("active_spawn"),
        "enemy_add": lambda: _enemy_add(st(), ctx["pick_object"], dirty, flash),
        "enemy_del": lambda: _enemy_del(st(), dirty, flash),
        "entry_cycle": lambda: _entry_cycle(st()),
        "entry_room": lambda: _entry_room(st(), dirty),
        "entry_dir": lambda: _entry_dir(st(), dirty),
        "entry_add": do_entry_add,
        "entry_del": lambda: _entry_del(st(), dirty),
        "tele_cycle": lambda: _tele_cycle(st()),
        "tele_x": lambda: tele_field("x"),
        "tele_y": lambda: tele_field("y"),
        "tele_w": lambda: tele_field("w"),
        "tele_h": lambda: tele_field("h"),
        "tele_dx": lambda: tele_field("dx"),
        "tele_dy": lambda: tele_field("dy"),
        "tele_dd": lambda: tele_field("dd"),
        "tele_to_room": lambda: tele_field("to_room"),
        "tele_to_map": lambda: _tele_map(st(), dirty),
        "tele_song": lambda: tele_field("to_song"),
        "tele_add": do_tele_add,
        "tele_del": lambda: _tele_del(st(), dirty),
        "tele_dest_phase": lambda: _tele_dest(st(), flash),
        "seq_src": lambda: _seq_src(st(), flash),
        "seq_cycle": lambda: _seq_cycle(st()),
        "seq_add": do_seq_add,
        "seq_del": lambda: _seq_del(st(), dirty),
        "seq_ents": lambda: _seq_ents(st(), dirty),
        "seq_ent_code": lambda: _seq_ent_code(st(), dirty),
        "seq_cmd_cycle": lambda: _seq_cmd_cycle(st()),
        "seq_cmd_add": lambda: _seq_cmd_add(st(), dirty),
        "seq_cmd_del": lambda: _seq_cmd_del(st(), dirty),
        "seq_block_cycle": lambda: _seq_block_cycle(st()),
        "seq_block_add": lambda: _seq_block_add(st(), dirty),
        "seq_block_del": lambda: _seq_block_del(st(), dirty),
        "macro_cycle": lambda: _macro_cycle(st()),
        "macro_add": do_macro_add,
        "macro_del": lambda: _macro_del(st()),
        "macro_clear": do_macro_clear,
        "macro_wall": do_macro_wall,
        "macro_walk_toggle": lambda: _macro_walk_toggle(st(), flash),
        "save": lambda: ctx["save"](),
        "save_as": lambda: ctx["save_as"](),
        "load": lambda: ctx["load"](),
        "new_map": lambda: ctx["new_map"](),
        "room_add": do_room_add,
        "room_del": lambda: _room_del(st(), dirty, flash),
        "parallax_toggle": lambda: _parallax_toggle(st(), dirty, flash),
    }
    for field in ops.COMMAND_DATA_FIELDS:
        actions[f"block:{field}"] = (lambda f=field: edit_block_field(f))
    return actions


def _jump_room(state, flash) -> None:
    room = prompt_int(
        "Jump to room",
        state.room_i,
        minimum=0,
        maximum=max(0, state.game_map.rooms - 1),
    )
    if room is not None:
        state.room_i = room
        flash(f"Room {room}")


def _cycle_enemy(state) -> None:
    if state.room.enemies:
        state.enemy_sel = (state.enemy_sel + 1) % state.room.enemies


def _enemy_id(state, pick_object, dirty) -> None:
    if not state.room.enemy:
        return
    oid = pick_object()
    if oid:
        state.room.enemy[state.enemy_sel].id = oid.replace("/", "\\")
        dirty()


def _enemy_dir(state, dirty) -> None:
    if not state.room.enemy:
        return
    e = state.room.enemy[state.enemy_sel]
    e.direction = (e.direction + 1) & 3
    dirty()


def _toggle_spawn(state, flash, dirty) -> None:
    if not state.room.enemy:
        return
    e = state.room.enemy[state.enemy_sel]
    if e.spawn_cond == 0:
        ops.ensure_spawn_info(e)
        flash("spawn_cond on")
    else:
        ops.clear_spawn_info(e)
        flash("spawn_cond off")
    dirty()


def _enemy_add(state, pick_object, dirty, flash) -> None:
    oid = pick_object()
    if oid:
        ops.add_enemy(state.room, oid, state.cam_x + 16, state.cam_y + 16)
        state.enemy_sel = state.room.enemies - 1
        dirty()
        flash(f"Added {Path(oid).stem}")


def _enemy_del(state, dirty, flash) -> None:
    if state.room.enemy:
        ops.delete_enemy(state.room, state.enemy_sel)
        state.enemy_sel = max(0, min(state.enemy_sel, state.room.enemies - 1))
        dirty()
        flash("Enemy deleted")


def _entry_cycle(state) -> None:
    if state.game_map.entries:
        state.entry_sel = (state.entry_sel + 1) % state.game_map.entries
        en = state.game_map.entry[state.entry_sel]
        if en.room != state.room_i:
            state.room_i = en.room


def _entry_room(state, dirty) -> None:
    if not state.game_map.entry:
        return
    en = state.game_map.entry[state.entry_sel]
    room = prompt_int(
        "entry.room", en.room, minimum=0, maximum=max(0, state.game_map.rooms - 1)
    )
    if room is not None:
        en.room = room
        dirty()
        if room != state.room_i:
            state.room_i = room


def _entry_dir(state, dirty) -> None:
    if not state.game_map.entry:
        return
    en = state.game_map.entry[state.entry_sel]
    en.direction = (en.direction + 1) & 7
    dirty()


def _entry_del(state, dirty) -> None:
    if state.game_map.entry:
        ops.delete_entry(state.game_map, state.entry_sel)
        state.entry_sel = max(0, min(state.entry_sel, state.game_map.entries - 1))
        dirty()


def _tele_cycle(state) -> None:
    if state.room.teleports:
        state.tele_sel = (state.tele_sel + 1) % state.room.teleports


def _tele_map(state, dirty) -> None:
    if not state.room.teleport:
        return
    tp = state.room.teleport[state.tele_sel]
    maps = sorted(p.name for p in (Path("data/map")).glob("*.map")) if Path("data/map").is_dir() else []
    from lynn.paths import data_root

    maps = sorted(p.name for p in (data_root() / "map").glob("*.map"))
    labels = ["(clear)"] + maps
    idx = pick_list("to_map", labels)
    if idx is None:
        return
    tp.to_map = "" if idx == 0 else maps[idx - 1]
    dirty()


def _tele_del(state, dirty) -> None:
    if state.room.teleport:
        ops.delete_teleport(state.room, state.tele_sel)
        state.tele_sel = max(0, min(state.tele_sel, state.room.teleports - 1))
        dirty()


def _tele_dest(state, flash) -> None:
    if not state.room.teleport:
        return
    tp = state.room.teleport[state.tele_sel]
    if tp.to_map:
        flash("Cross-map tele — edit dx/dy in panel")
        return
    state.tele_prev_room = state.room_i
    state.room_i = tp.to_room
    state.tele_phase = 2
    flash("Click dest dx/dy · Enter finish")


def _seq_src(state, flash) -> None:
    state.seq_src = SEQ_SOURCES[(SEQ_SOURCES.index(state.seq_src) + 1) % len(SEQ_SOURCES)]
    state.seq_sel = state.seq_cmd_sel = state.seq_block_sel = state.seq_ent_sel = 0
    flash(f"Sequence source: {state.seq_src}")


def _seq_cycle(state) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if owner.seq:
        state.seq_sel = (state.seq_sel + 1) % len(owner.seq)
        state.seq_cmd_sel = state.seq_block_sel = state.seq_ent_sel = 0


def _seq_del(state, dirty) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    ops.delete_sequence(owner, state.seq_sel)
    state.seq_sel = max(0, min(state.seq_sel, owner.seq_here - 1))
    dirty()


def _seq_ents(state, dirty) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if not owner.seq:
        return
    seq = owner.seq[min(state.seq_sel, len(owner.seq) - 1)]
    n = prompt_int("ents", seq.ents, minimum=0, maximum=64)
    if n is None:
        return
    while len(seq.ent_code) < n:
        seq.ent_code.append(0)
    seq.ent_code = seq.ent_code[:n]
    seq.ents = n
    dirty()


def _seq_ent_code(state, dirty) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if not owner.seq:
        return
    seq = owner.seq[min(state.seq_sel, len(owner.seq) - 1)]
    if not seq.ent_code:
        return
    state.seq_ent_sel = max(0, min(state.seq_ent_sel, len(seq.ent_code) - 1))
    val = prompt_int(f"ent_code[{state.seq_ent_sel}]", seq.ent_code[state.seq_ent_sel])
    if val is not None:
        seq.ent_code[state.seq_ent_sel] = val
        dirty()


def _seq_cmd_cycle(state) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if owner.seq and owner.seq[state.seq_sel].Command:
        seq = owner.seq[state.seq_sel]
        state.seq_cmd_sel = (state.seq_cmd_sel + 1) % seq.commands
        state.seq_block_sel = 0


def _seq_cmd_add(state, dirty) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if owner.seq:
        seq = owner.seq[state.seq_sel]
        ops.add_command(seq)
        state.seq_cmd_sel = seq.commands - 1
        dirty()


def _seq_cmd_del(state, dirty) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if owner.seq:
        seq = owner.seq[state.seq_sel]
        ops.delete_command(seq, state.seq_cmd_sel)
        state.seq_cmd_sel = max(0, min(state.seq_cmd_sel, seq.commands - 1))
        dirty()


def _seq_block_cycle(state) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if owner.seq and owner.seq[state.seq_sel].Command:
        cmd = owner.seq[state.seq_sel].Command[state.seq_cmd_sel]
        if cmd.ent:
            state.seq_block_sel = (state.seq_block_sel + 1) % cmd.ents


def _seq_block_add(state, dirty) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if owner.seq and owner.seq[state.seq_sel].Command:
        cmd = owner.seq[state.seq_sel].Command[state.seq_cmd_sel]
        ops.add_command_block(cmd)
        state.seq_block_sel = cmd.ents - 1
        dirty()


def _seq_block_del(state, dirty) -> None:
    owner = ops.seq_list_for(
        state.game_map, state.room, state.seq_src, state.enemy_sel, state.entry_sel
    )
    if owner.seq and owner.seq[state.seq_sel].Command:
        cmd = owner.seq[state.seq_sel].Command[state.seq_cmd_sel]
        ops.delete_command_block(cmd, state.seq_block_sel)
        state.seq_block_sel = max(0, min(state.seq_block_sel, cmd.ents - 1))
        dirty()


def _macro_cycle(state) -> None:
    if state.macros:
        state.macro_sel = (state.macro_sel + 1) % len(state.macros)


def _macro_del(state) -> None:
    if state.macros:
        del state.macros[state.macro_sel]
        state.macro_sel = max(0, min(state.macro_sel, len(state.macros) - 1))


def _macro_walk_toggle(state, flash) -> None:
    state.macro_walk_edit = not state.macro_walk_edit
    flash("Macro walk edit ON" if state.macro_walk_edit else "Macro walk edit OFF")


def _parallax_toggle(state, dirty, flash) -> None:
    """FB s_parallax bare XOR of room.parallax flag."""
    room = state.room
    if room.parallax:
        room.parallax = 0
        flash("Parallax off")
    else:
        room.parallax = -1
        flash("Parallax on")
    dirty()
    refresh = getattr(state, "_refresh_para", None)
    if callable(refresh):
        refresh()


def _room_del(state, dirty, flash) -> None:
    if state.game_map.rooms <= 1:
        flash("Cannot delete last room")
        return
    ops.delete_room(state.game_map, state.room_i)
    state.room_i = min(state.room_i, state.game_map.rooms - 1)
    dirty()
    flash("Room deleted")
