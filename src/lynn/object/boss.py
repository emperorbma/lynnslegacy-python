"""FB object_boss.bas — Grult circle, fireball, gtorch lighting, Dyssius."""

from __future__ import annotations

import math
import random

import lynn.events as events
from lynn import clock
from lynn.constants import (
    MO_JUST_CHECKING,
    u_boss5_down,
    u_boss5_left,
    u_boss5_right,
    u_dyssius,
    u_grult,
    u_gtorch,
    u_steelstrider,
)
from lynn.object.char import CharType
from lynn.object.dispatch import register_func
from lynn.object.gfx_frame import LLObject_IncrementFrame

_grult_proj_lock = 0
_anger_trigger_ball = 0
_anger_new_ball = 0
_anger_lock_x = 0
_anger_lock_y = 0


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
    """FB act_enemies: flash, ice grip, then the 4.5s sway jump into the slide."""
    if not _dyssius_pair(this):
        return
    from lynn.hero import _calc_slide, _stop_grip
    from lynn.macros import check_ice
    from lynn.object.projectile import LLObject_ClearProjectiles

    # The sway jump can abort flyback without clearing dmg_id. FB __flashy
    # is what ends those i-frames, or every later swing is ignored.
    if this.dmg_id != 0:
        from lynn.object.combat_funcs import __flashy

        __flashy(this)

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
    """FB: wait until the facing momentum has died, then open the eye (frame 0)."""
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


def __push_lynn_back(this: CharType) -> int:
    """FB object_boss.bas: unit vector from this actor through Lynn, times 3.

    The forest moth scene calls this, then Lynn's do_flyback, on the same command.
    """
    hero = events.hero
    if hero is None:
        return 1
    hx = float(hero.coords_x) + float(hero.perimeter_x) * 0.5
    hy = float(hero.coords_y) + float(hero.perimeter_y) * 0.5
    mx = float(this.coords_x) + float(this.perimeter_x) * 0.5
    my = float(this.coords_y) + float(this.perimeter_y) * 0.5
    fx, fy = _v2_calc_flyback(hx, hy, mx, my)
    hero.fly_x = fx * 3
    hero.fly_y = fy * 3
    return 1


def _room_enemy(index: int) -> CharType | None:
    others = events.current_others or []
    if 0 <= index < len(others):
        return others[index]
    return None


def _anger_frame(this: CharType) -> None:
    if (
        not this.anim
        or not this.animControl
        or not (0 <= this.current_anim < len(this.anim))
        or not (0 <= this.current_anim < len(this.animControl))
    ):
        return
    if LLObject_IncrementFrame(this) != 0:
        this.animating = 0
        this.frame = 0
        this.frame_hold = clock.timer + this.animControl[this.current_anim].rate


def __anger_flyback(this: CharType) -> int:
    """FB object_boss.bas: 70 fly_speed counts, then the next hit can land.

    The main loop there is uncapped, so this is one count per fly_speed.
    pop_due keeps that rate when the display frame is longer than fly_speed.
    """
    speed = this.fly_speed or 0.0009
    n, this.slide_hold = clock.pop_due(this.slide_hold, speed)
    this.shifty_state += n
    if this.shifty_state >= 70:
        this.shifty_state = 0
        this.slide_hold = 0
        this.invisible = 0
        from lynn.object.combat import LLObject_ClearDamage

        LLObject_ClearDamage(this)
        return 1
    return 0


def __anger_fireball_circle(this: CharType) -> int:
    """FB object_boss.bas: one orbital step, then let return_idle rewind.

    walk_speed .03 is one step about every 33 ms. cap=1 keeps that rate.
    """
    speed = this.walk_speed or 0.03
    n, this.walk_hold = clock.pop_due(this.walk_hold, speed, cap=1)
    for _ in range(n):
        radians = (3.14159 / 180.0) * this.degree
        this.coords_x = this.x_origin + this.radius * math.sin(radians)
        this.coords_y = this.y_origin - this.radius * math.cos(radians)
        if this.sway == 0:
            this.sway = 0.5
        prev = _room_enemy(this.num - 1) if this.num > 0 else None
        prev_radius = prev.radius if prev is not None else 0
        if this.lose_time != 0:
            this.sway = 1
            limit = prev_radius if prev_radius != 0 else 32
            if this.radius >= limit:
                this.lose_time = 0
                if prev is not None:
                    this.sway = prev.sway
                    if prev.radius != 0:
                        this.radius = prev.radius
        elif this.radius > 36 or this.radius < 24:
            this.sway = -this.sway
        this.radius += this.sway
        if this.degree >= 360:
            this.degree = 0
        else:
            this.degree += 3
    _anger_frame(this)
    return 1


def __anger_kill_fireball(this: CharType) -> int:
    from lynn.object.seq_funcs import __cripple, __make_dead

    for i in range(51, 59):
        ball = _room_enemy(i)
        if ball is None:
            break
        __make_dead(ball)
        __cripple(ball)
    return 1


def __anger_new_fireball(this: CharType) -> int:
    """Reload orbs 51..58 so they spiral back out from radius 1."""
    global _anger_new_ball
    from lynn.object.time_procs import __return_idle
    from lynn.object.xml_load import LLSystem_CopyNewObject

    c = _anger_new_ball + 51
    ball = _room_enemy(c)
    if ball is not None:
        LLSystem_CopyNewObject(ball, load_images=events.load_images != 0)
        ball.lose_time = -1
        ball.radius = 1
        prev = _room_enemy(c - 1)
        ball.degree = ((prev.degree if prev is not None else 0) + 45) % 360
    _anger_new_ball += 1
    if _anger_new_ball == 8:
        _anger_new_ball = 0
        __return_idle(this)
        return 0
    return 1


def __anger_middle(this: CharType) -> int:
    this.coords_x = 320
    this.coords_y = 320
    return 1


def __anger_teleport(this: CharType) -> int:
    this.coords_x = 256 + int(random.random() * (416 - 256))
    this.coords_y = 256 + int(random.random() * (416 - 256))
    this.sway = 0
    return 1


def __explode_jump(this: CharType) -> int:
    this.jump_count = 20000
    return 1


def __anger_trigger(this: CharType) -> int:
    """Send orbs 51..58 into anger_shoot, then switch Anger to the attack state."""
    global _anger_trigger_ball
    if this.sway == 0:
        from lynn.object.combat import LLObject_ShiftState

        ball = _room_enemy(_anger_trigger_ball + 51)
        if ball is not None:
            LLObject_ShiftState(ball, 1)
        _anger_trigger_ball += 1
        if _anger_trigger_ball == 8:
            _anger_trigger_ball = 0
            this.sway = -1
            LLObject_ShiftState(this, 2)
            return 0
    return 1


def __anger_shoot(this: CharType) -> int:
    """Fly this orb at Lynn until proj_dur expires, then remove it."""
    proj = this.projectile
    if proj is None:
        return 0
    length = proj.length if proj.length else 1800
    speed = this.fly_speed or 0.009
    n, this.fly_timer = clock.pop_due(this.fly_timer, speed)
    for _ in range(n):
        if proj.travelled == 0:
            hero = events.hero
            if hero is not None:
                hx = hero.coords_x + (int(hero.perimeter_x) >> 1)
                hy = hero.coords_y + (int(hero.perimeter_y) >> 1)
                mx = this.coords_x + (int(this.perimeter_x) >> 1)
                my = this.coords_y + (int(this.perimeter_y) >> 1)
                this.fly_x, this.fly_y = _v2_calc_flyback(hx, hy, mx, my)
        this.coords_x += this.fly_x
        this.coords_y += this.fly_y
        proj.travelled += 1
        if proj.travelled >= length:
            break
    if proj.travelled >= length:
        from lynn.object.projectile import LLObject_ClearProjectiles
        from lynn.object.seq_funcs import __cripple, __make_dead

        LLObject_ClearProjectiles(this)
        __make_dead(this)
        __cripple(this)
        return 1
    return 0


def __anger_fireball2(this: CharType) -> int:
    """FB: mouth shot at (11, 24) off the sprite. The engine steps it."""
    if this.anger_proj_trig == 0:
        if this.projectile is None:
            from lynn.object.char import EntityProjectile

            this.projectile = EntityProjectile()
            this.projectile.coords = [[0, 0]]
        if not this.projectile.coords:
            this.projectile.coords = [[0, 0]]
        this.projectile.coords[0][0] = 11 + this.coords_x
        this.projectile.coords[0][1] = 24 + this.coords_y
        __do_anger_proj(None)
        this.anger_proj_trig = 1
    return 1


def __do_anger_proj(this: CharType | None) -> int:
    """Home once on the first step, then fly straight. Cap matches other shots."""
    global _anger_lock_x, _anger_lock_y
    if this is None:
        _anger_lock_x = 0
        _anger_lock_y = 0
        return 0
    proj = this.projectile
    if proj is None or not proj.coords:
        return 0
    length = proj.length if proj.length else 256
    speed = this.fly_speed or 0.0009
    n, this.fly_timer = clock.pop_due(this.fly_timer, speed)
    for _ in range(n):
        if proj.travelled % 3 == 0:
            hero = events.hero
            hx = hero.coords_x if hero is not None else proj.coords[0][0]
            hy = hero.coords_y if hero is not None else proj.coords[0][1]
            if abs(proj.coords[0][0] - hx) < 48 and abs(proj.coords[0][1] - hy) < 48:
                _anger_lock_x = 1
                _anger_lock_y = 1
            if hero is not None:
                hmx = hero.coords_x + (int(hero.perimeter_x) >> 1)
                hmy = hero.coords_y + (int(hero.perimeter_y) >> 1)
                pmx = proj.coords[0][0] + 8
                pmy = proj.coords[0][1] + 8
                fx, fy = _v2_calc_flyback(hmx, hmy, pmx, pmy)
                if _anger_lock_x == 0:
                    this.fly_x = fx
                if _anger_lock_y == 0:
                    this.fly_y = fy
            _anger_lock_x = 1
            _anger_lock_y = 1
        proj.coords[0][0] += this.fly_x
        proj.coords[0][1] += this.fly_y
        proj.travelled += 1
        if proj.travelled >= length:
            break
    if proj.travelled >= length:
        from lynn.object.projectile import LLObject_ClearProjectiles

        LLObject_ClearProjectiles(this)
        this.fly_timer = 0
        this.anger_proj_trig = 0
    return 0


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


def _mid(obj: CharType) -> tuple[float, float]:
    return (
        float(obj.coords_x) + float(obj.perimeter_x) / 2.0,
        float(obj.coords_y) + float(obj.perimeter_y) / 2.0,
    )


def _room_enemy(index: int) -> CharType | None:
    others = events.current_others
    if others is None or not (0 <= index < len(others)):
        return None
    return others[index]


def _get_angle(ux: float, uy: float, vx: float, vy: float) -> float:
    """FB Get_Angle. 0 is up, 90 is right, and y grows downward."""
    o = abs(vy - uy)
    a = abs(vx - ux)
    if vy == uy and vx > ux:
        return 90.0
    if vy == uy and vx < ux:
        return 270.0
    if vx == ux and vy > uy:
        return 180.0
    if vx == ux and vy < uy:
        return 0.0
    if a == 0:
        return 0.0
    atan_deg = math.atan(o / a) / (math.pi / 180.0)
    if vy < uy and vx > ux:
        return 180.0 - (atan_deg + 90.0)
    if vy > uy and vx > ux:
        return atan_deg + 90.0
    if vy < uy and vx < ux:
        return 180.0 + (atan_deg + 90.0)
    if vy > uy and vx < ux:
        return 360.0 - (atan_deg + 90.0)
    return 0.0


def __sword_angle(this: CharType) -> int:
    """FB __sword_angle: 16-frame facing, nudged by 22.5/4 degrees."""
    hero = events.hero
    if hero is None:
        return 1
    sx, sy = _mid(this)
    hx, hy = _mid(hero)
    angle = _get_angle(sx, sy, hx, hy) + (22.5 / 4.0)
    if angle < 0:
        angle += 360.0
    elif angle >= 360.0:
        angle -= 360.0
    this.frame = int(angle / (360.0 / 16.0))
    return 1


def _sword_axes(this: CharType, scale: float, finish_on_block: bool) -> None:
    """One FB sword axis pair. The throw uses scale 2 and ends if a wall hits."""
    from lynn.map.collision import move_object

    room = events.current_room
    others = events.current_others
    this.fly_hold = int(this.direction)

    def _move(direction: int, moment: float) -> None:
        this.direction = direction
        if room is None:
            return
        moved = move_object(this, room, moment=moment, others=others)
        # A wall ends the throw. The Arx seed is impassable and the blade
        # starts inside it, so that object block must not cancel the fly.
        if finish_on_block and moved == 0:
            from lynn.map.collision import check_walk

            if check_walk(this, direction, room) == 0:
                this.fly_count = int(this.fly_length) - 1

    fly_y = float(this.fly_y)
    if fly_y > 0:
        _move(0, abs(fly_y) * scale)
    elif fly_y < 0:
        _move(2, abs(fly_y) * scale)
    fly_x = float(this.fly_x)
    if fly_x > 0:
        _move(3, abs(fly_x) * scale)
    elif fly_x < 0:
        _move(1, abs(fly_x) * scale)
    this.fly_timer = clock.timer + float(this.fly_speed or 0)
    this.direction = this.fly_hold


def __sword_fly(this: CharType) -> int:
    """FB __sword_fly: aim at Lynn once, then step at twice the unit vector."""
    hero = events.hero
    if this.fly_count == 0 and hero is not None:
        sx, sy = _mid(this)
        hx, hy = _mid(hero)
        this.fly_x, this.fly_y = _v2_calc_flyback(sx, sy, hx, hy)
    if this.fly_timer == 0:
        _sword_axes(this, 2.0, True)
        this.fly_count += 1
    if clock.timer >= this.fly_timer:
        this.fly_timer = 0
    if this.fly_count >= int(this.fly_length):
        this.fly_count = 0
        this.fly_timer = 0
        return 1
    return 0


def __sword_return(this: CharType) -> int:
    """FB __sword_return: fly back to Sterach, then reset when the mids meet."""
    from lynn.map.collision import check_bounds
    from lynn.object.combat import LLObject_ShiftState, LLObject_VectorPair

    sterach = _room_enemy(1)
    if sterach is not None:
        sx, sy = _mid(this)
        tx, ty = _mid(sterach)
        this.fly_x, this.fly_y = _v2_calc_flyback(sx, sy, tx, ty)
    if this.fly_timer == 0:
        _sword_axes(this, 1.0, False)
    if clock.timer >= this.fly_timer:
        this.fly_timer = 0
    if sterach is None:
        return 0
    if sterach.funcs.active_state != 1:
        # A killing blow already set dead. Shifting him back to the sword
        # reaction leaves dead set, so the death func never runs.
        if (
            sterach.dead == 0
            and sterach.hp > 0
            and check_bounds(LLObject_VectorPair(this), LLObject_VectorPair(sterach)) == 0
        ):
            LLObject_ShiftState(sterach, 1)
    else:
        sx, sy = _mid(this)
        tx, ty = _mid(sterach)
        if abs(tx - sx) < 1 and abs(ty - sy) < 1:
            LLObject_ShiftState(this, 0)
    return 0


def __sword_glow(this: CharType) -> int:
    """FB __sword_glow: toggle enemy[0] between the sword and the flash."""
    sword = _room_enemy(0)
    if sword is not None:
        sword.current_anim ^= 1
    return 1


def __sword_jump(this: CharType) -> int:
    """FB __sword_jump: Sterach sends enemy[0], the sword, into its throw."""
    sword = _room_enemy(0)
    if sword is not None:
        from lynn.object.combat import LLObject_ShiftState

        LLObject_ShiftState(sword, 1)
    return 1


def __check_for_dead_faces(this: CharType) -> int:
    """FB object_boss.bas: three dead Logosta faces start the crystal ending."""
    dead_face = 0
    faces = (u_boss5_left, u_boss5_right, u_boss5_down)
    for obj in events.current_others or []:
        if obj.unique_id in faces and obj.dead != 0:
            dead_face += 1
    if dead_face == 3:
        from lynn.object.combat import LLObject_ShiftState

        LLObject_ShiftState(this, 3)
    return 0


def __sterach_call(this: CharType) -> int:
    """FB __sterach_call: Sterach (enemy[1]) plays the arm-throw anim."""
    boss = _room_enemy(1)
    if boss is not None:
        boss.current_anim = 3
        boss.frame = 0
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
register_func("__push_lynn_back", __push_lynn_back)
register_func("__anger_flyback", __anger_flyback)
register_func("__anger_fireball_circle", __anger_fireball_circle)
register_func("__anger_kill_fireball", __anger_kill_fireball)
register_func("__anger_new_fireball", __anger_new_fireball)
register_func("__anger_middle", __anger_middle)
register_func("__anger_teleport", __anger_teleport)
register_func("__explode_jump", __explode_jump)
register_func("__anger_trigger", __anger_trigger)
register_func("__anger_shoot", __anger_shoot)
register_func("__anger_fireball2", __anger_fireball2)
register_func("__do_anger_proj", __do_anger_proj)
register_func("__sword_angle", __sword_angle)
register_func("__sword_fly", __sword_fly)
register_func("__sword_return", __sword_return)
register_func("__sword_glow", __sword_glow)
register_func("__sword_jump", __sword_jump)
register_func("__sterach_call", __sterach_call)
register_func("__check_for_dead_faces", __check_for_dead_faces)
