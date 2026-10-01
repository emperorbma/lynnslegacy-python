"""TempleWood and Arx gaps: scraps build the bridge, otherwise the gap stays shut."""

from pathlib import Path

import lynn.object  # noqa: F401
from lynn import clock
from lynn.constants import TRUE
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.gfx.box import BoxControl
from lynn.hero import DIR_UP, ctor_hero, ctor_hero_only
from lynn.map.collision import move_object
from lynn.map.loader import load_mapV
from lynn.object.dispatch import lookup_func, __noop
from lynn.object.tick import tick_object
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import resolve_map_path
from lynn.sequence import play_sequence


def _face_block(bridge):
    return bridge.anim[0].frame[0].face[0].impassable


def _load(map_name: str, room_i: int, stem: str):
    m = load_mapV(str(resolve_map_path(map_name)), load_tileset=False)
    room = m.room[room_i]
    stub = next(
        e for e in room.enemy if Path(e.id.replace("\\", "/")).stem == stem
    )
    bridge = spawn_from_stub(stub, load_images=True)
    bridge.num = 0
    return room, bridge


def _stand(room, bridge):
    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    hero.coords_x = bridge.coords_x
    hero.coords_y = bridge.coords_y + 32
    hero.direction = DIR_UP
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero_only(only)
    bind_hero(hero)
    bind_room(room, [bridge])
    return hero, only


def _walk_north(hero, room, bridge, steps: int) -> int:
    hero.direction = DIR_UP
    for _ in range(steps):
        if move_object(hero, room, moment=1, others=[bridge]) == 0:
            break
    return int(hero.coords_y)


def _play(seq, only, bridge):
    box = BoxControl()
    for i in range(4000):
        clock.timer = i * 0.05
        only.action = TRUE
        seq = play_sequence(seq, box, only)
        tick_object(bridge)
        if seq is None:
            return None
        only.action = 0
    return seq


def test_material_bridge_funcs_are_real():
    assert lookup_func("__templewood_bridge") is not lookup_func("__noop")
    assert lookup_func("__arx_bridge") is not lookup_func("__noop")


def test_scraps_build_the_gap_and_lynn_can_cross():
    cases = (
        ("ruins", 0, "tbridge", 1206, "those materials"),
        ("arx", 57, "abridge", 470, "those materials"),
    )
    saved = []
    try:
        for map_name, room_i, stem, flag, line in cases:
            room, bridge = _load(map_name, room_i, stem)
            saved.append((bridge, _face_block(bridge)))
            hero, only = _stand(room, bridge)
            only.hasItem[2] = TRUE
            only.action = TRUE
            tick_object(bridge)
            assert events.pending_seq is bridge.seq[0]
            assert line in events.pending_seq.Command[1].ent[0].text
            seq = events.pending_seq
            events.pending_seq = None
            seq = _play(seq, only, bridge)
            assert seq is None
            assert events.now[flag] != 0
            assert only.hasItem[2] != 0
            assert bridge.invisible == 0
            assert _face_block(bridge) == 0
            hero.coords_x = bridge.coords_x
            hero.coords_y = bridge.coords_y + 48
            assert _walk_north(hero, room, bridge, 80) < bridge.coords_y
    finally:
        for bridge, imp in saved:
            bridge.anim[0].frame[0].face[0].impassable = imp


def test_without_scraps_the_line_plays_once_and_the_gap_stays_shut():
    cases = (
        ("ruins", 0, "tbridge", 1206, 1208),
        ("arx", 57, "abridge", 470, 471),
    )
    saved = []
    try:
        for map_name, room_i, stem, built, nag in cases:
            room, bridge = _load(map_name, room_i, stem)
            saved.append((bridge, _face_block(bridge)))
            hero, only = _stand(room, bridge)
            blocked_at = bridge.coords_y + 48
            hero.coords_y = blocked_at
            only.action = TRUE
            tick_object(bridge)
            assert events.now[nag] != 0
            assert events.now[built] == 0
            assert events.pending_seq is bridge.seq[1]
            assert bridge.invisible != 0
            assert _face_block(bridge) != 0
            events.pending_seq = None
            events.current_seq = None
            only.action = TRUE
            tick_object(bridge)
            assert events.pending_seq is None
            hero.coords_y = blocked_at
            assert _walk_north(hero, room, bridge, 80) >= bridge.coords_y + 16
    finally:
        for bridge, imp in saved:
            bridge.anim[0].frame[0].face[0].impassable = imp


def test_a_saved_bridge_is_open_without_pressing_again():
    room, bridge = _load("ruins", 0, "tbridge")
    original = _face_block(bridge)
    try:
        hero, only = _stand(room, bridge)
        events.now[1206] = TRUE
        only.action = 0
        tick_object(bridge)
        assert events.pending_seq is None
        assert bridge.invisible == 0
        assert _face_block(bridge) == 0
        hero.coords_y = bridge.coords_y + 48
        assert _walk_north(hero, room, bridge, 80) < bridge.coords_y
    finally:
        bridge.anim[0].frame[0].face[0].impassable = original
