import lynn.object  # noqa: F401

from lynn.constants import TRUE, u_gold
from lynn.events import bind_hero, reset_events
from lynn.gfx.image import LLSystem_FaceType, LLSystem_FrameShell, LLSystem_ImageHeader
from lynn.hero import ctor_hero
from lynn.map.collision import check_bounds
from lynn.object.char import CharType
from lynn.object.combat_funcs import __drop
from lynn.demos import _sort_y
from lynn.gfx.loot import (
    LLObject_GrabItems,
    blit_enemy_loot,
    drop_sort_y,
    is_corpse_drop,
)


def test_drop_always_health_when_d_health_100():
    o = CharType()
    o.coords_x = 100
    o.coords_y = 80
    o.perimeter_x = 16
    o.perimeter_y = 16
    o.d_health = 100
    assert __drop(o) == 1
    assert o.dropped == 1
    assert 100 <= o.drop_x < 108
    assert 80 <= o.drop_y < 88


def test_drop_none_when_rates_zero():
    o = CharType()
    o.perimeter_x = 16
    o.perimeter_y = 8
    o.d_health = 0
    o.d_gold = 0
    o.d_silver = 0
    __drop(o)
    assert o.dropped == 0


def test_pickup_health_and_silver():
    hero = ctor_hero(load_images=False)
    hero.hp = 5
    hero.maxhp = 6
    hero.coords_x = 10
    hero.coords_y = 10
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    heart = CharType()
    heart.dropped = 1
    heart.drop_x = 12
    heart.drop_y = 12
    blit_enemy_loot(None, [heart], hero, 0, 0, [object(), object(), object()])
    assert hero.hp == 6
    assert heart.dropped == 0

    hero.money = 0
    coin = CharType()
    coin.dropped = 3
    coin.n_silver = 1
    coin.drop_x = 12
    coin.drop_y = 12
    blit_enemy_loot(None, [coin], hero, 0, 0, [object(), object(), object()])
    assert hero.money == 1
    assert coin.dropped == 0


def test_loot_hitbox_is_8x8():
    origin = (0, 0, 16, 16)
    assert check_bounds(origin, (10, 10, 8, 8)) == 0
    assert check_bounds(origin, (40, 40, 8, 8)) == -1


def test_drop_y_sorts_with_hero():
    hero = ctor_hero(load_images=False)
    hero.coords_y = 100
    hero.perimeter_y = 16
    north = CharType()
    north.dropped = 1
    north.drop_y = 90
    south = CharType()
    south.dropped = 3
    south.drop_y = 120
    assert drop_sort_y(north) < _sort_y(hero) < drop_sort_y(south)


def _hero_with_reach_face():
    hero = ctor_hero(load_images=False)
    hero.coords_x = 0
    hero.coords_y = 0
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.current_anim = 0
    face = LLSystem_FaceType(x=16, y=0, w=16, h=16)
    frame = LLSystem_FrameShell(faces=1, face=[face])
    header = LLSystem_ImageHeader(frame=[frame], frames=1)
    hero.anim = [header]
    hero.animControl = []
    return hero


def test_swing_face_picks_up_corpse_drop():
    hero = _hero_with_reach_face()
    hero.hp = 5
    hero.maxhp = 6
    heart = CharType()
    heart.dropped = 1
    heart.drop_x = 20
    heart.drop_y = 4
    blit_enemy_loot(None, [heart], hero, 0, 0, [object(), object(), object()])
    assert heart.dropped == 0
    assert hero.hp == 6


def test_unique_gold_pile_is_grabbed():
    reset_events()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 160
    hero.coords_y = 140
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.money = 0
    bind_hero(hero)
    pile = CharType()
    pile.unique_id = u_gold
    pile.dropped = 2
    pile.n_gold = 1
    pile.coords_x = 164
    pile.coords_y = 144
    pile.dead = 0
    LLObject_GrabItems(pile)
    assert pile.dropped == 0
    assert hero.money == 5
    assert pile.dead != 0


def test_unique_gold_is_not_a_corpse_overlay():
    o = CharType()
    o.dropped = 2
    o.unique_id = u_gold
    assert is_corpse_drop(o) is False
    o.unique_id = 0
    assert is_corpse_drop(o) is True
