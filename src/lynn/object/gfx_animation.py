"""FB object--gfx_animation.bas — idle cycle only for this slice."""

from __future__ import annotations

import random

from lynn import clock
from lynn.object.char import CharType, MatExpl
from lynn.object.dispatch import register_func
from lynn.object.gfx_frame import LLObject_IncrementFrame

_explode_lynn_explo = 0


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


def _ensure_expl_slots(this: CharType, n: int) -> None:
    while len(this.explosion) < n:
        this.explosion.append(MatExpl())


def __explode(this: CharType) -> int:
    """FB object--gfx.bas: spawn/animate explosion particles on expl_anim."""
    import random

    from lynn.audio import play_sample, sound_explosion

    n = int(this.explosions)
    expl_i = int(this.expl_anim)
    anim = this.anim[expl_i] if this.anim and 0 <= expl_i < len(this.anim) else None
    if n <= 0 or anim is None or anim.frames <= 0:
        return 1
    _ensure_expl_slots(this, n)
    if this.expl_timer == 0:
        this.cur_expl += 1
        if this.cur_expl >= n:
            this.cur_expl = n
        this.expl_timer = clock.timer + float(this.expl_delay) + (random.random() * 0.1)
    if clock.timer >= this.expl_timer:
        this.expl_timer = 0
    ctrl = this.animControl[expl_i] if this.animControl and expl_i < len(this.animControl) else None
    rate = ctrl.rate if ctrl is not None else 0.1
    spr_w = int(anim.x)
    spr_h = int(anim.y)
    for do_expl in range(this.cur_expl):
        particle = this.explosion[do_expl]
        if particle.x == 0 and particle.y == 0:
            particle.alive = -1
            xo, yo = int(this.expl_x_off), int(this.expl_y_off)
            xs, ys = int(this.expl_x_size), int(this.expl_y_size)
            particle.x = int(this.coords_x) + xo - (spr_w // 2)
            particle.y = int(this.coords_y) + yo - (spr_h // 2)
            if xs != 0:
                particle.x += int(random.random() * xs)
            else:
                particle.x += int(random.random() * (this.perimeter_x or 1))
            if ys != 0:
                particle.y += int(random.random() * ys)
            else:
                particle.y += int(random.random() * (this.perimeter_y or 1))
        if particle.alive != 0:
            if particle.frame <= int(random.random() * anim.frames):
                if particle.sound == 0:
                    particle.sound = -1
                    play_sample(sound_explosion, 70)
            if particle.frame_hold == 0:
                particle.frame += 1
                if particle.frame == anim.frames:
                    particle.frame = 0
                    particle.alive = 0
                particle.frame_hold = clock.timer + rate
            if clock.timer >= particle.frame_hold:
                particle.frame_hold = 0
    ver = -1
    for do_expl in range(n):
        alive = this.explosion[do_expl].alive if do_expl < len(this.explosion) else 0
        ver = ver & (-1 if alive == 0 else 0)
    if ver != 0:
        for do_expl in range(n):
            particle = this.explosion[do_expl]
            particle.x = 0
            particle.y = 0
            particle.frame = 0
            particle.alive = 0
            particle.sound = 0
        this.cur_expl = 0
        this.expl_timer = 0
        if this.isBoss != 0:
            return 3
        if this.fireworks != 0:
            return 1
    if this.fireworks == 0:
        return 1
    return 0


def __explode_lynn(this: CharType) -> int:
    """FB object--gfx_animation.bas: one explosion.ogg, pin sprite to Lynn, play once."""
    global _explode_lynn_explo
    from lynn.audio import play_sample, sound_explosion
    import lynn.events as events

    this.animating = 1
    this.invisible = 0
    if _explode_lynn_explo == 0:
        play_sample(sound_explosion)
        _explode_lynn_explo += 1
    hero = events.hero
    if hero is not None:
        this.coords_x = hero.coords_x - 24
        this.coords_y = hero.coords_y - 24
    anim = this.anim[this.current_anim] if this.anim and this.current_anim < len(this.anim) else None
    if anim is None or anim.frames <= 0:
        _explode_lynn_explo = 0
        this.animating = 0
        return 1
    if LLObject_IncrementFrame(this) != 0:
        this.frame = 0
        rate = this.animControl[this.current_anim].rate if this.animControl else 0.08
        this.frame_hold = clock.timer + rate
        _explode_lynn_explo = 0
        this.animating = 0
        return 1
    return 0


register_func("__gen_frame", __gen_frame)
register_func("__idle_animate", __idle_animate)
register_func("__active_animate", __active_animate)
register_func("__active_animate_x", __active_animate)
register_func("__explode", __explode)
register_func("__explode_lynn", __explode_lynn)
