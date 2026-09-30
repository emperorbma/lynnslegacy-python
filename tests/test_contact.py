import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

import lynn.object  # noqa: F401
from lynn import clock
from lynn.constants import DF_ROOM_ENEMY
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.object.combat import LLObject_MAINDamage, LLObject_ProcessHurt, hero_death_tick, hero_hurt_tick
from lynn.object.dispatch import lookup_func
from lynn.object.combat_funcs import __flashy
from lynn.object.xml_load import spawn_from_stub


def _overlap_roamer(hero):
    from types import SimpleNamespace

    stub = SimpleNamespace(
        id="data/object/roamer.xml",
        x_origin=hero.coords_x,
        y_origin=hero.coords_y,
        direction=0,
    )
    return spawn_from_stub(stub, load_images=True)


def test_roamer_contact_hurts_lynn():
    pygame.init()
    pygame.display.set_mode((320, 200))
    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    bind_hero_only(only)
    bind_hero(hero)
    roamer = _overlap_roamer(hero)
    bind_room(None, [roamer])
    hp0 = hero.hp
    LLObject_MAINDamage(hero, [roamer])
    assert hero.hp == hp0 - 1
    assert hero.dmg_id == DF_ROOM_ENEMY
    assert hero.hurt == 1
    pygame.quit()


def test_contact_iframes_block_second_hit():
    pygame.init()
    pygame.display.set_mode((320, 200))
    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    bind_hero_only(only)
    bind_hero(hero)
    roamer = _overlap_roamer(hero)
    bind_room(None, [roamer])
    LLObject_MAINDamage(hero, [roamer])
    hp = hero.hp
    LLObject_MAINDamage(hero, [roamer])
    assert hero.hp == hp
    pygame.quit()


def test_flashy_clears_dmg_id():
    pygame.init()
    pygame.display.set_mode((320, 200))
    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    bind_hero_only(only)
    bind_hero(hero)
    roamer = _overlap_roamer(hero)
    bind_room(None, [roamer])
    clock.timer = 0.0
    LLObject_MAINDamage(hero, [roamer])
    assert hero.dmg_id != 0
    for i in range(80):
        clock.timer = i * 0.02
        __flashy(hero)
        if hero.dmg_id == 0:
            break
    assert hero.dmg_id == 0
    assert hero.invisible == 0
    pygame.quit()


def test_hurt_flyback_moves_hero():
    pygame.init()
    pygame.display.set_mode((320, 200))
    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    bind_hero_only(only)
    bind_hero(hero)
    roamer = _overlap_roamer(hero)
    roamer.coords_x = hero.coords_x - 8
    from lynn.map.loader import load_mapV
    from lynn.paths import resolve_map_path

    room = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False).room[1]
    hero.coords_x, hero.coords_y = 160, 280
    roamer.coords_x, roamer.coords_y = 152, 280
    bind_room(room, [roamer])
    clock.timer = 0.0
    x0 = hero.coords_x
    LLObject_MAINDamage(hero, [roamer])
    assert hero.hurt != 0
    for i in range(40):
        clock.timer = i * 0.004
        hero_hurt_tick(hero)
        if hero.hurt == 0:
            break
    assert hero.coords_x != x0 or hero.fly_count == 0
    pygame.quit()


def test_lynn_death_falls_then_returns_to_title():
    """FB death_state: face down, lynnfall, red wash, black, jump_to_title.

    The hero tick forces fade_time .003. Without images the fall anim
    completes in one call; the fades still take their timed steps.
    """
    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    death = hero.funcs.func[hero.death_state]
    assert death[0] is lookup_func("__dir_down")
    assert death[1] is lookup_func("__active_anim_8")
    assert death[2] is lookup_func("__active_animate_x")
    assert death[3] is lookup_func("__fade_to_red")
    assert death[4] is lookup_func("__fade_to_black")
    hero.hp = 1
    hero.hurt = 1
    LLObject_ProcessHurt(hero)
    assert hero.dead == 1
    assert hero.fade_time == 0.07
    clock.timer = 0.0
    saw_fall = False
    # Frame holds use the fall rate (~0.18s). A cached lynnfall.spr still
    # has to play out; 0.2s per call clears that and the 0.003 fade steps.
    for _ in range(500):
        clock.timer += 0.2
        hero_death_tick(hero)
        if hero.current_anim == 8:
            saw_fall = True
        if events.goto_title != 0:
            break
    assert saw_fall
    assert hero.direction == 2
    assert hero.fade_time == 0.003
    assert events.fade_red == 255
    assert events.fade_black >= 250
    assert events.goto_title != 0
    reset_events()
