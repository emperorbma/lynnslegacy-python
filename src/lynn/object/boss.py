"""FB object_boss.bas — Grult circle, fireball, and gtorch lighting."""

from __future__ import annotations

import math
import random

import lynn.events as events
from lynn import clock
from lynn.constants import u_gtorch, u_grult
from lynn.object.char import CharType
from lynn.object.dispatch import register_func
from lynn.object.gfx_frame import LLObject_IncrementFrame

_grult_proj_lock = 0


def _v2_calc_flyback(mx: float, my: float, nx: float, ny: float) -> tuple[float, float]:
    """FB V2_CalcFlyback: unit vector from n toward m."""
    dx = mx - nx
    dy = my - ny
    dist = math.sqrt(dx * dx + dy * dy)
    if dist == 0:
        return 0.0, 0.0
    return dx / dist, dy / dist


def __do_circle(this: CharType) -> int:
    """FB object_boss.bas: orbit x_origin/y_origin; 30% fire chance every 45 degrees."""
    if this.walk_hold == 0:
        radians = (3.14159 / 180.0) * this.degree
        mov_x = this.radius * math.sin(radians)
        mov_y = this.radius * math.cos(radians)
        this.coords_x = this.x_origin + mov_x
        this.coords_y = this.y_origin - mov_y
        if int(this.degree) % 45 == 0:
            if random.random() * 100 < 30:
                this.funcs.current_func[this.funcs.active_state] = 0
                this.funcs.active_state = this.proj_state
                if 0 <= this.proj_state < len(this.funcs.current_func):
                    this.funcs.current_func[this.proj_state] = 0
                return 0
        if this.degree >= 360:
            this.degree = 0
        else:
            this.degree += 0.75
        this.walk_hold = clock.timer + (this.walk_speed or 0.009)
    if clock.timer >= this.walk_hold:
        this.walk_hold = 0
    if LLObject_IncrementFrame(this) != 0:
        this.animating = 0
        this.frame = 0
        rate = this.animControl[this.current_anim].rate if this.animControl else 0.055
        this.frame_hold = clock.timer + rate
    return 1


def __grult_fireball(this: CharType) -> int:
    """FB object_boss.bas: spawn a homing fireball from the mouth."""
    global _grult_proj_lock
    if this.grult_proj_trig == 0:
        if this.projectile is None:
            from lynn.object.char import EntityProjectile

            this.projectile = EntityProjectile()
            this.projectile.coords = [[0, 0]]
        if not this.projectile.coords:
            this.projectile.coords = [[0, 0]]
        this.projectile.coords[0][0] = 52 + this.coords_x
        this.projectile.coords[0][1] = 36 + this.coords_y
        _grult_proj_lock = 0
        this.grult_proj_trig = 1
    return 1


def __do_grult_proj(this: CharType) -> int:
    """FB object_boss.bas: home until within 48px, then lock heading."""
    global _grult_proj_lock
    if this is None:
        _grult_proj_lock = 0
        return 0
    proj = this.projectile
    if proj is None or not proj.coords:
        return 0
    if this.fly_timer == 0:
        if (proj.travelled & 3) == 0:
            hero = events.hero
            hx = hero.coords_x if hero is not None else proj.coords[0][0]
            hy = hero.coords_y if hero is not None else proj.coords[0][1]
            if abs(proj.coords[0][0] - hx) < 48 and abs(proj.coords[0][1] - hy) < 48:
                _grult_proj_lock = 1
            if _grult_proj_lock == 0 and hero is not None:
                hmx = hero.coords_x + (int(hero.perimeter_x) >> 1)
                hmy = hero.coords_y + (int(hero.perimeter_y) >> 1)
                pmx = proj.coords[0][0] + 2
                pmy = proj.coords[0][1] + 2
                this.fly_x, this.fly_y = _v2_calc_flyback(hmx, hmy, pmx, pmy)
        proj.coords[0][0] += this.fly_x
        proj.coords[0][1] += this.fly_y
        this.fly_timer = clock.timer + (this.fly_speed or 0.009)
        proj.travelled += 1
    if clock.timer >= this.fly_timer:
        this.fly_timer = 0
    length = proj.length if proj.length else 256
    if proj.travelled >= length:
        from lynn.object.projectile import LLObject_ClearProjectiles

        LLObject_ClearProjectiles(this)
        this.fly_timer = 0
        this.grult_proj_trig = 0
    return 0


def LLObject_CheckGTorchLit(this: CharType) -> None:
    """FB engine--LL.bas: Grult fireball AABB vs gtorch lights the room."""
    from lynn.map.collision import check_bounds
    from lynn.object.combat import LLObject_ShiftState
    from lynn.object.projectile import LLObject_ClearProjectiles

    proj = this.projectile
    if proj is None or not proj.coords:
        return
    others = events.current_others or []
    pw, ph = 16, 16
    if this.anim and 0 <= this.proj_anim < len(this.anim):
        anim = this.anim[this.proj_anim]
        pw = int(anim.x) or 16
        ph = int(anim.y) or 16
    origin = (proj.coords[0][0], proj.coords[0][1], pw, ph)
    for obj in others:
        if obj.unique_id != u_gtorch:
            continue
        target = (obj.coords_x, obj.coords_y, obj.perimeter_x, obj.perimeter_y)
        if check_bounds(origin, target) != 0:
            continue
        if obj.funcs.active_state == 0:
            obj.jump_timer = 0
            LLObject_ShiftState(obj, obj.hit_state)
            LLObject_ClearProjectiles(this)
            this.grult_proj_trig = 0
            this.fly_timer = 0
        return


def tick_grult(this: CharType) -> None:
    """FB act_enemies: stun when dark != 4, resume when dark == 4."""
    from lynn.object.combat import LLObject_ClearDamage, LLObject_ShiftState
    from lynn.object.projectile import LLObject_ClearProjectiles

    if this.unique_id != u_grult:
        return
    if this.funcs.active_state == 0 or this.funcs.active_state == this.proj_state:
        if events.dark != 4:
            this.stun_return_trig = 0
            LLObject_ClearProjectiles(this)
            this.fly_timer = 0
            this.fly_count = 0
            this.grult_proj_trig = 0
            this.jump_counter = 0
            LLObject_ShiftState(this, this.stun_state)
        return
    if this.stun_return_trig == 0:
        if events.dark == 4:
            this.stun_return_trig = 1
        if this.stun_return_trig == 1 and this.dead == 0:
            this.jump_counter = 0
            this.hurt = 0
            LLObject_ClearDamage(this)
            this.fly_count = 0
            this.fly_timer = 0
            this.flash_timer = 0
            this.invisible = 0
            this.mad = 0
            this.invincible = -1
            LLObject_ShiftState(this, this.reset_state)


register_func("__do_circle", __do_circle)
register_func("__grult_fireball", __grult_fireball)
register_func("__do_grult_proj", __do_grult_proj)
