"""FB object--gfx_frame.bas / Lua object_gfx_frame.lua."""

from __future__ import annotations

from lynn import clock
from lynn.macros import LLObject_CalculateFrame, iif
from lynn.object.char import CharType
from lynn.object.dispatch import register_func


def LLObject_IgnoreDirectional(this: CharType) -> int:
    if this.animating != 0:
        return -1
    if this.uni_directional != 0:
        return -1
    return 0


def LLObject_IncrementFrame(this: CharType) -> int:
    # Returns 1 when .frame meets the edge of its range.
    if this.frame_hold == 0:
        frame_transfer = LLObject_CalculateFrame(this)
        ctrl = this.animControl[this.current_anim]
        if 0 <= frame_transfer < len(ctrl.frame):
            ctrl.frame[frame_transfer].sound_lock = 0
        this.frame = this.frame + 1
        if LLObject_IgnoreDirectional(this) != 0:
            edge = this.anim[this.current_anim].frames
        else:
            edge = ctrl.dir_frames
        if this.frame == edge:
            return 1
        tet = iif((this.mad == 0) or (this.dead != 0), ctrl.rate, ctrl.rateMad)
        this.frame_hold = clock.timer + tet
    if clock.timer > this.frame_hold:
        this.frame_hold = 0
    return 0


def __reset_frame(this: CharType) -> int:
    this.frame = 0
    return 1


register_func("__reset_frame", __reset_frame)
