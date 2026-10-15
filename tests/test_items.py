"""Adrenaline Booster (item 5) and Healing Symbol (item 6)."""

from __future__ import annotations

import lynn.events as events
import lynn.items as items
import lynn.object  # noqa: F401
from lynn import clock
from lynn.events import bind_hero, bind_hero_only, reset_events
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.object.char import CharType
from lynn.object.combat import LLObject_DeriveHurt, start_item_use


def _setup(item: int):
    reset_events()
    items._adrenaline_state = 0
    items._healing_timer = 0.0
    clock.timer = 100.0
    hero, only = ctor_hero(), ctor_hero_only()
    hero.hp, hero.maxhp, hero.money = 10, 12, 50
    only.hasItem[item - 1] = 1
    only.selected_item = item
    bind_hero(hero)
    bind_hero_only(only)
    return hero, only


def test_booster_costs_three_hp_and_lasts_six_seconds():
    hero, only = _setup(5)
    start_item_use(hero)
    assert hero.hp == 7
    assert only.adrenaline == 106.0
    assert only.attacking == 0
    only.crazy_points = 50
    clock.timer = 105.0
    items.tick_item_effects(hero, only)
    assert only.adrenaline is not None
    clock.timer = 106.5
    items.tick_item_effects(hero, only)
    assert only.adrenaline is None
    assert only.crazy_points == 0


def test_booster_refuses_when_active_or_hp_too_low():
    hero, only = _setup(5)
    start_item_use(hero)
    start_item_use(hero)
    assert hero.hp == 7
    hero2, only2 = _setup(5)
    hero2.hp = 3
    start_item_use(hero2)
    assert hero2.hp == 3 and only2.adrenaline is None


def _hit(weapon: int) -> int:
    only = events.hero_only
    only.weapon = weapon
    foe = CharType()
    foe.dmg_id = 4
    LLObject_DeriveHurt(foe)
    return foe.hurt


def test_booster_adds_damage_by_weapon():
    hero, only = _setup(5)
    base = [_hit(w) for w in (0, 1, 2)]
    assert base == [1, 2, 4]
    only.adrenaline = clock.timer + 6
    assert [_hit(w) for w in (0, 1, 2)] == [2, 3, 6]


def test_healing_trades_two_gold_for_one_hp_and_sparkles():
    hero, only = _setup(6)
    start_item_use(hero)
    assert (hero.hp, hero.money) == (11, 48)
    assert only.healing != 0 and only.attacking == 0
    start_item_use(hero)
    assert hero.hp == 11
    frames = 0
    for _ in range(400):
        clock.timer += 0.02
        items.tick_item_effects(hero, only)
        frames = max(frames, only.healingFrame)
        if only.healing == 0:
            break
    assert only.healing == 0
    assert frames == items.HEAL_FRAMES - 1
    start_item_use(hero)
    assert hero.hp == 12


def test_healing_refuses_when_full_or_broke():
    hero, only = _setup(6)
    hero.hp = hero.maxhp
    start_item_use(hero)
    assert hero.money == 50 and only.healing == 0
    hero.hp = 5
    hero.money = 1
    start_item_use(hero)
    assert hero.hp == 5 and only.healing == 0


def test_heal_sprite_has_the_frames_the_tick_expects():
    from lynn.gfx.image import LLSystem_ImageLoad

    assert LLSystem_ImageLoad("data/pictures/char/heal.spr").frames >= items.HEAL_FRAMES
