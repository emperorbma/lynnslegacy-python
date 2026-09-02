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


def blit_enemy_loot(canvas, enemies: list[CharType], hero: CharType | None, cam_x: int, cam_y: int, drop_surfs: list) -> None:
    """Pick up drops. Drawing is done in the y-sorted pass."""
    for obj in enemies:
        if not is_corpse_drop(obj):
            continue
        if hero is None:
            continue
        kind = obj.dropped
        origin = (hero.coords_x, hero.coords_y, hero.perimeter_x, hero.perimeter_y)
        target = (obj.drop_x, obj.drop_y, 8, 8)
        if check_bounds(origin, target) != 0:
            continue
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
        obj.dropped = 0
