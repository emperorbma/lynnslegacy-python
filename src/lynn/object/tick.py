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
    if f.current_func[state] < 0:
        f.current_func[state] = 0


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
        _persist_opened_after_spawn_kill(obj)


def _persist_opened_after_spawn_kill(obj: CharType) -> None:
    """FB set_up_room_enemies: chests/buttons stay on the open sprite."""
    from lynn.constants import (
        u_bluechest,
        u_bluechestitem,
        u_button,
        u_chest,
        u_gbutton,
        u_ghut,
    )
    from lynn.object.combat import LLObject_ShiftState

    if obj.unique_id in (
        u_chest,
        u_bluechest,
        u_bluechestitem,
        u_ghut,
        u_button,
        u_gbutton,
    ):
        obj.current_anim = 1
    if obj.unique_id == u_ghut:
        LLObject_ShiftState(obj, 3)


def _objects_touching(a: CharType, b: CharType) -> int:
    from lynn.map.collision import check_bounds

    return check_bounds(
        (a.coords_x, a.coords_y, a.perimeter_x, a.perimeter_y),
        (b.coords_x, b.coords_y, b.perimeter_x, b.perimeter_y),
    )


def _tick_gbutton(obj: CharType, objs: list[CharType]) -> None:
    """FB act_enemies: gbutton state 1 if Lynn or a pushrock overlaps it."""
    import lynn.events as events
    from lynn.constants import u_pushrock

    pressed = 0
    hero = events.hero
    if hero is not None and _objects_touching(hero, obj) == 0:
        pressed = 1
    if pressed == 0:
        for other in objs:
            if other.unique_id == u_pushrock and _objects_touching(other, obj) == 0:
                pressed = 1
                break
    obj.funcs.active_state = 1 if pressed else 0


def LLObject_TorchModify(torch: CharType, enemies: list[CharType]) -> None:
    """FB LLObject_TorchModify: nearby ghosts and guards recolor an ltorch.

    Guards dim it (anim 3). A red shapeless (bshape) turns it red (anim 1)
    and hurts on contact. A green shapeless (gshape) turns it green (anim 2)
    and heals. The first living match in room order wins. Otherwise anim 0.
    """
    from lynn.constants import u_bguard, u_bshape, u_cguard, u_eguard, u_gshape, u_tguard

    tx = float(torch.coords_x) + float(torch.perimeter_x) / 2.0
    ty = float(torch.coords_y) + float(torch.perimeter_y) / 2.0
    reach = float(torch.vision_field)
    guards = (u_eguard, u_bguard, u_tguard, u_cguard)
    for enemy in enemies:
        if enemy.dead != 0:
            continue
        uid = enemy.unique_id
        if uid not in guards and uid not in (u_bshape, u_gshape):
            continue
        ex = float(enemy.coords_x) + float(enemy.perimeter_x) / 2.0
        ey = float(enemy.coords_y) + float(enemy.perimeter_y) / 2.0
        if abs(tx - ex) >= reach or abs(ty - ey) >= reach:
            continue
        if uid in guards:
            torch.current_anim = 3
        elif uid == u_bshape:
            torch.current_anim = 1
        else:
            torch.current_anim = 2
        return
    torch.current_anim = 0


def tick_objects(objs: list[CharType], cam: tuple[int, int] | None = None) -> None:
    from lynn.audio import play_sample
    from lynn.constants import (
        u_anger,
        u_dyssius,
        u_gbutton,
        u_gold,
        u_grult,
        u_health,
        u_ltorch,
        u_silver,
        u_steelstrider,
        u_sterach,
    )
    from lynn.object.boss import LLObject_CheckGTorchLit, tick_dyssius, tick_grult
    from lynn.object.combat import LLObject_ClearDamage, LLObject_ShiftState
    from lynn.object.combat_funcs import __flashy
    from lynn.object.control import in_proximity, out_proximity
    from lynn.object.dispatch import lookup_func
    from lynn.macros import LLObject_IsWithin
    from lynn.object.move_ai import __push

    cam_x = 0
    cam_y = 0
    if cam is not None:
        cam_x, cam_y = cam

    for obj in objs:
        # FB act_enemies: bosses and projectile users always run. Everyone
        # else stays frozen until the camera padding reaches them, which is
        # what keeps the open desert from ticking the whole room.
        if cam is not None and LLObject_IsWithin(obj, cam_x, cam_y) == 0:
            continue
        if obj.spawn_cond != 0:
            LLObject_CheckSpawn(obj)
        if obj.spawn_kill_trig != 0:
            continue
        if getattr(obj, "pushable", 0) != 0:
            __push(obj)
        if obj.unique_id == u_gbutton:
            _tick_gbutton(obj, objs)
        if obj.unique_id in (u_gold, u_silver, u_health):
            from lynn.gfx.loot import LLObject_GrabItems

            LLObject_GrabItems(obj)
        if obj.unique_id == u_ltorch:
            LLObject_TorchModify(obj, objs)
        if obj.dead == 0 and obj.froggy != 0:
            if obj.mad == 0:
                if obj.funcs.active_state < obj.reset_state:
                    obj.funcs.active_state = in_proximity(obj)
            else:
                obj.funcs.active_state = out_proximity(obj)
        if getattr(obj, "grult_proj_trig", 0) != 0:
            lookup_func("__do_grult_proj")(obj)
            LLObject_CheckGTorchLit(obj, objs)
        if getattr(obj, "anger_proj_trig", 0) != 0:
            lookup_func("__do_anger_proj")(obj)
        if obj.unique_id == u_grult:
            tick_grult(obj)
        tick_dyssius(obj)
        if obj.unique_id in (u_anger, u_sterach) and obj.hit != 0:
            if lookup_func("__anger_flyback")(obj) != 0:
                obj.hit = 0
        # FB act_enemies calls __flashy while dmg.id is set. Froggy enemies
        # whose hit_state is below reset_state get pulled into the chase
        # while Lynn is in vision, so flicker never finishes and this is
        # what ends the i-frames. Dyssius and the steel strider already
        # flash inside tick_dyssius.
        if obj.dmg_id != 0 and obj.unique_id not in (u_dyssius, u_steelstrider):
            __flashy(obj)
        tick_object(obj)
        proj = obj.projectile
        if proj is not None and proj.active != 0:
            lookup_func("__do_proj")(obj)
        if obj.vol_fade_trig != 0:
            lookup_func("__do_vol_fade")(obj)
        if obj.hurt != 0 and obj.unique_id not in (u_dyssius, u_steelstrider):
            state = obj.funcs.active_state
            count = obj.funcs.func_count[state] if state < len(obj.funcs.func_count) else 0
            if count and obj.funcs.current_func[state] >= count:
                if obj.unique_id == u_grult:
                    obj.fly_x = 0
                    obj.fly_y = 0
                    LLObject_ShiftState(obj, obj.stun_state)
                    if 0 <= obj.stun_state < len(obj.funcs.current_func):
                        obj.funcs.current_func[obj.stun_state] = 2
                else:
                    LLObject_ShiftState(obj, obj.reset_state)
                LLObject_ClearDamage(obj)
                obj.invisible = 0
                obj.flash_count = 0
                obj.flash_timer = 0
        if obj.dead == 0 and obj.hp <= 0 and obj.death_state:
            if obj.dead_sound != 0:
                play_sample(obj.dead_sound)
            LLObject_ShiftState(obj, obj.death_state)
    # FB maintain_temps runs after the temp-enemy pass. cripple sets
    # total_dead on its first call, and dead_drop_block has not reached
    # __drop yet, so a spawned roamer is released without a drop.
    objs[:] = [obj for obj in objs if getattr(obj, "is_temp", 0) == 0 or obj.total_dead == 0]
