"""FB object_boss.bas — Grult circle, fireball, gtorch lighting, Dyssius."""

from __future__ import annotations

import math
import random

import lynn.events as events
from lynn import clock
from lynn.constants import MO_JUST_CHECKING, u_dyssius, u_grult, u_gtorch, u_steelstrider
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
    speed = this.walk_speed or 0.009
    n, this.walk_hold = clock.pop_due(this.walk_hold, speed)
    fired = False
    for _ in range(n):
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
                fired = True
                break
        if this.degree >= 360:
            this.degree = 0
        else:
            this.degree += 0.75
    if fired:
        return 0
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
    global _grult_proj_lock, _grult_vx, _grult_vy
    if this is None:
        _grult_proj_lock = 0
        return 0
    proj = this.projectile
    if proj is None or not proj.coords:
        return 0
    speed = this.fly_speed or 0.009
    n, this.fly_timer = clock.pop_due(this.fly_timer, speed)
    for _ in range(n):
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
                _grult_vx, _grult_vy = _v2_calc_flyback(hmx, hmy, pmx, pmy)
        proj.coords[0][0] += _grult_vx
        proj.coords[0][1] += _grult_vy
        proj.travelled += 1
        if proj.travelled >= (proj.length if proj.length else 256):
            break
    length = proj.length if proj.length else 256
    if proj.travelled >= length:
        from lynn.object.projectile import LLObject_ClearProjectiles

        LLObject_ClearProjectiles(this)
        this.fly_timer = 0
        this.grult_proj_trig = 0
    return 0


def LLObject_CheckGTorchLit(this: CharType, others=None) -> None:
    """FB engine--LL.bas: Grult fireball AABB vs gtorch lights the room."""
    from lynn.map.collision import check_bounds
    from lynn.object.combat import LLObject_ShiftState
    from lynn.object.dispatch import lookup_func
    from lynn.object.projectile import LLObject_ClearProjectiles

    proj = this.projectile
    if proj is None or not proj.coords:
        return
    if others is None:
        others = events.current_others or []
    pw, ph = 16, 16
    if this.anim and 0 <= this.proj_anim < len(this.anim):
        anim = this.anim[this.proj_anim]
        pw = int(anim.x) or 16
        ph = int(anim.y) or 16
    px, py = proj.coords[0][0], proj.coords[0][1]
    if px == 0 and py == 0:
        return
    origin = (px, py, pw, ph)
    for obj in others:
        if obj.unique_id != u_gtorch:
            continue
        tw = int(obj.perimeter_x) or 16
        th = int(obj.perimeter_y) or 16
        target = (obj.coords_x, obj.coords_y, tw, th)
        if check_bounds(origin, target) != 0:
            continue
        if obj.funcs.active_state == 0:
            obj.jump_timer = 0
            LLObject_ShiftState(obj, obj.hit_state)
            lookup_func("__big_color_up")(obj)
            if 0 <= obj.hit_state < len(obj.funcs.current_func):
                obj.funcs.current_func[obj.hit_state] = 1
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
            this.fly_x = 0
            this.fly_y = 0
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


_DYSSIUS_SLIDE_LENGTH = 100


def _dyssius_pair(this: CharType) -> bool:
    return this.unique_id in (u_dyssius, u_steelstrider)


def _boss_momentum_move(this: CharType) -> None:
    """FB __momentum_move: step each live dir, then hold if any momentum remains."""
    from lynn.hero import _ensure_momentum

    from lynn.map.collision import move_object

    _ensure_momentum(this)
    room = events.current_room
    if room is None:
        return
    others = events.current_others
    face = this.direction
    moving = False
    for d in range(8):
        mom = this.momentum[d]
        if mom == 0.0:
            continue
        this.direction = d
        look = move_object(this, room, only_looking=0, moment=mom, others=others)
        if look == 0 and this.is_psfing == 0 and this.is_pushing == 0:
            this.momentum[d] = 0.0
        if this.momentum[d] != 0.0:
            moving = True
    this.direction = face
    if moving:
        this.walk_hold = clock.timer + (this.walk_speed or 0.03)


def tick_dyssius(this: CharType) -> None:
    """FB act_enemies: ice grip, then the 4.5s sway jump into the slide."""
    if not _dyssius_pair(this):
        return
    from lynn.hero import _calc_slide, _stop_grip
    from lynn.macros import check_ice
    from lynn.object.projectile import LLObject_ClearProjectiles

    room = events.current_room
    if room is not None:
        check_ice(this, room)
    if this.on_ice != 0:
        _calc_slide(this)
    else:
        _stop_grip(this)
    # FB coasts while walk_hold is already 0, then expires a stale hold
    # so the slide func (not the coast) takes the frame the timer elapses.
    if this.walk_hold == 0 and this.walk_steps == 0:
        _boss_momentum_move(this)
    if clock.timer > this.walk_hold:
        this.walk_hold = 0
    if this.dead == 0 and this.sway != 0 and clock.timer > this.sway:
        __dyssius_jump_slide(this)
        this.sway = 0
        this.fly_count = 0
        this.fly_timer = 0
        this.flash_timer = 0
        this.invisible = 0
        this.hurt = 0
        proj = this.projectile
        if proj is not None and proj.coords and (proj.coords[0][0] or proj.coords[0][1]):
            LLObject_ClearProjectiles(this)


def __dyssius_slide(this: CharType) -> int:
    """FB object_boss.bas: one accelerating step per walk_hold, 100 steps or a wall."""
    if this.walk_hold != 0:
        if clock.timer > this.walk_hold:
            this.walk_hold = 0
        else:
            return 0
    from lynn.hero import _ensure_momentum

    from lynn.map.collision import move_object

    _ensure_momentum(this)
    hold = int(getattr(this, "_dyssius_slide_hold", 0) or 0)
    room = events.current_room
    others = events.current_others
    if hold == 0:
        this.frame = 1
        for _try in range(20):
            this.direction = int(random.random() * 8)
            if room is None:
                break
            if move_object(this, room, only_looking=MO_JUST_CHECKING, others=others) != 0:
                break
    if this.unique_id == u_steelstrider:
        slide_speed = 4.0
    else:
        slide_speed = (this.walk_speed or 0.03) * 2
    d = int(this.direction)
    if d < 0 or d > 7:
        d = 0
        this.direction = 0
    this.momentum[d] += slide_speed
    blocked = False
    if room is not None:
        blocked = (
            move_object(
                this,
                room,
                only_looking=MO_JUST_CHECKING,
                moment=this.momentum[d],
                others=others,
            )
            == 0
        )
    if blocked:
        hold = _DYSSIUS_SLIDE_LENGTH - 1
    else:
        _boss_momentum_move(this)
    hold += 1
    if hold == _DYSSIUS_SLIDE_LENGTH:
        this._dyssius_slide_hold = 0
        return 1
    this._dyssius_slide_hold = hold
    this.walk_hold = clock.timer + (this.walk_speed or 0.03)
    return 0


def __dyssius_after_slide(this: CharType) -> int:
    """FB: wait until the facing momentum has died, then close the eye frame."""
    from lynn.hero import _ensure_momentum

    _ensure_momentum(this)
    d = int(this.direction)
    if 0 <= d <= 7 and this.momentum[d] == 0:
        this.frame = 0
        return 1
    return 0


def __dyssius_idle_gate(this: CharType) -> int:
    """FB chance_Percent(30): fire the beam, otherwise restart the idle."""
    if random.random() * 100 < 30:
        return 1
    from lynn.object.time_procs import __return_idle

    __return_idle(this)
    return 0


def __do_dyssius_proj(this: CharType) -> int:
    """FB: a two-segment beam dropped from the eye, 16px per refresh."""
    proj = this.projectile
    if proj is None:
        return 1
    while len(proj.coords) < 2:
        proj.coords.append([0, 0])
    if proj.refreshTime == 0:
        if proj.sound == 0:
            from lynn.audio import play_sample, sound_beam

            play_sample(sound_beam)
            proj.sound = -1
        if proj.travelled == 0:
            proj.coords[0][0] = 120 + this.coords_x
            proj.coords[0][1] = 105 + this.coords_y
            proj.coords[1][0] = proj.coords[0][0]
            proj.coords[1][1] = proj.coords[0][1] + 16
            proj.travelled += 1
        else:
            proj.coords[0][1] += 16
            proj.coords[1][1] += 16
            proj.travelled += 1
            length = proj.length if proj.length else 30
            if proj.travelled >= length:
                from lynn.object.projectile import LLObject_ClearProjectiles

                LLObject_ClearProjectiles(this)
                return 1
        rate = 0.08
        if this.animControl and 0 <= this.proj_anim < len(this.animControl):
            rate = this.animControl[this.proj_anim].rate or rate
        proj.refreshTime = clock.timer + rate
    elif clock.timer >= proj.refreshTime:
        proj.refreshTime = 0
    return 0


def __dyssius_flyback(this: CharType) -> int:
    """FB: 50 fly_speed ticks, clear the beam, then idle. Always returns 0."""
    speed = this.fly_speed or 0.009
    n, this.fly_timer = clock.pop_due(this.fly_timer, speed)
    this.fly_count += n
    proj = this.projectile
    if proj is not None and proj.coords and (proj.coords[0][0] or proj.coords[0][1]):
        from lynn.object.projectile import LLObject_ClearProjectiles

        LLObject_ClearProjectiles(this)
    if this.fly_count >= 50:
        this.fly_count = 0
        this.fly_timer = 0
        this.invisible = 0
        from lynn.object.combat import LLObject_ClearDamage
        from lynn.object.time_procs import __return_idle

        LLObject_ClearDamage(this)
        __return_idle(this)
    return 0


def __dyssius_jump_slide(this: CharType) -> int:
    """FB: leave the current state and start fp0 at the slide (index 2)."""
    st = this.funcs.active_state
    if 0 <= st < len(this.funcs.current_func):
        this.funcs.current_func[st] = 0
    this.funcs.active_state = 0
    if this.funcs.current_func:
        this.funcs.current_func[0] = 2
    return 0


def __dyssius_patience(this: CharType) -> int:
    """FB: arm a 4.5s sway timer once, then let infinity wait."""
    if this.sway == 0:
        this.sway = clock.timer + 4.5
    return 1


def __dyssius_eye_explode(this: CharType) -> int:
    this.expl_x_off = 117
    this.expl_y_off = 98
    this.expl_x_size = 16
    this.expl_y_size = 16
    this.explosions = 5
    return 1


def __dyssius_full_explode(this: CharType) -> int:
    this.expl_x_off = 0
    this.expl_y_off = 0
    this.expl_x_size = 0
    this.expl_y_size = 0
    this.explosions = 30
    return 1


register_func("__do_circle", __do_circle)
register_func("__grult_fireball", __grult_fireball)
register_func("__do_grult_proj", __do_grult_proj)
register_func("__dyssius_slide", __dyssius_slide)
register_func("__dyssius_after_slide", __dyssius_after_slide)
register_func("__dyssius_idle_gate", __dyssius_idle_gate)
register_func("__do_dyssius_proj", __do_dyssius_proj)
register_func("__dyssius_flyback", __dyssius_flyback)
register_func("__dyssius_jump_slide", __dyssius_jump_slide)
register_func("__dyssius_patience", __dyssius_patience)
register_func("__dyssius_eye_explode", __dyssius_eye_explode)
register_func("__dyssius_full_explode", __dyssius_full_explode)
