"""FB headers/ll/macros.bi helpers used from day one."""


def iif(cond, a, b):
    return a if cond else b


def imp(a: int, b: int) -> int:
    """FreeBASIC bitwise IMP: (NOT a) OR b, 32-bit."""
    return ((~a) | b) & 0xFFFFFFFF


def testbit(n: int, b: int) -> int:
    return n & (1 << b)


def quad_calc(x: int, y: int) -> int:
    # ((Abs(y And 1) Shl 1) + Abs(x And 1))
    return (abs(y & 1) << 1) + abs(x & 1)


def LLObject_CalculateFrame(this) -> int:
    if this.uni_directional == 0:
        dir_frames = 0
        if this.current_anim < len(this.animControl):
            dir_frames = this.animControl[this.current_anim].dir_frames
        return this.frame + (this.direction & 3) * dir_frames
    return this.frame
