"""FB object--gfx_animation.bas — idle cycle only for this slice."""

from __future__ import annotations

import random

from lynn import clock
from lynn.object.char import CharType
from lynn.object.dispatch import register_func
from lynn.object.gfx_frame import LLObject_IncrementFrame


def __gen_frame(this: CharType) -> int:
    """FB object_modification.bas: randomize this anim's rate in [low_frame, high_frame]."""
    lo = float(this.low_frame)
    hi = float(this.high_frame)
    if this.animControl and this.current_anim < len(this.animControl):
        this.animControl[this.current_anim].rate = (random.random() * (hi - lo)) + lo
    return 1


def __idle_animate(this: CharType) -> int:
    this.animating = 1
    if LLObject_IncrementFrame(this) != 0:
        this.animating = 0
        this.frame = 0
        this.frame_hold = clock.timer + this.animControl[this.current_anim].rate
        return 1
    return 0


def __active_animate(this: CharType) -> int:
    """FB object--gfx_animation.bas: play current anim once, then callback."""
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


register_func("__gen_frame", __gen_frame)
register_func("__idle_animate", __idle_animate)
register_func("__active_animate", __active_animate)
register_func("__active_animate_x", __active_animate)
