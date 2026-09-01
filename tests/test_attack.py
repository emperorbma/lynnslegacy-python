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
