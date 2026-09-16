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


def LLObject_IsWithin(this, cam_x: int = 0, cam_y: int = 0) -> int:
    """FB macros.bi: bosses and projectile users always; else on-screen AABB."""
    if getattr(this, "isBoss", 0) != 0:
        return -1
    if getattr(this, "proj_style", 0) != 0:
        return -1
    ax = 0 if getattr(this, "no_cam", 0) != 0 else cam_x
    ay = 0 if getattr(this, "no_cam", 0) != 0 else cam_y
    anim = None
    if this.anim and 0 <= this.current_anim < len(this.anim):
        anim = this.anim[this.current_anim]
    w = int(anim.x) if anim and anim.x else 16
    h = int(anim.y) if anim and anim.y else 16
    xin = abs(ax + 160 - this.coords_x) < (200 + w)
    yin = abs(ay + 100 - this.coords_y) < (150 + h)
    return -1 if xin and yin else 0


def LLObject_CalculateFrame(this) -> int:
    if this.uni_directional == 0:
        dir_frames = 0
        if this.current_anim < len(this.animControl):
            dir_frames = this.animControl[this.current_anim].dir_frames
        return this.frame + (this.direction & 3) * dir_frames
    return this.frame
