"""Forest room 14: the moth scene past the fire rocks."""

import math

import lynn.object  # noqa: F401

from lynn import clock
from lynn.constants import TRUE
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.gfx.box import BoxControl, TEXTBOX_CONFIRMATION
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import resolve_map_path
from lynn.sequence import play_sequence, try_touch_sequence


def test_push_lynn_back_is_real_and_points_away():
    assert lookup_func("__push_lynn_back") is not lookup_func("__noop")
    reset_events()
    hero = CharType()
    hero.coords_x = 360
    hero.coords_y = 144
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero(hero)
    moth = CharType()
    moth.coords_x = 320
    moth.coords_y = 0
    moth.perimeter_x = 16
    moth.perimeter_y = 16
    assert lookup_func("__push_lynn_back")(moth) == 1
    assert abs(math.hypot(hero.fly_x, hero.fly_y) - 3) < 1e-6
    assert hero.fly_x > 0
    assert hero.fly_y > 0


def test_moth_scene_behind_the_fire_rocks_finishes():
    """Room 14 touch scene used to stall on moth state 6 (__push_lynn_back)."""
    reset_events()
    game_map = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    room = game_map.room[14]
    objs = []
    for stub in room.enemy:
        obj = spawn_from_stub(stub, load_images=False)
        obj.num = len(objs)
        objs.append(obj)
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    box = BoxControl()
    bind_hero(hero)
    bind_hero_only(only)
    bind_room(room, objs)
    trig = next(o for o in objs if o.id.endswith("foresttrig.xml"))
    hero.coords_x = trig.coords_x
    hero.coords_y = trig.coords_y + 40
    seq = try_touch_sequence(hero, objs)
    assert seq is not None
    clock.timer = 10.0
    stalled = 0
    last = None
    for _frame in range(600):
        clock.timer += 0.05
        only.action = TRUE if box.activated and box.state == TEXTBOX_CONFIRMATION else 0
        if box.activated and box.state != TEXTBOX_CONFIRMATION and _frame % 3 == 0:
            only.action = TRUE
        seq = play_sequence(seq, box, only, None, None)
        if seq is None:
            break
        key = seq.current_command
        if key == last:
            stalled += 1
            assert stalled < 80, f"scene stuck on command {key}"
        else:
            stalled = 0
            last = key
    assert seq is None
    assert events.now[1020] != 0
    assert only.action_lock == 0
