"""FB blit_enemy_loot: draw and pick up health/gold/silver drops."""

from __future__ import annotations

from lynn.constants import u_gold, u_health, u_silver
from lynn.gfx.image import LLSystem_ImageLoad, frame_surface
from lynn.gfx.palette import LLPalette
from lynn.map.collision import check_bounds
from lynn.object.char import CharType

_DROP_UNIQUES = {u_gold, u_silver, u_health}
DROP_H = 8

DROP_SPRITES = (
    "data/pictures/char/helth.spr",
    "data/pictures/char/gold.spr",
    "data/pictures/char/silver.spr",
)


def load_drop_surfs(palette: LLPalette) -> list:
    surfs = []
    for path in DROP_SPRITES:
        header = LLSystem_ImageLoad(path)
        surfs.append(frame_surface(header, 0, palette) if header.frames else None)
    return surfs


def is_corpse_drop(obj: CharType) -> bool:
    """FB blit_enemy_loot skip: unique gold/silver/health are y-sorted objects, not overlays."""
    if obj.dropped == 0:
        return False
    return obj.unique_id not in _DROP_UNIQUES


def drop_sort_y(obj: CharType) -> tuple:
    """Same key as entity y-sort: placed then mid-y of the 8x8 drop."""
    return (0, int(obj.drop_y) + (DROP_H >> 1))


def blit_drop(canvas, obj: CharType, cam_x: int, cam_y: int, drop_surfs: list) -> None:
    if canvas is None or not drop_surfs:
        return
    anim_i = int(obj.dropped) - 1
    if anim_i < 0 or anim_i >= len(drop_surfs) or drop_surfs[anim_i] is None:
        return
    canvas.blit(drop_surfs[anim_i], (int(obj.drop_x) - cam_x, int(obj.drop_y) - cam_y))


def hero_touches_loot(hero: CharType, x: float, y: float) -> bool:
    """FB blit_enemy_loot: weapon faces if present, else the body box."""
    from lynn.macros import LLObject_CalculateFrame
    from lynn.object.combat import LLObject_VectorPair, LLObject_VectorPairEx, _faces

    target = (x, y, 8, 8)
    hero.frame_check = LLObject_CalculateFrame(hero)
    n = _faces(hero)
    if n <= 0:
        return check_bounds(LLObject_VectorPair(hero), target) == 0
    for face_i in range(n):
        if check_bounds(LLObject_VectorPairEx(hero, face_i), target) == 0:
            return True
    return False


def grant_loot(hero: CharType, kind: int, obj: CharType) -> None:
    if kind == 1:
        if hero.hp < hero.maxhp:
            hero.hp += 1
        from lynn.audio import play_sample, sound_healthgrab

        play_sample(sound_healthgrab)
    elif kind == 2:
        hero.money += int(obj.n_gold) * 5
        from lynn.audio import play_sample, sound_cashget

        play_sample(sound_cashget)
    elif kind == 3:
        hero.money += int(obj.n_silver)
        from lynn.audio import play_sample, sound_cashget

        play_sample(sound_cashget)


def LLObject_GrabItems(obj: CharType) -> None:
    """FB LLObject_GrabItems: unique gold/silver/health piles on the floor."""
    import lynn.events as events
    from lynn.object.dispatch import lookup_func

    hero = events.hero
    if obj.dead != 0 or hero is None or obj.dropped == 0:
        return
    if not hero_touches_loot(hero, obj.coords_x, obj.coords_y):
        return
    grant_loot(hero, obj.dropped, obj)
    obj.dropped = 0
    lookup_func("__make_dead")(obj)
    lookup_func("__cripple")(obj)


def blit_enemy_loot(canvas, enemies: list[CharType], hero: CharType | None, cam_x: int, cam_y: int, drop_surfs: list) -> None:
    """Pick up corpse drops. Drawing is done in the y-sorted pass."""
    for obj in enemies:
        if not is_corpse_drop(obj):
            continue
        if hero is None:
            continue
        if not hero_touches_loot(hero, obj.drop_x, obj.drop_y):
            continue
        grant_loot(hero, obj.dropped, obj)
        obj.dropped = 0
