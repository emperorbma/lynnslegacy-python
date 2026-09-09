import subprocess
import sys

import lynn.object  # noqa: F401

from lynn import clock
from lynn.constants import (
    DF_MAIN_CHAR,
    PROJECTILE_FIREBALL,
    TRUE,
    u_coldrock,
    u_gbutton,
    u_grult,
    u_gtorch,
    u_pushrock,
)
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.hero import ctor_hero_only, item_l_key, item_r_key
from lynn.object.char import CharType
from lynn.object.combat import LLObject_DeriveHurt, start_item_use
from lynn.object.dispatch import lookup_func
from lynn.object.tick import tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import project_root

OBJ = project_root() / "data" / "object"


def _load(name: str) -> CharType:
    obj = CharType()
    obj.id = f"data/object/{name}"
    return LLSystem_ObjectFromXML(obj, load_images=False)


def test_fresh_import_does_not_cycle_through_collision():
    """collision -> object.char used to re-enter boss.py while collision was loading."""
    code = (
        "from lynn.map.collision import check_bounds; "
        "import lynn.object; "
        "from lynn.hero import ctor_hero; "
        "from lynn.object.dispatch import lookup_func; "
        "assert lookup_func('__do_circle') is not lookup_func('__noop')"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(project_root()),
    )
    assert r.returncode == 0, r.stderr


def test_coldrock_and_powder_chest_load():
    rock = _load("coldrock.xml")
    assert rock.unique_id == u_coldrock
    assert rock.invincible != 0
    assert rock.fire_weak != 0
    assert rock.impassable != 0
    chest = _load("bluechestitem.xml")
    assert lookup_func("__give_item") is not lookup_func("__noop")
    assert chest.funcs.func[3][1] is lookup_func("__give_item")


def test_give_item_sets_hasItem():
    reset_events()
    only = ctor_hero_only()
    bind_hero_only(only)
    chest = _load("bluechestitem.xml")
    chest.chap = 0
    assert lookup_func("__give_item")(chest) == 1
    assert only.hasItem[0] == TRUE


def test_flare_powder_destroys_coldrock():
    reset_events()
    only = ctor_hero_only()
    only.hasItem[0] = TRUE
    only.selected_item = 1
    only.powder = 1
    bind_hero_only(only)
    rock = _load("coldrock.xml")
    rock.dmg_id = DF_MAIN_CHAR
    LLObject_DeriveHurt(rock)
    assert rock.hp == 0
    tick_objects([rock])
    assert rock.funcs.active_state == rock.death_state


def test_start_item_use_sets_flare_state():
    reset_events()
    from lynn.hero import ctor_hero

    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    only.hasItem[0] = TRUE
    only.selected_item = 1
    bind_hero_only(only)
    start_item_use(hero)
    assert only.attacking == TRUE
    assert hero.attack_state == 8
    assert only.powder == 1


def test_item_cycle_skips_empty_slots():
    only = ctor_hero_only()
    only.hasItem[0] = TRUE
    only.hasItem[2] = TRUE
    only.selected_item = 1
    item_r_key(only)
    assert only.selected_item == 3
    item_l_key(only)
    assert only.selected_item == 1


def test_grult_loads_as_boss():
    boss = _load("grult.xml")
    assert boss.unique_id == u_grult
    assert boss.isBoss != 0
    assert boss.hp == 15
    assert boss.proj_style == PROJECTILE_FIREBALL
    assert boss.radius == 60
    assert lookup_func("__do_circle") is not lookup_func("__noop")
    assert lookup_func("__grult_fireball") is not lookup_func("__noop")
    assert boss.funcs.func[0][0] is lookup_func("__do_circle")
    torch = _load("gtorch.xml")
    assert torch.unique_id == u_gtorch
    assert lookup_func("__big_color_up") is not lookup_func("__noop")
    assert lookup_func("__return_jump") is not lookup_func("__noop")


def test_do_circle_orbits_origin():
    boss = _load("grult.xml")
    boss.x_origin = 100
    boss.y_origin = 100
    boss.coords_x = 100
    boss.coords_y = 100
    boss.degree = 0
    clock.timer = 1.0
    lookup_func("__do_circle")(boss)
    assert boss.coords_x == 100
    assert boss.coords_y == 40


def test_grult_stuns_when_dark_not_4():
    reset_events()
    events.dark = 1
    boss = _load("grult.xml")
    boss.funcs.active_state = 0
    tick_objects([boss])
    assert boss.funcs.active_state == boss.stun_state


def test_gtorch_sets_room_dark():
    reset_events()
    events.dark = 4
    torch = _load("gtorch.xml")
    lookup_func("__big_color_up")(torch)
    assert events.dark == 1
    lookup_func("__big_color_down")(torch)
    assert events.dark == 4


def test_grult_fireball_spawns_at_mouth():
    reset_events()
    hero = CharType()
    hero.coords_x = 200
    hero.coords_y = 200
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero(hero)
    boss = _load("grult.xml")
    boss.coords_x = 100
    boss.coords_y = 100
    lookup_func("__grult_fireball")(boss)
    assert boss.grult_proj_trig != 0
    assert boss.projectile is not None
    assert boss.projectile.coords[0] == [152, 136]
    clock.timer = 1.0
    lookup_func("__do_grult_proj")(boss)
    assert boss.projectile.coords[0] != [152, 136]


def _open_room(w: int = 20, h: int = 20):
    from lynn.map.types import RoomType

    room = RoomType()
    room.x = w
    room.y = h
    room.layout = [[0] * (w * h) for _ in range(3)]
    return room


def test_pushrock_loads_pushable():
    rock = _load("pushrock.xml")
    assert rock.unique_id == u_pushrock
    assert rock.pushable != 0
    assert rock.impassable != 0
    assert lookup_func("__off_happen") is not lookup_func("__noop")


def test_push_rock_slides_when_lynn_faces_it():
    from lynn.object.move_ai import __push

    reset_events()
    room = _open_room()
    hero = CharType()
    hero.coords_x = 160
    hero.coords_y = 160
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.direction = 1
    rock = _load("pushrock.xml")
    rock.coords_x = 176
    rock.coords_y = 160
    rock.num = 0
    bind_hero(hero)
    bind_room(room, [rock])
    events.keys.right = TRUE
    clock.timer = 1.0
    __push(rock)
    assert rock.coords_x == 177
    assert hero.is_pushing == 2


def test_gbutton_presses_when_rock_overlaps():
    reset_events()
    room = _open_room()
    rock = _load("pushrock.xml")
    rock.coords_x = 80
    rock.coords_y = 80
    button = _load("gbutton.xml")
    button.coords_x = 80
    button.coords_y = 80
    button.chap = 10
    button.num = 1
    objs = [rock, button]
    bind_room(room, objs)
    tick_objects(objs)
    tick_objects(objs)
    assert button.unique_id == u_gbutton
    assert button.funcs.active_state == 1
    assert events.now[10] != 0
