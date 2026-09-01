import lynn.object  # noqa: F401
from lynn import clock
from lynn.constants import TRUE, u_healthguy
from lynn.events import bind_hero, bind_hero_only, reset_events
from lynn.gfx.box import BoxControl, parse_text, tick_box, make_box, TEXTBOX_CONFIRMATION
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.object.dispatch import lookup_func
from lynn.object.seq_funcs import __buy_health, __healthguy_branch, health_formula
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.object.char import CharType


def test_healthguy_unique_id_and_talk_funcs():
    obj = CharType()
    obj.id = "data/object/healthguy.xml"
    LLSystem_ObjectFromXML(obj, load_images=False)
    assert obj.unique_id == u_healthguy
    assert lookup_func("__do_nothing") is not lookup_func("__noop")
    assert lookup_func("__return_jump_npc") is not lookup_func("__noop")
    assert lookup_func("__return_reset_npc") is not lookup_func("__noop")
    assert lookup_func("__buy_health") is not lookup_func("__noop")
    assert lookup_func("__translate_result") is not lookup_func("__noop")
    assert lookup_func("__do_nothing")(obj) == 1


def test_health_formula_and_tokens():
    reset_events()
    hero = ctor_hero(load_images=False)
    bind_hero(hero)
    assert health_formula(6) == 50
    assert health_formula(7) == 55
    assert parse_text("hp {HEALTHNOW} to {HEALTHUP} for {HEALTHPRICE}") == "hp 6 to 7 for 50"


def test_healthguy_branch_poor_and_maxed():
    reset_events()
    hero = ctor_hero(load_images=False)
    bind_hero(hero)
    guy = CharType()
    guy.sel_seq = 0
    hero.money = 0
    __healthguy_branch(guy)
    assert guy.sel_seq == 2
    guy.sel_seq = 0
    hero.money = 200
    hero.maxhp = 30
    __healthguy_branch(guy)
    assert guy.sel_seq == 1


def test_buy_health_increases_maxhp():
    reset_events()
    hero = ctor_hero(load_images=False)
    hero.money = 50
    hero.maxhp = 6
    hero.hp = 6
    bind_hero(hero)
    assert __buy_health(CharType()) == 1
    assert hero.maxhp == 7
    assert hero.money == 0


def test_conf_box_enter_closes():
    import lynn.events as events

    reset_events()
    box = BoxControl()
    clock.timer = 0.0
    make_box(box, "Upgrade?", conf=TRUE)
    assert box.confBox != 0
    tick_box(box, TRUE)
    assert box.state == TEXTBOX_CONFIRMATION
    events.keys.right = TRUE
    tick_box(box, 0)
    assert box.selected == 1
    events.keys.right = 0
    events.keys.enter_pulse = TRUE
    tick_box(box, 0)
    assert box.activated == 0
