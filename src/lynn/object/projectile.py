"""FB LLObject_*Projectiles / __do_proj / __trigger_projectile (orb and beam)."""

from __future__ import annotations

import math

import lynn.events as events
from lynn import clock
from lynn.constants import (
    DF_PROJ,
    DF_ROOM_ENEMY,
    PROJECTILE_8WAY,
    PROJECTILE_BEAM,
    PROJECTILE_CROSS,
    PROJECTILE_DIAGONAL,
    PROJECTILE_FIREBALL,
    PROJECTILE_NONE,
    PROJECTILE_ORB,
    PROJECTILE_SCHIZO,
    u_anger,
    u_dyssius,
    u_fbug,
    u_grult,
    u_ibug,
    u_steelstrider,
)

# FB engine--LL.bas IncrementProjectiles: cross, 8-way, and schizo share this fan.
_FAN_STYLES = (PROJECTILE_CROSS, PROJECTILE_8WAY, PROJECTILE_SCHIZO)
_RAD = math.pi / 180.0
from lynn.object.char import CharType, EntityProjectile
from lynn.object.dispatch import register_func


def _proj_wh(obj: CharType) -> tuple[int, int]:
    if obj.anim and 0 <= obj.proj_anim < len(obj.anim):
        anim = obj.anim[obj.proj_anim]
        return int(anim.x) or 16, int(anim.y) or 16
    return 16, 16


def LLObject_ClearProjectiles(obj: CharType) -> None:
    proj = obj.projectile
    if proj is None:
        return
    for pair in proj.coords:
        pair[0] = 0
        pair[1] = 0
    proj.plock = 0
    proj.active = 0
    proj.refreshTime = 0
    proj.saveDirection = 0
    proj.travelled = 0
    proj.sound = 0


def LLObject_InitializeProjectiles(obj: CharType) -> None:
    proj = obj.projectile
    if proj is None or not proj.coords:
        return
    if proj.saveDirection == 0:
        proj.direction = int(obj.direction) & 3
        proj.saveDirection = -1
    pw, ph = _proj_wh(obj)
    sx = (obj.coords_x + (int(obj.perimeter_x) >> 1)) - (pw >> 1)
    sy = (obj.coords_y + (int(obj.perimeter_y) >> 1)) - (ph >> 1)
    for pair in proj.coords:
        pair[0] = sx
        pair[1] = sy
    if obj.proj_style == PROJECTILE_BEAM and len(proj.coords) > 1:
        beam = 16
        d = proj.direction & 3
        if d == 0:
            proj.coords[1][0] = proj.coords[0][0]
            proj.coords[1][1] = proj.coords[0][1] - beam
        elif d == 1:
            proj.coords[1][0] = proj.coords[0][0] + beam
            proj.coords[1][1] = proj.coords[0][1]
        elif d == 2:
            proj.coords[1][0] = proj.coords[0][0]
            proj.coords[1][1] = proj.coords[0][1] + beam
        else:
            proj.coords[1][0] = proj.coords[0][0] - beam
            proj.coords[1][1] = proj.coords[0][1]


def LLObject_IncrementProjectiles(obj: CharType) -> None:
    proj = obj.projectile
    if proj is None or not proj.coords:
        return
    d = proj.direction & 3
    if obj.proj_style == PROJECTILE_ORB:
        if d == 0:
            proj.coords[0][1] -= 8
        elif d == 1:
            proj.coords[0][0] += 8
        elif d == 2:
            proj.coords[0][1] += 8
        else:
            proj.coords[0][0] -= 8
        return
    if obj.proj_style == PROJECTILE_DIAGONAL and len(proj.coords) >= 4:
        proj.coords[0][0] -= 1
        proj.coords[0][1] -= 1
        proj.coords[1][0] += 1
        proj.coords[1][1] -= 1
        proj.coords[2][0] += 1
        proj.coords[2][1] += 1
        proj.coords[3][0] -= 1
        proj.coords[3][1] += 1
        return
    if obj.proj_style in _FAN_STYLES:
        n = proj.projectiles or len(proj.coords)
        n = min(n, len(proj.coords))
        if n <= 0:
            return
        step = 360.0 / n
        angle = 0.0
        for i in range(n):
            proj.coords[i][0] += math.sin(angle * _RAD)
            proj.coords[i][1] += math.cos(angle * _RAD)
            angle += step
        return
    if obj.proj_style == PROJECTILE_BEAM and len(proj.coords) > 1:
        old = proj.coords[0][:]
        proj.coords[0][0] = proj.coords[1][0]
        proj.coords[0][1] = proj.coords[1][1]
        proj.coords[1][0] += proj.coords[1][0] - old[0]
        proj.coords[1][1] += proj.coords[1][1] - old[1]


def __trigger_projectile(this: CharType) -> int:
    """FB object_states.bas: projectile.active = proj_style."""
    if this.projectile is None:
        this.projectile = EntityProjectile()
    this.projectile.active = this.proj_style if this.proj_style else PROJECTILE_NONE
    if this.projectile.active == 0:
        this.projectile.active = 1
    return 1


def __do_proj(this: CharType) -> int:
    """FB object_etc.bas: init/step/expire an active projectile."""
    proj = this.projectile
    if proj is None or proj.active == 0:
        return 1
    # Firebugs and ice bugs burst on death. Every other corpse drops its shot.
    if this.dead != 0 and this.unique_id not in (u_fbug, u_ibug):
        LLObject_ClearProjectiles(this)
        return 1
    if proj.refreshTime == 0:
        if this.proj_style == PROJECTILE_BEAM and proj.sound == 0:
            from lynn.audio import play_sample, sound_beam

            play_sample(sound_beam)
            proj.sound = -1
        if proj.travelled == 0:
            LLObject_InitializeProjectiles(this)
        else:
            LLObject_IncrementProjectiles(this)
        proj.travelled += 1
        length = proj.length if proj.length else 20
        if proj.travelled >= length:
            LLObject_ClearProjectiles(this)
            return 1
        rate = 0.08
        if this.animControl and 0 <= this.proj_anim < len(this.animControl):
            rate = this.animControl[this.proj_anim].rate or rate
        proj.refreshTime = clock.timer + rate
    if clock.timer >= proj.refreshTime:
        proj.refreshTime = 0
    return 1


def LLObject_ProjectileDamage(enemies: list[CharType], hr: CharType) -> None:
    """FB ProjectileDamage: active orb/beam vs hero AABB."""
    from lynn.map.collision import check_bounds

    if hr.invincible != 0 or hr.dead != 0 or hr.dmg_id != 0:
        return
    for index, enemy in enumerate(enemies):
        if enemy is hr or enemy.dead != 0:
            continue
        proj = enemy.projectile
        grult_shot = enemy.unique_id == u_grult and getattr(enemy, "grult_proj_trig", 0) != 0
        anger_shot = enemy.unique_id == u_anger and getattr(enemy, "anger_proj_trig", 0) != 0
        boss_beam = enemy.unique_id in (u_dyssius, u_steelstrider)
        if proj is None or (proj.active == 0 and not grult_shot and not anger_shot and not boss_beam):
            continue
        pw, ph = _proj_wh(enemy)
        for specific, pair in enumerate(proj.coords):
            if not grult_shot and not anger_shot and not boss_beam and pair[0] == 0 and pair[1] == 0:
                continue
            origin = (pair[0], pair[1], pw, ph)
            if check_bounds(origin, (hr.coords_x, hr.coords_y, hr.perimeter_x, hr.perimeter_y)) != 0:
                continue
            hr.dmg_id = DF_ROOM_ENEMY | DF_PROJ
            hr.dmg_index = index
            hr.dmg_specific = specific
            from lynn.object.combat import LLObject_DamageCalc

            LLObject_DamageCalc(hr)
            if hr.dmg_id != 0:
                return


def enemy_proj_drawable(obj: CharType) -> bool:
    """FB blit_enemy draws a live projectile without checking projectile.active.

    Dyssius and Steelstrider never set active. Grult and Anger shots are
    separate y-sorted sprites, so this path stays off for those triggers.
    Cleared beams sit at (0, 0) and must not be drawn.
    """
    proj = getattr(obj, "projectile", None)
    if proj is None or proj.invisible != 0:
        return False
    if getattr(obj, "grult_proj_trig", 0) != 0 or getattr(obj, "anger_proj_trig", 0) != 0:
        return False
    if not proj.coords:
        return False
    fan = obj.proj_style in _FAN_STYLES or obj.proj_style == PROJECTILE_DIAGONAL
    if fan:
        if not any(pair[0] or pair[1] for pair in proj.coords):
            return False
    elif proj.coords[0][0] == 0 and proj.coords[0][1] == 0:
        return False
    boss_beam = obj.unique_id in (u_dyssius, u_steelstrider)
    if proj.active == 0 and not boss_beam:
        return False
    # FB draws the Dyssius beam and multi-shots on the first travel step.
    if proj.travelled == 1 and not boss_beam and not fan:
        return False
    return True


def blit_enemy_proj(canvas, obj: CharType, cam_x: int, cam_y: int, proj_surfs) -> None:
    """FB blit_enemy_proj for orbs, beams, fans, and boss fireballs."""
    proj = obj.projectile
    grult_shot = getattr(obj, "grult_proj_trig", 0) != 0
    anger_shot = getattr(obj, "anger_proj_trig", 0) != 0
    boss_beam = obj.unique_id in (u_dyssius, u_steelstrider)
    fan = obj.proj_style in _FAN_STYLES or obj.proj_style == PROJECTILE_DIAGONAL
    if proj is None or proj.invisible != 0 or not proj_surfs:
        return
    if proj.active == 0 and not grult_shot and not anger_shot and not boss_beam:
        return
    if not proj.coords:
        return
    if not any(pair[0] or pair[1] for pair in proj.coords):
        return
    # FB draws the Dyssius beam and multi-shots on the first travel step.
    if not grult_shot and not anger_shot and not boss_beam and not fan and proj.travelled == 1:
        return
    n = len(proj_surfs)
    if obj.proj_style in (PROJECTILE_ORB, PROJECTILE_FIREBALL) or grult_shot or anger_shot:
        fi = proj.travelled % n if n else 0
        canvas.blit(proj_surfs[fi], (int(proj.coords[0][0]) - cam_x, int(proj.coords[0][1]) - cam_y))
        return
    if fan:
        fi = proj.travelled % n if n else 0
        count = proj.projectiles or len(proj.coords)
        for pair in proj.coords[:count]:
            if pair[0] == 0 and pair[1] == 0:
                continue
            canvas.blit(proj_surfs[fi], (int(pair[0]) - cam_x, int(pair[1]) - cam_y))
        return
    if obj.proj_style == PROJECTILE_BEAM:
        fi = (proj.direction & 1) if n > 1 else 0
        if fi >= n:
            fi = 0
        for pair in proj.coords[:2]:
            canvas.blit(proj_surfs[fi], (int(pair[0]) - cam_x, int(pair[1]) - cam_y))


register_func("__trigger_projectile", __trigger_projectile)
register_func("__do_proj", __do_proj)
