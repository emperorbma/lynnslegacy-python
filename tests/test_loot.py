import lynn.object  # noqa: F401

from lynn.hero import ctor_hero
from lynn.map.collision import check_bounds
from lynn.object.char import CharType
from lynn.object.combat_funcs import __drop
from lynn.gfx.loot import blit_enemy_loot


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
