"""FB engine--gfx_LL.bas blit_hud / hud_BlitMain / hud_BlitEnemies."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

import lynn.events as events
from lynn.constants import (
    u_antiwall,
    u_antiwall2,
    u_beetle,
    u_bombrock,
    u_boss5_down,
    u_boss5_left,
    u_boss5_right,
    u_bush,
    u_charger,
    u_coldrock,
    u_core,
    u_crate,
    u_crate_health,
    u_goldblock,
    u_greyrock,
    u_hotrock,
    u_swordie,
)
from lynn.gfx.image import LLSystem_ImageLoad, frame_surfaces
from lynn.gfx.palette import LLPalette
from lynn.hero import MainCharType
from lynn.macros import LLObject_IsWithin
from lynn.object.char import CharType

HUD_HEALTH = "data/pictures/hud/hud_health.spr"
HUD_ITEMS = "data/pictures/hud/hud_items.spr"
HUD_CASH = "data/pictures/hud/cash.spr"
HUD_CASHNUMBERS = "data/pictures/hud/cashnumbers.spr"
HUD_FULLBAR = "data/pictures/hud/fullbar.spr"
HUD_KEY = "data/pictures/hud/key.spr"
HUD_KEY2 = "data/pictures/hud/key2.spr"
HUD_MATERIALS2 = "data/pictures/hud/materials2.spr"
HUD_MATERIALS3 = "data/pictures/hud/materials3.spr"
HUD_STATUS = (
    "data/pictures/char/lynnstatus1.spr",
    "data/pictures/char/lynnstatus2.spr",
    "data/pictures/char/lynnstatus3.spr",
)
_HUD_NO_BARS = frozenset(
    {
        u_hotrock,
        u_coldrock,
        u_bush,
        u_crate,
        u_crate_health,
        u_greyrock,
        u_bombrock,
        u_beetle,
        u_charger,
        u_swordie,
        u_antiwall,
        u_antiwall2,
        u_goldblock,
    }
)


@dataclass
class HudImages:
    """FB load_hudImage + load_status_images (savImages)."""

    img: list = field(default_factory=list)
    sav_img: list = field(default_factory=list)
    bar_color: tuple[int, int, int] = (255, 255, 255)


def load_hud(palette: LLPalette) -> HudImages:
    hud = HudImages()
    hud.img = [
        frame_surfaces(LLSystem_ImageLoad(HUD_HEALTH), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_ITEMS), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_CASH), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_CASHNUMBERS), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_FULLBAR), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_KEY), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_KEY2), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_MATERIALS2), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_MATERIALS3), palette),
    ]
    hud.sav_img = [frame_surfaces(LLSystem_ImageLoad(path), palette) for path in HUD_STATUS]
    if len(palette.colors) > 26:
        hud.bar_color = palette.colors[26]
    return hud


def hud_pip_frame(hp: int, maxhp: int, p: int) -> int:
    """0 full, 1 empty (below maxhp), 2 locked. FB hud_BlitMain."""
    if hp > p:
        return 0
    if maxhp > p:
        return 1
    return 2


def hud_BlitMain(canvas, hero: CharType, hud: HudImages) -> None:
    pips = hud.img[0] if hud.img else []
    if len(pips) < 3:
        return
    for p in range(30):
        x_opt = ((p % 15) << 3) + 8
        y_opt = ((p // 15) << 3) + 8
        canvas.blit(pips[hud_pip_frame(hero.hp, hero.maxhp, p)], (x_opt, y_opt))


def hud_IsShowing(this: CharType) -> int:
    """FB hud_IsShowing: damaged (or boss) living on-map enemies."""
    dmgd = this.dmg_id != 0
    dying = this.dead != 0 and this.unique_id not in (
        u_boss5_right,
        u_boss5_left,
        u_boss5_down,
    )
    flick = this.invisible == 0
    hpgone = this.hp <= 0
    nodead = this.total_dead == 0
    core_ok = True if this.unique_id != u_core else (0 <= 725 < len(events.now) and events.now[725] != 0)
    elit = core_ok and this.isBoss != 0
    hero = events.hero
    no_change = hero is None or hero.switch_room == -1
    show_enemies = this.unique_id not in _HUD_NO_BARS
    return int(
        ((dmgd or elit or (dying and flick and hpgone)) and nodead and no_change) and show_enemies
    )


def hud_BlitEnemy(canvas, this: CharType, hud: HudImages, ctr: int) -> None:
    pips = hud.img[0] if hud.img else []
    if len(pips) < 2:
        return
    for p in range(60):
        x_opt = ((p % 15) << 3) + 8
        y_opt = ((p // 15) << 3) + 8
        dest = (x_opt + 146, y_opt + (ctr << 4))
        if this.hp > p:
            canvas.blit(pips[0], dest)
        elif this.maxhp > p:
            canvas.blit(pips[1], dest)


def hud_BlitEnemies(canvas, hud: HudImages, enemies, cam_x: int, cam_y: int) -> None:
    ctr = 0
    for enemy in enemies or []:
        if LLObject_IsWithin(enemy, cam_x, cam_y) == 0:
            continue
        if hud_IsShowing(enemy):
            hud_BlitEnemy(canvas, enemy, hud, ctr)
            ctr += 1


def blit_hud(
    canvas,
    hero: CharType,
    hero_only: MainCharType,
    hud: HudImages,
    enemies=None,
    cam_x: int = 0,
    cam_y: int = 0,
    is_dungeon: int = 0,
) -> None:
    """FB blit_hud: hearts, enemy bars, item, keys, cash, crazy-points bar."""
    hud_BlitMain(canvas, hero, hud)
    hud_BlitEnemies(canvas, hud, enemies, cam_x, cam_y)
    items = hud.img[1] if len(hud.img) > 1 else []
    sel = hero_only.selected_item
    if sel == 3:
        if hero_only.has_weapon == 2 and items:
            canvas.blit(items[0], (132, 8))
        elif 0 <= 1206 < len(events.now) and events.now[1206] and len(hud.img) > 8 and hud.img[8]:
            canvas.blit(hud.img[8][0], (132, 8))
        elif 0 <= 470 < len(events.now) and events.now[470] and len(hud.img) > 7 and hud.img[7]:
            canvas.blit(hud.img[7][0], (132, 8))
        elif items and 0 <= sel < len(items):
            canvas.blit(items[sel], (132, 8))
    elif items and 0 <= sel < len(items):
        canvas.blit(items[sel], (132, 8))
    if is_dungeon != 0:
        if hero_only.b_key != 0 and len(hud.img) > 6 and hud.img[6]:
            canvas.blit(hud.img[6][0], (8, 164))
        keys = hud.img[5] if len(hud.img) > 5 else []
        for key_put in range(max(0, int(hero.key))):
            if keys:
                canvas.blit(keys[0], (8 + (key_put * 8), 180))
    if len(hud.img) > 2 and hud.img[2]:
        canvas.blit(hud.img[2][0], (275, 8))
    money = hero.money
    if money < 0:
        money = 0
    if money > 999:
        money = 999
    hero.money = money
    digits = hud.img[3] if len(hud.img) > 3 else []
    mny = f"{money:03d}"
    for nums in range(3):
        d = ord(mny[nums]) - 48
        if digits and 0 <= d < len(digits):
            canvas.blit(digits[d], (289 + (nums << 3), 8))
    if hero_only.adrenaline is None:
        if len(hud.img) > 4 and hud.img[4]:
            canvas.blit(hud.img[4][0], (12, 24))
        ceiling = hero_only.crazy_points
        if ceiling > 100:
            ceiling = 100
        if ceiling > 0:
            pygame.draw.rect(canvas, hud.bar_color, pygame.Rect(15, 27, ceiling, 4))
