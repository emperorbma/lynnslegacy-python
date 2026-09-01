import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

import lynn.object  # noqa: F401

from lynn.constants import TRUE
from lynn.events import bind_hero_only
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.object.combat import (
    LLObject_MAINAttack,
    hero_attack,
    start_hero_attack,
)
from lynn.object.xml_load import spawn_from_stub


def test_no_attack_without_weapon():
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero_only(only)
    start_hero_attack(hero)
    assert only.attacking == 0


def test_start_attack_with_sapling():
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    only.has_weapon = 0
    only.weapon = 0
    bind_hero_only(only)
    start_hero_attack(hero)
    assert only.attacking == TRUE
    hero_attack(hero)
    assert hero.current_anim == 3


def test_sapling_hit_hurts_roamer():
    pygame.init()
    pygame.display.set_mode((320, 200))
    from types import SimpleNamespace

    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    only.has_weapon = 0
    only.weapon = 0
    bind_hero_only(only)
    stub = SimpleNamespace(
        id="data/object/roamer.xml",
        x_origin=hero.coords_x + 16,
        y_origin=hero.coords_y,
        direction=0,
    )
    roamer = spawn_from_stub(stub, load_images=True)
    hp0 = roamer.hp
    assert hp0 == 2
    hero.direction = 1
    start_hero_attack(hero)
    from lynn import clock

    # Advance wall-clock so directional_animate can step through swing frames.
    for i in range(40):
        clock.timer = i * 0.07
        if only.attacking != 0:
            hero_attack(hero)
        LLObject_MAINAttack([roamer], hero)
        if roamer.hp < hp0 or roamer.dead != 0:
            break
    assert roamer.hp < hp0 or roamer.dead != 0
    pygame.quit()


def _swing_until_hurt(hero, only, roamer):
    from lynn import clock

    hp0 = roamer.hp
    start_hero_attack(hero)
    for i in range(40):
        clock.timer = clock.timer + 0.07
        if only.attacking != 0:
            hero_attack(hero)
        LLObject_MAINAttack([roamer], hero)
        if roamer.hp < hp0 or roamer.dead != 0:
            return True
    return False


def test_roamer_dies_and_is_gone():
    pygame.init()
    pygame.display.set_mode((320, 200))
    from types import SimpleNamespace

    from lynn import clock
    from lynn.object.tick import tick_objects

    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    only.has_weapon = 0
    only.weapon = 0
    bind_hero_only(only)
    stub = SimpleNamespace(
        id="data/object/roamer.xml",
        x_origin=hero.coords_x + 16,
        y_origin=hero.coords_y,
        direction=0,
    )
    roamer = spawn_from_stub(stub, load_images=True)
    hero.direction = 1
    clock.timer = 0.0
    assert _swing_until_hurt(hero, only, roamer)
    # Finish hit reaction so a second swing can connect.
    for i in range(80):
        clock.timer += 0.05
        tick_objects([roamer])
        if roamer.hurt == 0 and roamer.dead == 0:
            break
    if roamer.dead == 0:
        roamer.coords_x = hero.coords_x + 16
        roamer.coords_y = hero.coords_y
        only.attacking = 0
        assert _swing_until_hurt(hero, only, roamer)
    for i in range(200):
        clock.timer += 0.05
        tick_objects([roamer])
        if roamer.total_dead != 0:
            break
    assert roamer.dead != 0
    assert roamer.total_dead != 0
    assert roamer.invisible != 0
    pygame.quit()
