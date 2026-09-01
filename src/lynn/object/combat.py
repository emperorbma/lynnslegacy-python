"""FB engine--object_damage.bas MAINAttack / DamageCalc / ProcessHurt (hero sapling hit)."""

from __future__ import annotations

import lynn.events as events
from lynn.constants import DF_MAIN_CHAR, DF_ROOM_ENEMY, DF_TEMP_ENEMY, TRUE
from lynn.macros import LLObject_CalculateFrame
from lynn.map.collision import check_bounds
from lynn.object.char import CharType


def LLObject_ShiftState(h: CharType, s: int) -> None:
    h.funcs.current_func[h.funcs.active_state] = 0
    h.funcs.active_state = s
    if 0 <= s < len(h.funcs.current_func):
        h.funcs.current_func[s] = 0


def LLObject_ClearDamage(h: CharType) -> None:
    h.hurt = 0
    h.dmg_id = 0
    h.dmg_index = 0
    h.dmg_specific = 0


def LLObject_VectorPair(o: CharType) -> tuple:
    return (o.coords_x, o.coords_y, o.perimeter_x, o.perimeter_y)


def LLObject_VectorPairEx(o: CharType, face_i: int) -> tuple:
    x = o.coords_x
    y = o.coords_y
    if o.animControl and o.current_anim < len(o.animControl):
        x -= o.animControl[o.current_anim].x_off
        y -= o.animControl[o.current_anim].y_off
    fi = o.frame_check
    if o.anim and o.current_anim < len(o.anim):
        frames = o.anim[o.current_anim].frame
        if 0 <= fi < len(frames) and 0 <= face_i < len(frames[fi].face):
            face = frames[fi].face[face_i]
            return (x + face.x, y + face.y, face.w, face.h)
    return LLObject_VectorPair(o)


def _faces(o: CharType) -> int:
    fi = o.frame_check
    if o.anim and o.current_anim < len(o.anim):
        frames = o.anim[o.current_anim].frame
        if 0 <= fi < len(frames):
            return frames[fi].faces
    return 0


def hero_attack(hr: CharType) -> None:
    """FB hero_attack: run attack_state until the swing block finishes."""
    st = hr.attack_state
    f = hr.funcs
    if st < 0 or st >= len(f.func) or not f.func[st]:
        if events.hero_only is not None:
            events.hero_only.attacking = 0
        return
    count = f.func_count[st] if st < len(f.func_count) else len(f.func[st])
    idx = f.current_func[st]
    if idx < 0 or idx >= len(f.func[st]):
        idx = 0
        f.current_func[st] = 0
    result = f.func[st][idx](hr)
    f.current_func[st] += result
    if f.current_func[st] >= count:
        f.current_func[st] = 0
        if events.hero_only is not None:
            events.hero_only.attacking = 0
        hr.psycho = 0


def _damager(h: CharType) -> CharType | None:
    others = events.current_others
    if others is None:
        return None
    i = h.dmg_index
    if 0 <= i < len(others):
        return others[i]
    return None


def _face_strength(enemy: CharType, specific: int) -> int:
    fi = enemy.frame_check
    if enemy.anim and enemy.current_anim < len(enemy.anim):
        frames = enemy.anim[enemy.current_anim].frame
        if 0 <= fi < len(frames):
            shell = frames[fi]
            if shell.faces == 0:
                return int(enemy.strength)
            if 0 <= specific < len(shell.face):
                return int(shell.face[specific].strength)
    return int(enemy.strength)


def LLObject_DeriveHurt(h: CharType) -> None:
    only = events.hero_only
    weap = only.weapon if only is not None else 0
    if h.dmg_id in (DF_ROOM_ENEMY, DF_TEMP_ENEMY):
        enemy = _damager(h)
        if enemy is None:
            return
        h.hurt = _face_strength(enemy, h.dmg_specific)
        return
    if h.invincible != 0:
        return
    if h.mace_weak != 0 and weap < 1:
        return
    if h.star_weak != 0 and weap < 2:
        return
    h.hurt = 2 ** weap


def _set_fly_from(h: CharType, origin_x: float, origin_y: float) -> None:
    dx = h.coords_x - origin_x
    dy = h.coords_y - origin_y
    h.fly_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
    h.fly_y = 1 if dy > 0 else (-1 if dy < 0 else 0)


def _play_hurt_sound(h: CharType) -> None:
    from lynn.audio import play_sample, sound_lynn_hurt_1
    from lynn.constants import u_lynn
    import random

    if h.unique_id == u_lynn:
        play_sample(sound_lynn_hurt_1 + int(random.random() * 3), 50)
        return
    if h.hit_sound != 0:
        vol = h.hit_sound_vol if h.hit_sound_vol != 0 else 100
        play_sample(h.hit_sound, vol)


def _play_dead_sound(h: CharType) -> None:
    from lynn.audio import play_sample
    from lynn.constants import u_lynn

    if h.dead_sound == 0:
        return
    if h.unique_id == u_lynn:
        play_sample(h.dead_sound, 30)
    else:
        play_sample(h.dead_sound)


def LLObject_ProcessHurt(h: CharType) -> None:
    h.hp -= h.hurt
    if h.hurt < 0:
        LLObject_ClearDamage(h)
        return
    if h.hp > 0:
        _play_hurt_sound(h)
        if h.dmg_id == DF_MAIN_CHAR:
            LLObject_ShiftState(h, h.hit_state)
        elif h.dmg_id in (DF_ROOM_ENEMY, DF_TEMP_ENEMY):
            enemy = _damager(h)
            if enemy is not None:
                _set_fly_from(h, enemy.coords_x, enemy.coords_y)
        return
    if h.dead == 0:
        _play_dead_sound(h)
        LLObject_ShiftState(h, h.death_state)
        h.dead = 1
    LLObject_ClearDamage(h)


def LLObject_DamageCalc(h: CharType) -> None:
    LLObject_DeriveHurt(h)
    if h.hurt != 0:
        LLObject_ProcessHurt(h)
    else:
        LLObject_ClearDamage(h)
    h.frame_check = 0


def LLObject_MAINAttack(enemies: list[CharType], hr: CharType) -> None:
    """FB MAINAttack: hero weapon faces vs living enemies."""
    hr.frame_check = LLObject_CalculateFrame(hr)
    hero_faces = _faces(hr)
    if hero_faces <= 0:
        return
    for enemy in enemies:
        if enemy is hr or enemy.dead != 0 or enemy.dmg_id != 0:
            continue
        enemy.frame_check = LLObject_CalculateFrame(enemy)
        for face_i in range(hero_faces):
            origin = LLObject_VectorPairEx(hr, face_i)
            target = LLObject_VectorPair(enemy)
            if check_bounds(origin, target) != 0:
                continue
            enemy.dmg_id = DF_MAIN_CHAR
            enemy.dmg_index = 0
            LLObject_DamageCalc(enemy)
            if enemy.hp > 0:
                dx = enemy.coords_x - hr.coords_x
                dy = enemy.coords_y - hr.coords_y
                enemy.fly_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
                enemy.fly_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
            if enemy.dmg_id != 0:
                break


def start_hero_attack(hr: CharType) -> None:
    only = events.hero_only
    if only is None or only.weapon == -1 or only.attacking != 0:
        return
    if only.action_lock != 0 or hr.dead != 0:
        return
    only.attacking = TRUE
    if 0 <= hr.attack_state < len(hr.funcs.current_func):
        hr.funcs.current_func[hr.attack_state] = 0


def LLObject_ObjectDamage(enemies: list[CharType], hr: CharType, e_type: int = DF_ROOM_ENEMY) -> None:
    """FB ObjectDamage: living enemies with strength vs hero AABB."""
    if hr.invincible != 0:
        return
    for enemy_collide, enemy in enumerate(enemies):
        if enemy is hr or int(enemy.strength) == 0:
            continue
        enemy.frame_check = LLObject_CalculateFrame(enemy)
        faces = _faces(enemy)
        if faces <= 0:
            if check_bounds(LLObject_VectorPair(enemy), LLObject_VectorPair(hr)) != 0:
                continue
            hr.dmg_id = e_type
            hr.dmg_index = enemy_collide
            hr.dmg_specific = 0
            LLObject_DamageCalc(hr)
            if hr.dmg_id != 0:
                return
            continue
        for check_fields in range(faces):
            origin = LLObject_VectorPairEx(enemy, check_fields)
            if check_bounds(origin, LLObject_VectorPair(hr)) != 0:
                continue
            hr.dmg_id = e_type
            hr.dmg_index = enemy_collide
            hr.dmg_specific = check_fields
            LLObject_DamageCalc(hr)
            if hr.dmg_id != 0:
                return


def LLObject_MAINDamage(hr: CharType, enemies: list[CharType] | None = None) -> None:
    """FB MAINDamage: contact (projectiles later). i-frames are dmg_id != 0."""
    if hr.invincible != 0 or hr.dead != 0:
        return
    if hr.dmg_id != 0:
        return
    room_enemies = enemies if enemies is not None else (events.current_others or [])
    LLObject_ObjectDamage(room_enemies, hr, DF_ROOM_ENEMY)


def hero_hurt_tick(hr: CharType) -> None:
    """FB engine--LL.bas: while hurt, run hit_state (do_flyback) until it wraps."""
    if hr.hurt == 0:
        return
    st = hr.hit_state
    f = hr.funcs
    if st < 0 or st >= len(f.func) or not f.func[st]:
        hr.hurt = 0
        return
    count = f.func_count[st] if st < len(f.func_count) else len(f.func[st])
    idx = f.current_func[st]
    if idx < 0 or idx >= len(f.func[st]):
        idx = 0
        f.current_func[st] = 0
    result = f.func[st][idx](hr)
    f.current_func[st] += result
    if f.current_func[st] >= count:
        f.current_func[st] = 0
        hr.hurt = 0
        hr.dmg_index = 0
        hr.dmg_specific = 0


def hero_death_tick(hr: CharType) -> None:
    """FB: run death_state until it wraps. Title jump is later."""
    if hr.dead == 0:
        return
    st = hr.death_state
    f = hr.funcs
    if st < 0 or st >= len(f.func) or not f.func[st]:
        return
    count = f.func_count[st] if st < len(f.func_count) else len(f.func[st])
    if count == 0:
        return
    idx = f.current_func[st]
    if idx >= count:
        return
    if idx < 0 or idx >= len(f.func[st]):
        return
    result = f.func[st][idx](hr)
    f.current_func[st] += result
