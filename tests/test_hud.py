import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from lynn.constants import SCREEN_H, SCREEN_W
from lynn.gfx.hud import blit_hud, hud_pip_frame, load_hud
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.paths import project_root


@pytest.fixture(scope="module")
def pygame_dummy():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((SCREEN_W, SCREEN_H))
    yield
    pygame.quit()


def test_hud_pip_frame_new_game_six_hearts():
    # hp=6, maxhp=6: p 0..5 full, p 6..29 locked (no empty pips).
    for p in range(6):
        assert hud_pip_frame(6, 6, p) == 0
    for p in range(6, 30):
        assert hud_pip_frame(6, 6, p) == 2


def test_hud_pip_frame_damaged():
    # hp=3, maxhp=6: 3 full, 3 empty, rest locked.
    assert [hud_pip_frame(3, 6, p) for p in range(8)] == [0, 0, 0, 1, 1, 1, 2, 2]


def test_ctor_hero_only_is_empty_new_game():
    only = ctor_hero_only()
    assert only.has_weapon == -1
    assert only.weapon == -1
    assert only.hasItem == [0, 0, 0, 0, 0, 0]
    assert only.selected_item == 0
    hero = ctor_hero(load_images=False)
    assert hero.hp == 6
    assert hero.maxhp == 6
    assert hero.money == 0


@pytest.mark.skipif(
    not (project_root() / "data/pictures/hud/HUD_health.spr").is_file(),
    reason="no hud sprites",
)
def test_blit_hud_new_game_layout(pygame_dummy):
    from lynn.gfx.palette import load_pal
    from lynn.paths import chdir_project_root

    chdir_project_root()
    hud = load_hud(load_pal("data/palette/ll.pal"))
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    canvas = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    canvas.fill((0, 0, 0))
    blit_hud(canvas, hero, only, hud)

    # First pip full (pink), first locked pip near-white, empty item slot, $000.
    assert canvas.get_at((8 + 4, 8 + 4))[:3] == (255, 157, 157)
    assert canvas.get_at((8 + 6 * 8 + 4, 8 + 4))[:3] == (252, 252, 252)
    assert canvas.get_at((132 + 8, 8 + 8))[:3] == (32, 32, 32)
    assert canvas.get_at((289 + 4, 8 + 8))[:3] == (252, 252, 252)


@pytest.mark.skipif(
    not (project_root() / "data/pictures/hud/cashnumbers.spr").is_file(),
    reason="no hud sprites",
)
def test_blit_hud_clamps_money_and_shows_digits(pygame_dummy):
    from lynn.gfx.palette import load_pal
    from lynn.paths import chdir_project_root

    chdir_project_root()
    hud = load_hud(load_pal("data/palette/ll.pal"))
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    hero.money = 1001
    canvas = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    canvas.fill((0, 0, 0))
    blit_hud(canvas, hero, only, hud)
    assert hero.money == 999
    # Hundreds digit '9' is not the same as '0' (white interior).
    assert canvas.get_at((289 + 4, 8 + 8))[:3] != (252, 252, 252)
