import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from lynn.constants import SCREEN_H, SCREEN_W, TRUE
from lynn.gfx.menu import (
    handleKeybSelected,
    keyboardSelected,
    load_menu,
    menu_Blit,
)
from lynn.hero import ctor_hero_only


def test_keyboard_selected_from_resume_is_one_hop():
    from lynn.gfx.menu import MainMenu

    menu = MainMenu(selectedItem=18)
    keyboardSelected(menu, TRUE, 0, 0, 0)
    assert menu.selectedItem == 19
    menu.selectedItem = 18
    keyboardSelected(menu, 0, TRUE, 0, 0)
    assert menu.selectedItem == 3
    menu.selectedItem = 0
    keyboardSelected(menu, TRUE, TRUE, 0, 0)
    # Same Select Case: both apply to slot 0, right wins.
    assert menu.selectedItem == 1


def test_handle_title_sets_goto_title():
    from lynn.gfx.menu import MainMenu
    import lynn.events as events
    from lynn.events import reset_events

    reset_events()
    only = ctor_hero_only()
    menu = MainMenu(selectedItem=19)
    assert handleKeybSelected(menu, only) == TRUE
    assert events.goto_title == TRUE


def test_handle_resume_closes_and_empty_weapon_does_not_equip():
    from lynn.gfx.menu import MainMenu

    only = ctor_hero_only()
    menu = MainMenu(selectedItem=18)
    assert handleKeybSelected(menu, only) == TRUE
    menu.selectedItem = 0
    assert handleKeybSelected(menu, only) == 0
    assert only.weapon == -1
    only.has_weapon = 0
    assert handleKeybSelected(menu, only) == 0
    assert only.weapon == 0


def test_ctor_hero_only_owns_default_outfit():
    only = ctor_hero_only()
    assert only.hasCostume[0] != 0
    assert only.isWearing == 0
    assert all(c == 0 for c in only.hasCostume[1:])


def test_choosing_a_costume_swaps_lynn_sprites():
    from lynn.events import bind_hero, bind_hero_only, reset_events
    from lynn.gfx.menu import MainMenu
    from lynn.hero import ctor_hero
    from lynn.audio import sound_mace_0
    from lynn.paths import chdir_project_root

    chdir_project_root()
    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    only.hasCostume[1] = TRUE
    only.hasCostume[2] = TRUE
    bind_hero(hero)
    bind_hero_only(only)
    attack_name = hero.anim[3].filename
    menu = MainMenu(selectedItem=10)
    handleKeybSelected(menu, only)
    assert only.isWearing == 1
    assert "cougar/walk" in hero.anim[0].filename.replace("\\", "/")
    assert hero.animControl[0].rate == 0.05
    assert hero.anim[0].frames > 0
    assert hero.anim[3].filename == attack_name

    menu.selectedItem = 9
    handleKeybSelected(menu, only)
    assert only.isWearing == 0
    assert hero.anim[0].filename.replace("\\", "/").endswith("lynn24.spr")
    assert hero.animControl[0].rate == 0.08
    assert hero.anim[3].frame[0].sound == sound_mace_0
    assert hero.anim[3].frame[0].vol == 50

    menu.selectedItem = 11
    handleKeybSelected(menu, only)
    assert only.isWearing == 2
    assert "lynnity/walk" in hero.anim[0].filename.replace("\\", "/")
    assert "lynnity/attack_1" in hero.anim[3].filename.replace("\\", "/")
    assert hero.anim[3].frame[0].vol == 50

    import lynn.outfit as outfit
    from lynn.object.dispatch import lookup_func

    outfit._swap_state = 0
    assert lookup_func("__outfit_swap")(hero) == 1
    assert only.isWearing == 2
    assert hero.anim[0].filename.replace("\\", "/").endswith("lynn24.spr")
    assert lookup_func("__outfit_swap")(hero) == 1
    assert "lynnity/walk" in hero.anim[0].filename.replace("\\", "/")


def test_outfit_change_marks_the_drawn_frames_stale():
    from lynn.demos import _obj_anims_stale
    from lynn.gfx.image import LLSystem_ImageHeader
    from lynn.object.char import CharType

    hero = CharType()
    hero.anim = [LLSystem_ImageHeader(filename="data/pictures/char/lynn24.spr", frames=8)]
    hero._anim_token = ("data/pictures/char/lynn24.spr",)
    assert not _obj_anims_stale([[0] * 8], hero)
    hero.anim[0] = LLSystem_ImageHeader(
        filename="data/pictures/char/outfits/cougar/walk.spr",
        frames=8,
    )
    assert _obj_anims_stale([[0] * 8], hero)


def test_cougar_is_fast_and_the_red_knight_regenerates():
    from lynn import clock
    from lynn.audio import sound_healthgrab
    import lynn.audio as audio
    from lynn.object.char import CharType
    from lynn.outfit import tick_hero_outfit

    hero = CharType()
    hero.hp = 3
    hero.maxhp = 6
    only = ctor_hero_only()
    only.isWearing = 1
    tick_hero_outfit(hero, only)
    assert hero.walk_speed == 0.003
    assert only.healTimer == 0

    only.isWearing = 5
    clock.timer = 10
    only.healTimer = 1
    tick_hero_outfit(hero, only)
    assert hero.walk_speed == 0.02
    assert hero.hp == 4
    assert only.healTimer == 0
    assert audio.last_play[0] == sound_healthgrab

    only.isWearing = 0
    tick_hero_outfit(hero, only)
    assert hero.walk_speed == 0.009
    assert only.healTimer == 0


@pytest.fixture(scope="module")
def pygame_dummy():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((SCREEN_W, SCREEN_H))
    yield
    pygame.quit()


def test_menu_blit_new_game_has_outfit_and_resume(pygame_dummy):
    from lynn.gfx.palette import load_pal
    from lynn.paths import chdir_project_root

    chdir_project_root()
    menu = load_menu(load_pal("data/palette/ll.pal"))
    only = ctor_hero_only()
    menu.selectedItem = 18
    canvas = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    canvas.fill((0, 0, 0))
    menu_Blit(canvas, menu, only)
    # Background is not flat black; resume icon sits at (126, 54).
    assert canvas.get_at((160, 100))[:3] != (0, 0, 0)
    assert canvas.get_at((126 + 8, 54 + 8))[:3] != (0, 0, 0)


def test_font_glyphs_are_cropped(pygame_dummy):
    from lynn.gfx.palette import load_pal
    from lynn.paths import chdir_project_root

    chdir_project_root()
    menu = load_menu(load_pal("data/palette/ll.pal"))
    glyph = menu.font[ord("A")]
    assert glyph.get_width() == 8
    assert glyph.get_height() == 14
