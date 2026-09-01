"""FB engine--gfx_LL.bas blit_hud / hud_BlitMain (hero HUD only; no enemy bars)."""

from __future__ import annotations

from dataclasses import dataclass, field

from lynn.gfx.image import LLSystem_ImageLoad, frame_surfaces
from lynn.gfx.palette import LLPalette
from lynn.hero import MainCharType
from lynn.object.char import CharType

HUD_HEALTH = "data/pictures/hud/HUD_health.spr"
HUD_ITEMS = "data/pictures/hud/HUD_items.spr"
HUD_CASH = "data/pictures/hud/cash.spr"
HUD_CASHNUMBERS = "data/pictures/hud/cashnumbers.spr"


@dataclass
class HudImages:
    """FB load_hudImage: img(0) health pips, img(1) items, img(2) $, img(3) digits."""

    img: list = field(default_factory=list)


def load_hud(palette: LLPalette) -> HudImages:
    hud = HudImages()
    hud.img = [
        frame_surfaces(LLSystem_ImageLoad(HUD_HEALTH), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_ITEMS), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_CASH), palette),
        frame_surfaces(LLSystem_ImageLoad(HUD_CASHNUMBERS), palette),
    ]
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


def blit_hud(canvas, hero: CharType, hero_only: MainCharType, hud: HudImages) -> None:
    """FB blit_hud: hearts, selected item, cash. No dungeon keys or enemy bars."""
    hud_BlitMain(canvas, hero, hud)
    items = hud.img[1] if len(hud.img) > 1 else []
    sel = hero_only.selected_item
    if items and 0 <= sel < len(items):
        canvas.blit(items[sel], (132, 8))
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
