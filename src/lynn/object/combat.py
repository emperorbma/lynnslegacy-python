"""FB engine--object_damage.bas MAINAttack / DamageCalc / ProcessHurt (hero sapling hit)."""

from __future__ import annotations

import lynn.events as events
from lynn.constants import DF_MAIN_CHAR, TRUE
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


def LLObject_DeriveHurt(h: CharType) -> None:
    only = events.hero_only
    weap = only.weapon if only is not None else 0
    if h.invincible != 0:
        return
    if h.mace_weak != 0 and weap < 1:
        return
    if h.star_weak != 0 and weap < 2:
        return
    h.hurt = 2 ** weap


def LLObject_ProcessHurt(h: CharType) -> None:
    h.hp -= h.hurt
    if h.hurt < 0:
        LLObject_ClearDamage(h)
        return
    if h.hp > 0:
        if h.dmg_id == DF_MAIN_CHAR:
            LLObject_ShiftState(h, h.hit_state)
        return
    if h.dead == 0:
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
    only.attacking = TRUE
    if 0 <= hr.attack_state < len(hr.funcs.current_func):
        hr.funcs.current_func[hr.attack_state] = 0
