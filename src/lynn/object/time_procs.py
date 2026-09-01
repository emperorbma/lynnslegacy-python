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


register_func("__return_idle", __return_idle)
register_func("__second_pause", __second_pause)
register_func("__half_second_pause", __half_second_pause)
