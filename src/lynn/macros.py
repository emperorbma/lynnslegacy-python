"""FB headers/ll/macros.bi helpers used from day one."""


def iif(cond, a, b):
    return a if cond else b


def imp(a: int, b: int) -> int:
    """FreeBASIC bitwise IMP: (NOT a) OR b, 32-bit."""
    return ((~a) | b) & 0xFFFFFFFF


def LLObject_CalculateFrame(this) -> int:
    if this.uni_directional == 0:
        dir_frames = 0
        if this.current_anim < len(this.animControl):
            dir_frames = this.animControl[this.current_anim].dir_frames
        return this.frame + (this.direction & 3) * dir_frames
    return this.frame
