import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from lynn.constants import SCREEN_H, SCREEN_W
from lynn.constants import DF_MAIN_CHAR, TRUE
from lynn.events import bind_hero, bind_hero_only, reset_events
from lynn.gfx.hud import blit_hud, hud_IsShowing, hud_pip_frame, load_hud
from lynn.hero import cache_crazy, ctor_hero, ctor_hero_only
from lynn.object.char import CharType
from lynn.object.combat import LLObject_ProcessHurt, start_hero_attack
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


def test_imageload_finds_fb_mixed_case_hud():
    from lynn.gfx.image import LLSystem_ImageLoad
    from lynn.paths import chdir_project_root

    chdir_project_root()
    # FB/Windows: HUD_health.spr. Data tree (and LOVE): hud_health.spr.
    health = LLSystem_ImageLoad("data/pictures/hud/HUD_health.spr")
    items = LLSystem_ImageLoad("data/pictures/hud/HUD_items.spr")
    assert health.frames == 3
    assert items.frames >= 1


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
    not (project_root() / "data/pictures/hud/hud_health.spr").is_file(),
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


def test_hud_shows_damaged_enemy_not_bushes():
    reset_events()
    bat = CharType()
    bat.hp = 1
    bat.maxhp = 1
    bat.dmg_id = DF_MAIN_CHAR
    assert hud_IsShowing(bat) != 0
    bush = CharType()
    bush.hp = 1
    bush.maxhp = 1
    bush.dmg_id = DF_MAIN_CHAR
    from lynn.constants import u_bush

    bush.unique_id = u_bush
    assert hud_IsShowing(bush) == 0
    boss = CharType()
    boss.isBoss = TRUE
    boss.hp = 15
    boss.maxhp = 15
    assert hud_IsShowing(boss) != 0


def test_hit_charges_crazy_and_psycho_attack():
    reset_events()
    only = ctor_hero_only()
    only.weapon = 0
    only.has_weapon = 0
    bind_hero_only(only)
    hero = ctor_hero(load_images=False)
    bind_hero(hero)
    enemy = CharType()
    enemy.hp = 2
    enemy.maxhp = 2
    enemy.hurt = 1
    enemy.dmg_id = DF_MAIN_CHAR
    enemy.funcs.func = [[lambda _h: 1]]
    enemy.funcs.func_count = [1]
    enemy.funcs.current_func = [0]
    enemy.funcs.states = 1
    LLObject_ProcessHurt(enemy)
    assert only.crazy_cache == 10
    from lynn import clock
    import lynn.hero as hero_mod

    hero_mod._cache_wait = 0
    clock.timer = 1.0
    for i in range(20):
        clock.timer = 1.0 + i * 0.02
        cache_crazy(only)
    assert only.crazy_points == 10
    only.crazy_points = 99
    start_hero_attack(hero)
    assert hero.psycho == TRUE
    assert hero.attack_state == 37
    assert only.crazy_points == 0


@pytest.mark.skipif(
    not (project_root() / "data/pictures/hud/fullbar.spr").is_file(),
    reason="no hud sprites",
)
def test_blit_hud_enemy_pips_and_crazy_bar(pygame_dummy):
    from lynn.gfx.palette import load_pal
    from lynn.paths import chdir_project_root

    chdir_project_root()
    reset_events()
    hud = load_hud(load_pal("data/palette/ll.pal"))
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    only.crazy_points = 40
    enemy = CharType()
    enemy.hp = 2
    enemy.maxhp = 2
    enemy.dmg_id = DF_MAIN_CHAR
    enemy.coords_x = 160
    enemy.coords_y = 100
    enemy.perimeter_x = 16
    enemy.perimeter_y = 16
    canvas = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    canvas.fill((0, 0, 0))
    blit_hud(canvas, hero, only, hud, enemies=[enemy], cam_x=0, cam_y=0)
    # Enemy pip at (146+8, 8) full heart pink.
    assert canvas.get_at((146 + 8 + 4, 8 + 4))[:3] == (255, 157, 157)
    # Crazy bar fill starts at (15, 27).
    assert canvas.get_at((20, 28))[:3] != (0, 0, 0)
