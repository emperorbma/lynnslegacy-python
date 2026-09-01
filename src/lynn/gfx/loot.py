"""FB blit_enemy_loot: draw and pick up health/gold/silver drops."""

from __future__ import annotations

from lynn.gfx.image import LLSystem_ImageLoad, frame_surface
from lynn.gfx.palette import LLPalette
from lynn.map.collision import check_bounds
from lynn.object.char import CharType

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


def blit_enemy_loot(canvas, enemies: list[CharType], hero: CharType | None, cam_x: int, cam_y: int, drop_surfs: list) -> None:
    if not drop_surfs:
        return
    for obj in enemies:
        kind = obj.dropped
        if kind == 0:
            continue
        anim_i = kind - 1
        if anim_i < 0 or anim_i >= len(drop_surfs) or drop_surfs[anim_i] is None:
            continue
        if canvas is not None:
            canvas.blit(drop_surfs[anim_i], (int(obj.drop_x) - cam_x, int(obj.drop_y) - cam_y))
        if hero is None:
            continue
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
