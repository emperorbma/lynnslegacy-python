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


def __flashy(this: CharType) -> int:
    """FB object--gfx.bas: i-frames. dmg.id stays set until flash_count fills."""
    if this.flash_timer == 0:
        this.invisible = 0 if this.invisible != 0 else -1
        this.flash_timer = clock.timer + (this.flash_time or 0.02)
        this.flash_count += 1
    if clock.timer >= this.flash_timer:
        this.flash_timer = 0
    if this.flash_count >= this.flash_length:
        this.flash_count = 0
        this.flash_timer = 0
        this.invisible = 0
        this.dmg_id = 0
        from lynn.object.combat import LLObject_ClearDamage

        LLObject_ClearDamage(this)
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
    """FB object_etc.bas: roll health / gold / silver onto the corpse."""
    import random

    roll = int(random.random() * 100)
    kind = 0
    if this.d_health > roll:
        kind = 1
    elif this.d_gold > int(random.random() * 100):
        kind = 2
    elif this.d_silver > int(random.random() * 100):
        kind = 3
    if kind == 0:
        return 1
    this.dropped = kind
    span_x = int(this.perimeter_x) - 8
    span_y = int(this.perimeter_y) - 8
    ox = int(random.random() * span_x) if span_x > 0 else 0
    oy = int(random.random() * span_y) if span_y > 0 else 0
    this.drop_x = int(this.coords_x) + ox
    this.drop_y = int(this.coords_y) + oy
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
