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
