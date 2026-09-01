"""Attack / hit / death XML funcs used by Lynn and roamers."""

from __future__ import annotations

import lynn.events as events
from lynn import clock
from lynn.object.char import CharType
from lynn.object.dispatch import register_func
from lynn.object.gfx_frame import LLObject_IncrementFrame


def __weapon_anim(this: CharType) -> int:
    weap = events.hero_only.weapon if events.hero_only is not None else 0
    this.current_anim = weap + 3
    this.frame = 0
    return 1


def __directional_animate(this: CharType) -> int:
    if LLObject_IncrementFrame(this) != 0:
        this.frame -= 1
        rate = this.animControl[this.current_anim].rate if this.animControl else 0.08
        this.frame_hold = clock.timer + rate
        return 1
    return 0


def __flicker(this: CharType) -> int:
    if this.flash_length <= 0:
        this.invisible = 0
        return 1
    if this.flash_timer == 0:
        this.invisible = -1 if this.invisible == 0 else 0
        this.flash_timer = clock.timer + (this.flash_time or 0.02)
        this.flash_count += 1
    if clock.timer >= this.flash_timer:
        this.flash_timer = 0
    if this.flash_count >= this.flash_length:
        this.flash_count = 0
        this.flash_timer = 0
        this.invisible = 0
        return 1
    return 0


def __do_flyback(this: CharType) -> int:
    if this.fly_length <= 0:
        this.fly_count = 0
        this.invisible = 0
        return 1
    if this.fly_timer == 0:
        this.fly_timer = clock.timer + (this.fly_speed or 0.004)
        this.fly_count += 1
        this.coords_x += this.fly_x
        this.coords_y += this.fly_y
    if clock.timer >= this.fly_timer:
        this.fly_timer = 0
    if this.fly_count >= this.fly_length:
        this.fly_count = 0
        this.fly_timer = 0
        this.invisible = 0
        return 1
    return 0


def __infinity(this: CharType) -> int:
    return 0


def __drop(this: CharType) -> int:
    return 1


def __active_anim_dead(this: CharType) -> int:
    this.frame = 0
    this.current_anim = this.dead_anim
    return 1


def __dead_animate(this: CharType) -> int:
    this.animating = 1
    anim = this.anim[this.current_anim] if this.anim and this.current_anim < len(this.anim) else None
    if anim is None or anim.frames <= 0:
        this.animating = 0
        return 1
    if LLObject_IncrementFrame(this) != 0:
        this.frame -= 1
        rate = this.animControl[this.current_anim].rate if this.animControl else 0.08
        this.frame_hold = clock.timer + rate
        this.animating = 0
        return 1
    return 0


for _name, _fn in list(globals().items()):
    if _name.startswith("__") and callable(_fn):
        register_func(_name, _fn)
