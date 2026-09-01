"""FB play_sequence / LLObject_ActionSequence / is_facing (sapling-capable)."""

from __future__ import annotations

import lynn.events as events
from lynn.constants import FALSE, TRUE
from lynn.gfx.box import BoxControl, make_box, tick_box
from lynn.map.collision import check_bounds
from lynn.map.types import SequenceType
from lynn.object.char import CharType

SF_BOX = 1024


def is_facing(o: CharType, o2: CharType, tile: int = 16) -> int:
    """0 if o is facing o2, -1 otherwise. FB engine--LL.bas is_facing."""
    if o.direction == 0:
        if o.coords_y >= (o2.coords_y + (o2.perimeter_y - 1)) and (
            o.coords_x >= (o2.coords_x - (o.perimeter_x - 1))
            or o.coords_x <= ((o2.coords_x + o2.perimeter_x) + (o.perimeter_x - 1))
        ):
            return 0
        return -1
    if o.direction == 2:
        if o.coords_y + (tile - 1) <= o2.coords_y and (
            o.coords_x >= (o2.coords_x - (tile - 1))
            or o.coords_x <= ((o2.coords_x + o2.perimeter_x) + (tile - 1))
        ):
            return 0
        return -1
    if o.direction == 3:
        if o.coords_x >= (o2.coords_x + (o2.perimeter_x - 1)) and (
            o.coords_y >= o2.coords_y or o.coords_y <= (o2.coords_y + o2.perimeter_y)
        ):
            return 0
        return -1
    if o.direction == 1:
        if o.coords_x + (tile - 1) <= o2.coords_x and (
            o.coords_y >= o2.coords_y or o.coords_y <= (o2.coords_y + o2.perimeter_y)
        ):
            return 0
        return -1
    return -1


def LLObject_isTouching(hero: CharType, other: CharType) -> int:
    origin = (hero.coords_x, hero.coords_y, hero.perimeter_x, hero.perimeter_y)
    target = (other.coords_x - 1, other.coords_y - 1, other.perimeter_x + 2, other.perimeter_y + 2)
    return check_bounds(origin, target)


def bind_sequence_ents(seq: SequenceType, hero: CharType, room_objs: list[CharType]) -> None:
    seq.ent = []
    for code in seq.ent_code:
        if code == -1:
            seq.ent.append(hero)
        elif 0 <= code < len(room_objs):
            seq.ent.append(room_objs[code])
        else:
            seq.ent.append(hero)


def try_action_sequence(hero: CharType, hero_only, room_objs: list[CharType]) -> SequenceType | None:
    """FB act_enemies action_sequence branch. Returns the seq to play, or None."""
    if hero_only.action == 0:
        return None
    for obj in room_objs:
        if getattr(obj, "action_sequence", 0) == 0:
            continue
        if obj.dead != 0 or obj.seq_release != 0:
            continue
        if is_facing(hero, obj) != 0:
            continue
        if LLObject_isTouching(hero, obj) != 0:
            continue
        if not obj.seq:
            continue
        sel = obj.sel_seq if 0 <= obj.sel_seq < len(obj.seq) else 0
        seq = obj.seq[sel]
        seq.current_command = 0
        for cmd in seq.Command:
            for ent in cmd.ent:
                ent.ent_func = 0
        bind_sequence_ents(seq, hero, room_objs)
        return seq
    return None


def _assign(char: CharType, cmd, hero_only) -> None:
    if char.mod_lock == 0:
        if cmd.seq_pause != 0:
            char.seq_paused = 1
        char.mod_lock = 1
    if cmd.free_to_move == 0:
        hero_only.action_lock = TRUE
    if cmd.abs_x != 0:
        char.coords_x = cmd.abs_x
    if cmd.abs_y != 0:
        char.coords_y = cmd.abs_y
    if cmd.fadeTime:
        char.fade_time = cmd.fadeTime
    if cmd.display_hud != 0:
        events.do_hud = TRUE
    char.dest_x = cmd.dest_x
    char.dest_y = cmd.dest_y
    if cmd.jump_count != 0:
        char.jump_count = cmd.jump_count
    char.chap = cmd.chap
    if cmd.walk_speed != 0:
        char.walk_speed = cmd.walk_speed


def sequence_FullReset(seq: SequenceType, hero_only) -> None:
    for cmd in seq.Command:
        for ent in cmd.ent:
            if ent.active_ent != SF_BOX and 0 <= ent.active_ent < len(seq.ent):
                actor = seq.ent[ent.active_ent]
                actor.mod_lock = 0
                actor.seq_paused = 0
                actor.return_trig = 0
            ent.ent_func = 0
    seq.current_command = 0
    hero_only.action_lock = 0


def _command_progressing(seq: SequenceType, box: BoxControl) -> int:
    cmd = seq.Command[seq.current_command]
    for ent in cmd.ent:
        if ent.active_ent == SF_BOX:
            if box.activated != 0:
                return 0
        elif 0 <= ent.active_ent < len(seq.ent):
            if seq.ent[ent.active_ent].return_trig == 0:
                return 0
    return TRUE


def play_sequence(seq: SequenceType | None, box: BoxControl, hero_only, palette=None, menu=None) -> SequenceType | None:
    if seq is None or seq.current_command >= seq.commands:
        if seq is not None:
            sequence_FullReset(seq, hero_only)
        events.do_hud = TRUE
        return None
    events.do_hud = 0
    cmd = seq.Command[seq.current_command]
    for ent in cmd.ent:
        if ent.active_ent == SF_BOX:
            if box.box_IsInited == 0:
                make_box(box, ent.text, palette, menu)
            tick_box(box, hero_only.action)
        else:
            if not (0 <= ent.active_ent < len(seq.ent)):
                continue
            actor = seq.ent[ent.active_ent]
            _assign(actor, ent, hero_only)
            if actor.return_trig:
                continue
            state = ent.ent_state
            funcs = actor.funcs
            if 0 <= state < len(funcs.func) and funcs.func[state]:
                block = funcs.func[state]
                fi = ent.ent_func
                if fi < 0 or fi >= len(block):
                    fi = 0
                    ent.ent_func = 0
                result = block[fi](actor)
                ent.ent_func += result
                if ent.ent_func >= (funcs.func_count[state] if state < len(funcs.func_count) else len(block)):
                    ent.ent_func = 0
        if _command_progressing(seq, box) != 0:
            for e2 in cmd.ent:
                if e2.active_ent != SF_BOX and 0 <= e2.active_ent < len(seq.ent):
                    seq.ent[e2.active_ent].return_trig = 0
                e2.ent_func = 0
                e2.ent_state = e2.hold_state
            seq.current_command += 1
            box.box_IsInited = 0
            break
    if seq.current_command >= seq.commands:
        sequence_FullReset(seq, hero_only)
        events.do_hud = TRUE
        return None
    return seq
