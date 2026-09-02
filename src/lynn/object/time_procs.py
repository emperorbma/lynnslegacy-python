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


def __return_jump_npc(this: CharType) -> int:
    this.funcs.current_func[this.funcs.active_state] = 0
    this.funcs.active_state = this.jump_state
    return 1


def __return_reset_npc(this: CharType) -> int:
    this.funcs.current_func[this.funcs.active_state] = 0
    this.funcs.active_state = this.reset_state
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


def __jump_2_back(this: CharType) -> int:
    return -1


register_func("__return_idle", __return_idle)
register_func("__return_reset", __return_reset)
register_func("__return_jump_npc", __return_jump_npc)
register_func("__return_reset_npc", __return_reset_npc)
register_func("__poll_action", __poll_action)
register_func("__second_pause", __second_pause)
register_func("__half_second_pause", __half_second_pause)
register_func("__q_second_pause", __q_second_pause)
register_func("__counted_jump", __counted_jump)
register_func("__counted_jump_2", __counted_jump_2)
register_func("__timed_jump", __timed_jump)
register_func("__jump_2_back", __jump_2_back)
