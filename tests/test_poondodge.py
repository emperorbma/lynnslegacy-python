"""Evernight Silk is a chest flag, then Poondodge finishes the ninja suit."""

import lynn.object  # noqa: F401
import lynn.object.move_ai  # noqa: F401

import lynn.clock as clock
from lynn.constants import TRUE
from lynn.demos import MapDemo, set_up_room_enemies
from lynn.events import bind_hero, bind_hero_only, now, reset_events
from lynn.gfx.box import BoxControl
from lynn.gfx.palette import load_pal
from lynn.hero import DIR_UP, ctor_hero, ctor_hero_only
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.seq_funcs import __poondodge_branch
from lynn.object.tick import tick_object, tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import data_file, resolve_map_path
from lynn.sequence import play_sequence, try_action_sequence


def _room(map_name: str, room_i: int):
    reset_events()
    game_map = load_mapV(str(resolve_map_path(map_name)), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    demo.hero.perimeter_x = 16
    demo.hero.perimeter_y = 16
    demo.hero.direction = DIR_UP
    demo.hero_room = room_i
    demo.box = BoxControl()
    set_up_room_enemies(demo, room_i, load_images=False)
    bind_hero(demo.hero)
    bind_hero_only(demo.hero_only)
    return demo, demo.objects_by_room[room_i]


def _face(hero, obj) -> None:
    hero.direction = DIR_UP
    hero.coords_x = obj.coords_x
    hero.coords_y = obj.coords_y + 15


def _finish(seq, box, only, objs, limit=800):
    for _ in range(limit):
        clock.timer += 0.05
        if box.activated != 0:
            only.action = TRUE
        seq = play_sequence(seq, box, only)
        only.action = 0
        tick_objects(objs)
        if seq is None:
            return
    raise AssertionError(f"sequence stalled at command {seq.current_command}")


def _named(objs, stem: str):
    return next(o for o in objs if str(o.id).replace("\\", "/").endswith(stem))


def test_poondodge_branch_arms_the_turn_in_only_with_the_silk():
    reset_events()
    tailor = CharType()
    assert lookup_func("__poondodge_branch") is not lookup_func("__noop")
    assert __poondodge_branch(tailor) == 1
    assert tailor.sel_seq == 0
    now[1221] = TRUE
    assert __poondodge_branch(tailor) == 1
    assert tailor.sel_seq == 1
    now[1220] = TRUE
    tailor.sel_seq = 0
    assert __poondodge_branch(tailor) == 1
    assert tailor.sel_seq == 0


def test_evernight_chest_gives_the_silk_once():
    demo, objs = _room("evernight", 1)
    chest = next(
        o
        for o in objs
        if str(o.id).replace("\\", "/").endswith("chest.xml")
        and o.seq
        and "Evernight Silk" in o.seq[0].Command[1].ent[0].text
    )
    assert chest.funcs.func[3][1].__name__ == "__set_happen"
    _face(demo.hero, chest)
    demo.hero_only.action = TRUE
    seq = try_action_sequence(demo.hero, demo.hero_only, objs)
    demo.hero_only.action = 0
    assert seq is chest.seq[0]
    assert seq.Command[0].ent[0].chap == 1221
    _finish(seq, demo.box, demo.hero_only, objs)
    assert now[1221] != 0
    assert demo.hero.key == 0
    assert chest.spawn_kill_trig != 0
    assert chest.current_anim == 1
    demo.hero_only.action = TRUE
    assert try_action_sequence(demo.hero, demo.hero_only, objs) is None


def test_talking_without_the_silk_is_the_carpet_line():
    demo, objs = _room("inhouse", 7)
    tailor = _named(objs, "poondodge.xml")
    tick_object(tailor)
    assert tailor.sel_seq == 0
    _face(demo.hero, tailor)
    demo.hero_only.action = TRUE
    seq = try_action_sequence(demo.hero, demo.hero_only, objs)
    assert seq is tailor.seq[0]
    assert "carpet" in seq.Command[1].ent[0].text


def test_turning_in_the_silk_finishes_the_ninja_suit():
    demo, objs = _room("inhouse", 7)
    tailor = _named(objs, "poondodge.xml")
    unfinished = _named(objs, "ninja.xml")
    finished = _named(objs, "ninja2.xml")
    assert finished.spawn_wait_trig == 0
    assert "blank.spr" in str(finished.anim[0].filename).replace("\\", "/")
    now[1221] = TRUE
    tick_object(tailor)
    assert tailor.sel_seq == 1
    _face(demo.hero, tailor)
    demo.hero_only.action = TRUE
    seq = try_action_sequence(demo.hero, demo.hero_only, objs)
    demo.hero_only.action = 0
    assert seq is tailor.seq[1]
    assert "evernight silk" in seq.Command[0].ent[0].text.lower()
    assert seq.Command[2].ent[0].chap == 1220
    money = demo.hero.money
    _finish(seq, demo.box, demo.hero_only, objs)
    assert now[1220] != 0
    assert events_fade_clear()
    assert unfinished.spawn_kill_trig != 0
    assert finished.spawn_wait_trig != 0
    assert finished.action_sequence != 0
    assert "ninja2" in str(finished.anim[0].filename).replace("\\", "/").lower()
    _face(demo.hero, finished)
    demo.hero_only.action = TRUE
    seq = try_action_sequence(demo.hero, demo.hero_only, objs)
    demo.hero_only.action = 0
    assert seq is finished.seq[0]
    assert "Evernight Silk" in seq.Command[1].ent[0].text
    assert seq.Command[2].ent[0].chap == 3
    _finish(seq, demo.box, demo.hero_only, objs)
    assert demo.hero_only.hasCostume[3] != 0
    assert demo.hero.money == money
    assert now[1225] != 0


def events_fade_clear() -> bool:
    import lynn.events as events

    return events.fade_white == 0 and events.fade_black == 0


def test_poondodge_idle_is_the_branch():
    obj = CharType()
    obj.id = "data/object/poondodge.xml"
    LLSystem_ObjectFromXML(obj, load_images=False)
    assert obj.funcs.func[0][0].__name__ == "__poondodge_branch"
