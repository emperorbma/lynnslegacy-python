"""FB object--gfx_animation.bas — idle cycle only for this slice."""

from __future__ import annotations

from lynn import clock
from lynn.object.char import CharType
from lynn.object.dispatch import register_func
from lynn.object.gfx_frame import LLObject_IncrementFrame


def __idle_animate(this: CharType) -> int:
    this.animating = 1
    if LLObject_IncrementFrame(this) != 0:
        this.animating = 0
        this.frame = 0
        this.frame_hold = clock.timer + this.animControl[this.current_anim].rate
        return 1
    return 0


register_func("__idle_animate", __idle_animate)
