"""Minimal act_enemies inner step: run one XML func and wrap the block."""

from __future__ import annotations

from lynn.object.char import CharType


def tick_object(this: CharType) -> None:
    f = this.funcs
    if f.states == 0 or not f.func:
        return
    state = f.active_state
    if state < 0 or state >= len(f.func):
        return
    count = f.func_count[state] if state < len(f.func_count) else 0
    if count == 0:
        return
    if f.current_func[state] == count:
        f.current_func[state] = 0
    idx = f.current_func[state]
    block = f.func[state]
    if idx < 0 or idx >= len(block):
        return
    result = block[idx](this)
    f.current_func[state] = f.current_func[state] + result


def spawn_pairs_met(pairs) -> int:
    """FB wait/kill/active switch AND: each pair's now[index] vs code_state."""
    from lynn.constants import TRUE
    from lynn.events import now

    if not pairs:
        return TRUE
    res = TRUE
    for pair in pairs:
        op = now[pair.code_index] != 0 if 0 <= pair.code_index < len(now) else False
        if pair.code_state == 0:
            op = not op
        if not op:
            return 0
    return res


def LLObject_SpawnWait(obj: CharType) -> int:
    """FB LLObject_SpawnWait: wait switches met and not yet triggered."""
    if obj.spawn_wait_trig != 0 or obj.spawn_info is None:
        return 0
    if obj.spawn_info.wait_n == 0:
        return 0
    return spawn_pairs_met(obj.spawn_info.wait_spawn)


def LLObject_CheckSpawn(obj: CharType) -> None:
    from lynn.constants import TRUE
    from lynn.object.dispatch import lookup_func

    if obj.spawn_cond == 0 or obj.spawn_info is None:
        return
    if obj.spawn_kill_trig != 0:
        return
    info = obj.spawn_info
    if obj.spawn_wait_trig == 0 and info.wait_n != 0:
        if spawn_pairs_met(info.wait_spawn):
            from lynn.object.xml_load import LLSystem_CopyNewObject

            num = obj.num
            LLSystem_CopyNewObject(obj)
            obj.num = num
            obj.coords_x = obj.x_origin
            obj.coords_y = obj.y_origin
            obj.spawn_wait_trig = TRUE
    if info.kill_n == 0:
        return
    if spawn_pairs_met(info.kill_spawn):
        lookup_func("__make_dead")(obj)
        lookup_func("__cripple")(obj)
        obj.seq_release = 0
        obj.spawn_kill_trig = TRUE


def tick_objects(objs: list[CharType]) -> None:
    from lynn.object.control import in_proximity, out_proximity

    for obj in objs:
        if obj.spawn_cond != 0:
            LLObject_CheckSpawn(obj)
        if obj.spawn_kill_trig != 0:
            continue
        if obj.dead == 0 and obj.froggy != 0:
            if obj.mad == 0:
                if obj.funcs.active_state < obj.reset_state:
                    obj.funcs.active_state = in_proximity(obj)
            else:
                obj.funcs.active_state = out_proximity(obj)
        tick_object(obj)
        if obj.vol_fade_trig != 0:
            from lynn.object.dispatch import lookup_func

            lookup_func("__do_vol_fade")(obj)
        if obj.hurt != 0:
            state = obj.funcs.active_state
            count = obj.funcs.func_count[state] if state < len(obj.funcs.func_count) else 0
            if count and obj.funcs.current_func[state] >= count:
                from lynn.object.combat import LLObject_ClearDamage, LLObject_ShiftState

                LLObject_ShiftState(obj, obj.reset_state)
                LLObject_ClearDamage(obj)
                obj.invisible = 0
                obj.flash_count = 0
                obj.flash_timer = 0
