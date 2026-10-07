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
    start_item_use,
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
    # hit_state is do_flyback + flicker (flash_length 30); 0.05 steps take two ticks per flash.
    for i in range(400):
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


def test_desert_goblin_chase_does_not_stick_invulnerable():
    """A melee hit yanks the spear goblins into the chase with dmg_id still set."""
    from types import SimpleNamespace

    from lynn import clock
    from lynn.constants import DF_MAIN_CHAR
    from lynn.events import bind_hero, bind_hero_only
    from lynn.hero import ctor_hero, ctor_hero_only
    from lynn.object.combat import LLObject_DamageCalc
    from lynn.object.tick import tick_objects

    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    only.weapon = 0
    bind_hero(hero)
    bind_hero_only(only)
    hero.coords_x = 40
    hero.coords_y = 40
    saved = clock.timer
    try:
        for xml, hp0 in (("gbandit.xml", 4), ("blackg.xml", 8), ("roamer.xml", 2)):
            clock.timer = 0.0
            enemy = spawn_from_stub(
                SimpleNamespace(
                    id=f"data/object/{xml}",
                    x_origin=48,
                    y_origin=40,
                    direction=0,
                ),
                load_images=False,
            )
            assert enemy.hp == hp0
            enemy.dmg_id = DF_MAIN_CHAR
            enemy.dmg_specific = 0
            LLObject_DamageCalc(enemy)
            assert enemy.hp == hp0 - 1
            assert enemy.dmg_id != 0
            tick_objects([enemy])
            if enemy.froggy != 0:
                assert enemy.funcs.active_state == enemy.jump_state
                assert enemy.mad != 0
                assert enemy.dmg_id != 0
            cleared = False
            for _ in range(80):
                clock.timer += enemy.flash_time or 0.02
                tick_objects([enemy])
                if enemy.dmg_id == 0:
                    cleared = True
                    break
            assert cleared
            assert enemy.hp == hp0 - 1
            enemy.dmg_id = DF_MAIN_CHAR
            enemy.dmg_specific = 0
            LLObject_DamageCalc(enemy)
            assert enemy.hp == hp0 - 2
    finally:
        clock.timer = saved


def test_powder_swing_drops_a_walk_hold():
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    only.selected_item = 1
    bind_hero_only(only)
    hero.frame_hold = 9.0
    start_item_use(hero)
    assert only.attacking == TRUE
    assert hero.attack_state == 8
    assert hero.frame_hold == 0


def test_mace_swing_sounds_on_the_step_that_shows_frame_zero():
    """Frame 0 is the only mace sample, and it lasts a single logic step."""
    pygame.init()
    pygame.display.set_mode((320, 200))
    from lynn import audio, clock
    from lynn.audio import sound_mace_2
    from lynn.gfx.blit import _play_frame_sound
    from lynn.macros import LLObject_CalculateFrame

    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    only.has_weapon = 2
    only.weapon = 2
    bind_hero_only(only)
    saved = clock.timer
    try:
        clock.timer = 1.0
        hero.direction = 1
        hero.frame_hold = clock.timer + 0.08
        audio.last_play = None
        start_hero_attack(hero)
        hero_attack(hero)
        assert hero.current_anim == 5
        assert hero.frame == 0
        assert hero.frame_hold == 0
        _play_frame_sound(hero)
        assert audio.last_play == (sound_mace_2, 50)
        for _ in range(3):
            clock.timer += clock.LOGIC_DT
            hero_attack(hero)
            _play_frame_sound(hero)
        shown = LLObject_CalculateFrame(hero)
        assert hero.frame != 0
        assert hero.anim[hero.current_anim].frame[shown].sound == 0
        assert audio.last_play == (sound_mace_2, 50)
    finally:
        clock.timer = saved
        pygame.quit()


def _mace_connect_step(frame_hold: float) -> int | None:
    from types import SimpleNamespace

    from lynn import clock

    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    only.has_weapon = 2
    only.weapon = 2
    bind_hero_only(only)
    hero.coords_x = 100
    hero.coords_y = 100
    hero.direction = 1
    hero.frame_hold = frame_hold
    roamer = spawn_from_stub(
        SimpleNamespace(
            id="data/object/roamer.xml",
            x_origin=hero.coords_x + 16,
            y_origin=hero.coords_y,
            direction=0,
        ),
        load_images=True,
    )
    hp0 = roamer.hp
    clock.timer = 1.0
    start_hero_attack(hero)
    for i in range(80):
        clock.timer += clock.LOGIC_DT
        if only.attacking != 0:
            hero_attack(hero)
        LLObject_MAINAttack([roamer], hero)
        if roamer.hp < hp0 or roamer.dead != 0:
            return i
    return None


def test_mace_hit_ignores_a_leftover_walk_hold():
    pygame.init()
    pygame.display.set_mode((320, 200))
    from lynn import clock

    saved = clock.timer
    try:
        held = _mace_connect_step(1.08)
        clear = _mace_connect_step(0.0)
        assert held is not None
        assert held == clear
        # A live walk hold used to push this hit out by about 0.08s (past step 40).
        assert held < 40
    finally:
        clock.timer = saved
        pygame.quit()
