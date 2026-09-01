"""FB object_control.bas in_proximity / out_proximity (savepoint froggy)."""

from __future__ import annotations

import lynn.events as events
from lynn import clock
from lynn.object.char import CharType


def in_proximity(this: CharType) -> int:
    hero = events.hero
    if hero is None:
        return this.funcs.active_state
    hx = hero.coords_x + (int(hero.perimeter_x) >> 1)
    hy = hero.coords_y + (int(hero.perimeter_y) >> 1)
    tx = this.coords_x + (int(this.perimeter_x) >> 1)
    ty = this.coords_y + (int(this.perimeter_y) >> 1)
    more_x = abs(hx - tx)
    more_y = abs(hy - ty)
    vf = int(this.vision_field)
    if more_x < vf and more_y < vf:
        if this.shifty != 0:
            if this.shifty_lock == 0:
                import random

                this.shifty_state = int(random.random() * 2)
                this.shifty_lock = 1
        if this.shifty != 0 and this.shifty_state != 0:
            return this.funcs.active_state
        this.mad = 1
        this.reset_delay = 0
        this.pause_hold = 0
        if 0 <= this.funcs.active_state < len(this.funcs.current_func):
            this.funcs.current_func[this.funcs.active_state] = 0
        return this.jump_state
    return this.funcs.active_state


def out_proximity(this: CharType) -> int:
    hero = events.hero
    if hero is None:
        return this.funcs.active_state
    hx = hero.coords_x + (int(hero.perimeter_x) >> 1)
    hy = hero.coords_y + (int(hero.perimeter_y) >> 1)
    tx = this.coords_x + (int(this.perimeter_x) >> 1)
    ty = this.coords_y + (int(this.perimeter_y) >> 1)
    more_x = abs(hx - tx)
    more_y = abs(hy - ty)
    vf = int(this.vision_field)
    if more_x < vf and more_y < vf:
        this.reset_delay = clock.timer + this.lose_time
    if clock.timer >= this.reset_delay:
        if more_x > vf or more_y > vf:
            this.reset_delay = 0
            this.mad = 0
            if 0 <= this.funcs.active_state < len(this.funcs.current_func):
                this.funcs.current_func[this.funcs.active_state] = 0
            return this.reset_state
    if this.far_reset_delay == 0:
        if more_x > (vf * 2) or more_y > (vf * 2):
            this.far_reset_delay = clock.timer + 1
            return this.funcs.active_state
    else:
        if more_x < (vf * 2) or more_y < (vf * 2):
            this.far_reset_delay = 0
            return this.funcs.active_state
        if clock.timer >= this.far_reset_delay:
            this.far_reset_delay = 0
            this.reset_delay = 0
            this.mad = 0
            if 0 <= this.funcs.active_state < len(this.funcs.current_func):
                this.funcs.current_func[this.funcs.active_state] = 0
            return this.reset_state
    return this.funcs.active_state
