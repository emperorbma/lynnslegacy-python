"""FB engine--gfx_LL.bas menu_Blit + engine--LL.bas menu_Input (keyboard)."""

from __future__ import annotations

from dataclasses import dataclass, field

from lynn.constants import TRUE
from lynn.gfx.image import LLSystem_ImageLoad, frame_surfaces
from lynn.gfx.palette import LLPalette
from lynn.hero import MainCharType

# FB ll_menu_gfx
menu_blankspace = 0
menu_bridge = 1
menu_bridge_select = 2
menu_bridge2 = 3
menu_bridge2_select = 4
menu_bridge3 = 5
menu_bridge3_select = 6
menu_blank = 7
menu_blank_select = 8
menu_flare = 9
menu_flare_select = 10
menu_full_background = 11
menu_heal = 12
menu_heal_select = 13
menu_ice = 14
menu_ice_select = 15
menu_idol = 16
menu_idol_select = 17
menu_mace = 18
menu_mace_select = 19
menu_menu_select = 20
menu_regen = 21
menu_regen_select = 22
menu_resume_select = 23
menu_sapling = 24
menu_sapling_select = 25
menu_square_cursor = 26
menu_star = 27
menu_star_select = 28
menu_cougar = 29
menu_lynnity = 30
menu_ninja = 31
menu_standard = 32
menu_cougar_select = 33
menu_lynnity_select = 34
menu_ninja_select = 35
menu_standard_select = 36
menu_bikini = 37
menu_bikini_select = 38
menu_rknight = 39
menu_rknight_select = 40
menu_MAX = 41

_MENU_PATHS = (
    "data/pictures/menu/blankspace.spr",
    "data/pictures/menu/bridge.spr",
    "data/pictures/menu/bridge_select.spr",
    "data/pictures/menu/bridge2.spr",
    "data/pictures/menu/bridge2_select.spr",
    "data/pictures/menu/bridge3.spr",
    "data/pictures/menu/bridge3_select.spr",
    "data/pictures/menu/item_blank.spr",
    "data/pictures/menu/item_blank_select.spr",
    "data/pictures/menu/flare.spr",
    "data/pictures/menu/flare_select.spr",
    "data/pictures/menu/full_background.spr",
    "data/pictures/menu/heal.spr",
    "data/pictures/menu/heal_select.spr",
    "data/pictures/menu/ice.spr",
    "data/pictures/menu/ice_select.spr",
    "data/pictures/menu/idol.spr",
    "data/pictures/menu/idol_select.spr",
    "data/pictures/menu/mace.spr",
    "data/pictures/menu/mace_select.spr",
    "data/pictures/menu/menu_select.spr",
    "data/pictures/menu/regen.spr",
    "data/pictures/menu/regen_select.spr",
    "data/pictures/menu/resume_select.spr",
    "data/pictures/menu/sapling.spr",
    "data/pictures/menu/sapling_select.spr",
    "data/pictures/menu/square_cursor.spr",
    "data/pictures/menu/star.spr",
    "data/pictures/menu/star_select.spr",
    "data/pictures/char/outfits/cougar/icon.spr",
    "data/pictures/char/outfits/lynnity/icon.spr",
    "data/pictures/char/outfits/ninja/icon.spr",
    "data/pictures/char/icon.spr",
    "data/pictures/char/outfits/cougar/icon_select.spr",
    "data/pictures/char/outfits/lynnity/icon_select.spr",
    "data/pictures/char/outfits/ninja/icon_select.spr",
    "data/pictures/char/icon_select.spr",
    "data/pictures/char/outfits/swimsuit/icon.spr",
    "data/pictures/char/outfits/swimsuit/icon_select.spr",
    "data/pictures/char/outfits/redknight/icon.spr",
    "data/pictures/char/outfits/redknight/icon_select.spr",
)

# selectedItem -> (up, right, down, left)
MENU_NAV = {
    0: (12, 1, 3, 18),
    1: (13, 2, 4, 0),
    2: (14, 18, 5, 1),
    3: (0, 4, 6, 18),
    4: (1, 5, 7, 3),
    5: (2, 18, 8, 4),
    6: (3, 7, 9, 19),
    7: (4, 8, 10, 6),
    8: (5, 19, 11, 7),
    9: (6, 10, 12, 19),
    10: (7, 11, 13, 9),
    11: (8, 19, 14, 10),
    12: (9, 13, 0, 14),
    13: (10, 14, 1, 12),
    14: (11, 12, 2, 13),
    18: (19, 3, 19, 5),
    19: (18, 6, 18, 8),
}

CURSOR_XY = {
    0: (18, 18),
    1: (42, 18),
    2: (66, 18),
    3: (18, 54),
    4: (42, 54),
    5: (66, 54),
    6: (18, 78),
    7: (42, 78),
    8: (66, 78),
    9: (18, 121),
    10: (42, 121),
    11: (66, 121),
    12: (18, 157),
    13: (42, 157),
    14: (66, 157),
    18: (126, 54),
    19: (126, 90),
}


@dataclass
class MainMenu:
    """FB ll_mainmenu."""

    selectedItem: int = 18
    img: list = field(default_factory=list)
    menuNames: list = field(default_factory=list)
    font: list = field(default_factory=list)


def load_menu(palette: LLPalette) -> MainMenu:
    menu = MainMenu()
    menu.img = []
    for path in _MENU_PATHS:
        surfs = frame_surfaces(LLSystem_ImageLoad(path), palette)
        menu.img.append(surfs[0] if surfs else None)
    menu.menuNames = [""] * menu_MAX
    menu.menuNames[menu_bridge_select] = "Some old scraps."
    menu.menuNames[menu_flare_select] = "Flare Powder."
    menu.menuNames[menu_ice_select] = "Ice Powder."
    menu.menuNames[menu_idol_select] = "An ancient treasure."
    menu.menuNames[menu_regen_select] = "Adrenaline Booster."
    menu.menuNames[menu_heal_select] = "Healing Symbol."
    menu.menuNames[menu_sapling_select] = "A small sapling."
    menu.menuNames[menu_mace_select] = "My old mace."
    menu.menuNames[menu_star_select] = "Handcrafted 0wnage."
    menu.menuNames[menu_standard_select] = "Normal outfit."
    menu.menuNames[menu_cougar_select] = "Mew..."
    menu.menuNames[menu_lynnity_select] = "Tight Leather."
    menu.menuNames[menu_ninja_select] = "..."
    menu.menuNames[menu_bikini_select] = "Not very practical..."
    menu.menuNames[menu_rknight_select] = "Regenerative power."
    menu.menuNames[menu_menu_select] = "Back to title screen."
    menu.menuNames[menu_resume_select] = "Back to the game."
    menu.font = [_crop_glyph(s) for s in frame_surfaces(LLSystem_ImageLoad("data/pictures/llfont.spr"), palette)]
    return menu


def _crop_glyph(surf):
    """llfont cells are 9x17 with ~8x11 ink. Crop to 8x12 so UI type isn't so tall."""
    w, h = surf.get_width(), surf.get_height()
    if w >= 8 and h >= 14:
        return surf.subsurface((0, 2, 8, 12)).copy()
    return surf


def graphicalString(canvas, menu: MainMenu, text: str, x: int, y: int) -> None:
    """FB graphicalString: 8px advance, glyph = ASCII index into llfont.spr."""
    origin_x = x
    for ch in text:
        if ch == "\n":
            y += 16
            x = origin_x
            continue
        idx = ord(ch)
        if 0 <= idx < len(menu.font) and menu.font[idx] is not None:
            canvas.blit(menu.font[idx], (x, y))
        x += 8


def _blit_i(canvas, menu: MainMenu, x: int, y: int, i: int) -> None:
    if 0 <= i < len(menu.img) and menu.img[i] is not None:
        canvas.blit(menu.img[i], (x, y))


def _slot(canvas, menu, x, y, owned, selected, icon, icon_sel) -> None:
    if owned:
        _blit_i(canvas, menu, x, y, icon_sel if selected else icon)
    else:
        _blit_i(canvas, menu, x, y, menu_blankspace)


def menu_Blit(canvas, menu: MainMenu, hero_only: MainCharType) -> None:
    """FB menu_Blit. Plot-gated bridge/idol variants omitted until llg(now)."""
    _blit_i(canvas, menu, 0, 0, menu_full_background)
    hw = hero_only.has_weapon
    weap = hero_only.weapon
    _slot(canvas, menu, 18, 18, hw >= 0, weap == 0, menu_sapling, menu_sapling_select)
    _slot(canvas, menu, 42, 18, hw >= 1, weap == 1, menu_mace, menu_mace_select)
    _slot(canvas, menu, 66, 18, hw >= 2, weap == 2, menu_star, menu_star_select)

    items = hero_only.hasItem
    sel = hero_only.selected_item
    _slot(canvas, menu, 18, 54, items[0] != 0, sel == 1, menu_flare, menu_flare_select)
    _slot(canvas, menu, 42, 54, items[1] != 0, sel == 2, menu_ice, menu_ice_select)
    if items[2] != 0:
        if weap == 2:
            bridge, bridge_sel = menu_blank, menu_blank_select
        else:
            bridge, bridge_sel = menu_bridge, menu_bridge_select
        _blit_i(canvas, menu, 66, 54, bridge_sel if sel == 3 else bridge)
    else:
        _blit_i(canvas, menu, 66, 54, menu_blankspace)
    _slot(canvas, menu, 18, 78, items[3] != 0, sel == 4, menu_idol, menu_idol_select)
    _slot(canvas, menu, 42, 78, items[4] != 0, sel == 5, menu_regen, menu_regen_select)
    _slot(canvas, menu, 66, 78, items[5] != 0, sel == 6, menu_heal, menu_heal_select)

    cos = hero_only.hasCostume
    wear = hero_only.isWearing
    _slot(canvas, menu, 18, 121, cos[0] != 0, wear == 0, menu_standard, menu_standard_select)
    _slot(canvas, menu, 42, 121, cos[1] != 0, wear == 1, menu_cougar, menu_cougar_select)
    _slot(canvas, menu, 66, 121, cos[2] != 0, wear == 2, menu_lynnity, menu_lynnity_select)
    _slot(canvas, menu, 18, 157, cos[3] != 0, wear == 3, menu_ninja, menu_ninja_select)
    _slot(canvas, menu, 42, 157, cos[4] != 0, wear == 4, menu_bikini, menu_bikini_select)
    _slot(canvas, menu, 66, 157, cos[5] != 0, wear == 5, menu_rknight, menu_rknight_select)

    i = menu.selectedItem
    name = _hover_name(menu, hero_only, i)
    if name:
        graphicalString(canvas, menu, name, 134, 154)
    if i == 18:
        _blit_i(canvas, menu, 126, 54, menu_resume_select)
    elif i == 19:
        _blit_i(canvas, menu, 126, 90, menu_menu_select)
    elif i in CURSOR_XY:
        x, y = CURSOR_XY[i]
        _blit_i(canvas, menu, x, y, menu_square_cursor)


def _hover_name(menu: MainMenu, hero_only: MainCharType, i: int) -> str:
    hw = hero_only.has_weapon
    items = hero_only.hasItem
    cos = hero_only.hasCostume
    names = {
        0: menu.menuNames[menu_sapling_select] if hw >= 0 else "",
        1: menu.menuNames[menu_mace_select] if hw >= 1 else "",
        2: menu.menuNames[menu_star_select] if hw >= 2 else "",
        3: menu.menuNames[menu_flare_select] if items[0] != 0 else "",
        4: menu.menuNames[menu_ice_select] if items[1] != 0 else "",
        5: (
            "Nothing left!"
            if items[2] != 0 and hero_only.weapon == 2
            else (menu.menuNames[menu_bridge_select] if items[2] != 0 else "")
        ),
        6: menu.menuNames[menu_idol_select] if items[3] != 0 else "",
        7: menu.menuNames[menu_regen_select] if items[4] != 0 else "",
        8: menu.menuNames[menu_heal_select] if items[5] != 0 else "",
        9: menu.menuNames[menu_standard_select] if cos[0] != 0 else "",
        10: menu.menuNames[menu_cougar_select] if cos[1] != 0 else "",
        11: menu.menuNames[menu_lynnity_select] if cos[2] != 0 else "",
        12: menu.menuNames[menu_ninja_select] if cos[3] != 0 else "",
        13: menu.menuNames[menu_bikini_select] if cos[4] != 0 else "",
        14: menu.menuNames[menu_rknight_select] if cos[5] != 0 else "",
        18: menu.menuNames[menu_resume_select] if hw >= 0 else "",
        19: menu.menuNames[menu_menu_select] if hw >= 0 else "",
    }
    return names.get(i, "")


def keyboardSelected(menu: MainMenu, key_up: int, key_right: int, key_down: int, key_left: int) -> None:
    """FB keyboardSelected: one Select Case on the current slot. Later keys win."""
    nav = MENU_NAV.get(menu.selectedItem)
    if nav is None:
        return
    up, right, down, left = nav
    if key_up == TRUE:
        menu.selectedItem = up
    if key_right == TRUE:
        menu.selectedItem = right
    if key_down == TRUE:
        menu.selectedItem = down
    if key_left == TRUE:
        menu.selectedItem = left


def handleKeybSelected(menu: MainMenu, hero_only: MainCharType) -> int:
    """FB handleKeybSelected. TRUE if the pause loop should close. Title (19) is a no-op until enter_map."""
    i = menu.selectedItem
    if i == 0 and hero_only.has_weapon >= 0:
        hero_only.weapon = 0
    elif i == 1 and hero_only.has_weapon >= 1:
        hero_only.weapon = 1
    elif i == 2 and hero_only.has_weapon >= 2:
        hero_only.weapon = 2
    elif i == 3 and hero_only.hasItem[0] != 0:
        hero_only.selected_item = 1
    elif i == 4 and hero_only.hasItem[1] != 0:
        hero_only.selected_item = 2
    elif i == 5 and hero_only.hasItem[2] != 0:
        hero_only.selected_item = 3
    elif i == 6 and hero_only.hasItem[3] != 0:
        hero_only.selected_item = 4
    elif i == 7 and hero_only.hasItem[4] != 0:
        hero_only.selected_item = 5
    elif i == 8 and hero_only.hasItem[5] != 0:
        hero_only.selected_item = 6
    elif i == 9 and hero_only.hasCostume[0] != 0:
        hero_only.isWearing = 0
    elif i == 10 and hero_only.hasCostume[1] != 0:
        hero_only.isWearing = 1
    elif i == 11 and hero_only.hasCostume[2] != 0:
        hero_only.isWearing = 2
    elif i == 12 and hero_only.hasCostume[3] != 0:
        hero_only.isWearing = 3
    elif i == 13 and hero_only.hasCostume[4] != 0:
        hero_only.isWearing = 4
    elif i == 14 and hero_only.hasCostume[5] != 0:
        hero_only.isWearing = 5
    elif i == 18:
        return TRUE
    return 0
