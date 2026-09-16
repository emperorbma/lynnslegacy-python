"""FB object_time.bas — idle return and pause timers."""

from __future__ import annotations

from lynn import clock
from lynn.object.char import CharType
from lynn.object.dispatch import register_func


def __return_idle(this: CharType) -> int:
    this.funcs.current_func[this.funcs.active_state] = 0
    this.funcs.active_state = 0
    this.funcs.current_func[this.funcs.active_state] = 0
    return 0


def __return_reset(this: CharType) -> int:
    this.funcs.current_func[this.funcs.active_state] = 0
    this.funcs.active_state = this.reset_state
    return 0


def __return_jump(this: CharType) -> int:
    """FB object_time.bas: switch to jump_state without advancing."""
    this.funcs.current_func[this.funcs.active_state] = 0
    this.funcs.active_state = this.jump_state
    return 0


def __return_jump_npc(this: CharType) -> int:
    this.funcs.current_func[this.funcs.active_state] = 0
    this.funcs.active_state = this.jump_state
    return 1


def __return_reset_npc(this: CharType) -> int:
    this.funcs.current_func[this.funcs.active_state] = 0
    this.funcs.active_state = this.reset_state
    return 1


def __check_key(this: CharType) -> int:
    """FB object_time.bas: consume a small key, or abort the door sequence."""
    import lynn.events as events

    hero = events.hero
    if hero is None or hero.key == 0:
        this.return_trig = 1
        return 1
    hero.key -= 1
    return 1


def __if_all_dead(this: CharType) -> int:
    """FB object_time.bas: stay here until every real enemy in the room is dead.

    Doors, torches, and other gates are ignored. Return -1 to keep polling,
    1 to open (only if this.chap is set).
    """
    import lynn.events as events
    from lynn.constants import u_bardoor, u_fkeydoor, u_keydoor, u_ltorch, u_torch

    skip = {u_keydoor, u_fkeydoor, u_ltorch, u_torch, u_bardoor}
    for obj in events.current_others or []:
        if obj.dead == 0 and obj.unique_id not in skip:
            return -1
    if this.chap != 0:
        return 1
    return 0


def __check_b_key(this: CharType) -> int:
    """FB object_time.bas: fancy key is a flag; missing it aborts without advancing."""
    import lynn.events as events

    only = events.hero_only
    if only is None or only.b_key == 0:
        this.return_trig = 1
        return 0
    return 1


def __poll_action(this: CharType) -> int:
    import lynn.events as events

    hero = events.hero
    only = events.hero_only
    if hero is not None and hero.switch_room == -1:
        if only is not None and only.action != 0:
            return 1
    return 0


def __second_pause(this: CharType) -> int:
    if this.pause == 0:
        this.pause = clock.timer + 1
        return 0
    if clock.timer >= this.pause:
        this.pause = 0
        return 1
    return 0


def __half_second_pause(this: CharType) -> int:
    if this.pause == 0:
        this.pause = clock.timer + 0.5
        return 0
    if clock.timer >= this.pause:
        this.pause = 0
        return 1
    return 0


def __q_second_pause(this: CharType) -> int:
    """FB object_time.bas: 0.25s hold."""
    if this.pause == 0:
        this.pause = clock.timer + 0.25
        return 0
    if clock.timer >= this.pause:
        this.pause = 0
        return 1
    return 0


def __counted_jump(this: CharType) -> int:
    """FB object_time.bas: loop the previous func jump_count times."""
    if this.jump_count == this.jump_counter:
        this.jump_counter = 0
        return 1
    this.jump_counter += 1
    return -1


def __counted_jump_2(this: CharType) -> int:
    if this.jump_count == this.jump_counter:
        this.jump_counter = 0
        return 1
    this.jump_counter += 1
    return -2


def __timed_jump(this: CharType) -> int:
    if this.jump_timer == 0:
        this.jump_timer = float(this.jump_time) + clock.timer
    if clock.timer >= this.jump_timer:
        this.jump_timer = 0
        return 1
    return -1


def __timed_jump_2(this: CharType) -> int:
    """FB object_time.bas: wait jump_time, rewind two funcs each tick."""
    if this.jump_timer == 0:
        this.jump_timer = float(this.jump_time) + clock.timer
    if clock.timer >= this.jump_timer:
        this.jump_timer = 0
        return 1
    return -2


def __cond_jump(this: CharType) -> int:
    """FB object_time.bas: 50% rewind one func, else advance."""
    import random

    return -1 if int(random.random() * 2) < 1 else 1


def __jump_2_back(this: CharType) -> int:
    return -1


register_func("__return_idle", __return_idle)
register_func("__return_reset", __return_reset)
register_func("__return_jump", __return_jump)
register_func("__return_jump_npc", __return_jump_npc)
register_func("__return_reset_npc", __return_reset_npc)
register_func("__poll_action", __poll_action)
register_func("__check_key", __check_key)
register_func("__check_b_key", __check_b_key)
register_func("__if_all_dead", __if_all_dead)
register_func("__second_pause", __second_pause)
register_func("__half_second_pause", __half_second_pause)
register_func("__q_second_pause", __q_second_pause)
register_func("__counted_jump", __counted_jump)
register_func("__counted_jump_2", __counted_jump_2)
register_func("__timed_jump", __timed_jump)
register_func("__timed_jump_2", __timed_jump_2)
register_func("__cond_jump", __cond_jump)
register_func("__jump_2_back", __jump_2_back)
