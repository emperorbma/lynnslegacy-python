"""Desert thief turns in the Nerme idol when Lynn already holds it."""

import lynn.object  # noqa: F401

import lynn.clock as clock

from lynn.constants import TRUE
from lynn.events import bind_hero, bind_hero_only, bind_room, now, reset_events
from lynn.gfx.menu import (
    MainMenu,
    idol_menu_icons,
    idol_menu_name,
    menu_blank,
    menu_blank_select,
    menu_idol,
    menu_idol_select,
)
from lynn.hero import DIR_UP, ctor_hero, ctor_hero_only
from lynn.map.collision import check_against
from lynn.map.loader import load_mapV
from lynn.object.dispatch import lookup_func
from lynn.object.move_ai import __home
from lynn.object.tick import tick_object
from lynn.object.xml_load import LLSystem_ObjectFromXML, spawn_from_stub
from lynn.object.char import CharType
from lynn.paths import resolve_map_path
from lynn.sequence import try_action_sequence


def _desert_bandit():
    reset_events()
    room = load_mapV(str(resolve_map_path("desert")), load_tileset=False).room[0]
    objs = [spawn_from_stub(stub, load_images=False) for stub in room.enemy]
    bandit = next(o for o in objs if str(o.id).replace("\\", "/").endswith("bandit.xml"))
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.direction = DIR_UP
    hero.coords_x = bandit.coords_x
    hero.coords_y = bandit.coords_y + 15
    bind_hero(hero)
    bind_hero_only(only)
    for i, obj in enumerate(objs):
        obj.num = i + 1
    return hero, only, objs, bandit, room


def test_bandit_check_is_the_idle_func():
    obj = CharType()
    obj.id = "data/object/bandit.xml"
    LLSystem_ObjectFromXML(obj, load_images=False)
    assert lookup_func("__bandit_check") is not lookup_func("__noop")
    assert obj.funcs.func[0][0].__name__ == "__bandit_check"


def test_bandit_check_arms_the_turn_in_only_with_the_idol():
    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    thief = CharType()
    from lynn.object.seq_funcs import __bandit_check

    assert __bandit_check(thief) == 0
    assert thief.sel_seq == 0
    only.hasItem[3] = TRUE
    assert __bandit_check(thief) == 0
    assert thief.sel_seq == 1


def test_talking_without_the_idol_is_the_refusal():
    hero, only, objs, bandit, _room = _desert_bandit()
    tick_object(bandit)
    assert bandit.sel_seq == 0
    only.action = TRUE
    seq = try_action_sequence(hero, only, objs)
    assert seq is bandit.seq[0]
    assert "something unique" in seq.Command[3].ent[0].text


def test_talking_with_the_idol_starts_the_turn_in():
    hero, only, objs, bandit, _room = _desert_bandit()
    only.hasItem[3] = TRUE
    tick_object(bandit)
    assert bandit.sel_seq == 1
    only.action = TRUE
    seq = try_action_sequence(hero, only, objs)
    assert seq is bandit.seq[1]
    assert "What's that you've got there?" in seq.Command[0].ent[0].text
    assert seq.Command[13].ent[0].chap == 1212


def test_thief_walks_onto_the_idol_he_is_taking():
    """Seq 1 command 9 homes him onto the idol. That prop does not block."""
    hero, _only, objs, bandit, room = _desert_bandit()
    idol = next(o for o in objs if str(o.id).replace("\\", "/").endswith("idol.xml"))
    idol.coords_x = 3920
    idol.coords_y = 1600
    hero.coords_x = 3896
    hero.coords_y = 1600
    bind_room(room, objs)
    bandit.coords_x = 3936
    bandit.direction = 3
    assert check_against(bandit, idol, 3) == 0
    bandit.coords_x = 3952
    bandit.coords_y = 1600
    bandit.dest_x = 3920
    bandit.dest_y = 1600
    bandit.walk_hold = 0
    arrived = 0
    for _ in range(80):
        clock.timer += 0.05
        if __home(bandit) == 1:
            arrived = 1
            break
    assert arrived == 1
    assert (int(bandit.coords_x), int(bandit.coords_y)) == (3920, 1600)


def test_idol_menu_blanks_after_the_thief_takes_it():
    reset_events()
    menu = MainMenu()
    menu.menuNames = [""] * (menu_idol_select + 1)
    menu.menuNames[menu_idol_select] = "An ancient treasure."
    only = ctor_hero_only()
    only.hasItem[3] = TRUE
    assert idol_menu_icons() == (menu_idol, menu_idol_select)
    assert idol_menu_name(menu, only) == "An ancient treasure."
    now[1212] = TRUE
    assert idol_menu_icons() == (menu_blank, menu_blank_select)
    assert idol_menu_name(menu, only) == "Gave it away..."
    only.hasItem[3] = 0
    assert idol_menu_name(menu, only) == ""
