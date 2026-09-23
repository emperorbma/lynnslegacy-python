"""Gelidus ice cave: chasm bridge (happen 357) and related switches."""

from pathlib import Path

import lynn.object  # noqa: F401
import lynn.object.move_ai  # noqa: F401
from lynn.constants import TRUE
from lynn.events import bind_hero, bind_room, reset_events
import lynn.events as events
from lynn.hero import ctor_hero
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.tick import tick_object, tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import resolve_map_path
from lynn.sequence import try_touch_sequence


def _stem(o) -> str:
    return Path(str(o.id).replace("\\", "/")).name.lower()


def test_bridge_chasm_is_implemented():
    reset_events()
    chasm = CharType()
    chasm.id = "data/object/geliduschasm.xml"
    chasm = LLSystem_ObjectFromXML(chasm, load_images=False)
    assert lookup_func("__bridge_chasm") is not lookup_func("__noop")
    assert chasm.impassable != 0
    assert lookup_func("__bridge_chasm")(chasm) == 1
    assert chasm.impassable != 0
    events.now[357] = TRUE
    assert lookup_func("__bridge_chasm")(chasm) == 0
    assert chasm.impassable == 0
    assert chasm.funcs.active_state == chasm.reset_state


def test_gelidus_r15_button_opens_chasm():
    reset_events()
    m = load_mapV(str(resolve_map_path("gelidus")), load_tileset=False)
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.gfx.palette import load_pal
    from lynn.hero import ctor_hero_only
    from lynn.paths import data_file

    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=m,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    demo.hero.perimeter_x = 16
    demo.hero.perimeter_y = 16
    demo.hero_room = 15
    set_up_room_enemies(demo, 15, load_images=False)
    objs = demo.objects_by_room[15]
    bind_hero(demo.hero)
    bind_room(m.room[15], objs)
    button = next(o for o in objs if _stem(o) == "button.xml")
    chasms = [o for o in objs if _stem(o) == "geliduschasm.xml"]
    assert len(chasms) == 3
    assert all(c.impassable != 0 for c in chasms)
    demo.hero.coords_x = button.coords_x
    demo.hero.coords_y = button.coords_y
    seq = try_touch_sequence(demo.hero, objs)
    assert seq is not None
    from lynn.gfx.box import BoxControl
    from lynn.sequence import play_sequence

    box = BoxControl()
    for _ in range(40):
        seq = play_sequence(seq, box, demo.hero_only)
        tick_objects(objs)
        if seq is None:
            break
    assert events.now[357] != 0
    for _ in range(5):
        tick_objects(objs)
    assert all(c.impassable == 0 for c in chasms)
