"""Can we finish the game, as far as the port currently goes?

This is the live player route, not a pile of one-off map checks. Append the
next shipped dungeon or boss at the bottom of
``test_critical_path_as_far_as_ported`` so a break on the way to the ending
fails in one place.

Shipped so far: forest sapling (the stick) → town portal → Interport → Moenia.
"""

from pathlib import Path

import lynn.object  # noqa: F401

from lynn import clock
from lynn.constants import DF_MAIN_CHAR, TRUE, u_bush
from lynn.demos import MapDemo, set_up_room_enemies, try_hero_teleport
from lynn.events import bind_hero, bind_hero_only, now, reset_events
import lynn.events as events
from lynn.gfx.box import BoxControl
from lynn.gfx.palette import load_pal
from lynn.hero import DIR_UP, ctor_hero, ctor_hero_only, place_hero
from lynn.map.loader import load_mapV
from lynn.object.combat import LLObject_DamageCalc
from lynn.object.tick import tick_objects
from lynn.paths import data_file, resolve_map_path
from lynn.sequence import play_sequence, try_action_sequence


def _map_stem(demo: MapDemo) -> str:
    name = demo.game_map.filename or events.map_filename
    return Path(str(name).replace("\\", "/")).stem.lower()


def _new_game() -> MapDemo:
    reset_events()
    path = resolve_map_path("forest_fall")
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in game_map.room]
    hero = ctor_hero(load_images=False)
    demo.hero = hero
    demo.hero_only = ctor_hero_only()
    demo.hero_room = place_hero(hero, game_map, 0)
    demo.box = BoxControl()
    bind_hero(hero)
    bind_hero_only(demo.hero_only)
    events.map_filename = Path(path).name
    events.hero_room = demo.hero_room
    return demo


def _stand_on_tele(hero, tele) -> None:
    hero.coords_x = tele.x
    hero.coords_y = tele.y
    if tele.w == 0:
        hero.coords_x = tele.x - (hero.perimeter_x >> 1)
    else:
        hero.coords_x = tele.x
    if tele.h == 0:
        hero.coords_y = tele.y - (hero.perimeter_y >> 1)
    else:
        hero.coords_y = tele.y - hero.perimeter_y + 1


def _take_tele(demo: MapDemo, tele_i: int) -> None:
    room = demo.game_map.room[demo.hero_room]
    tele = room.teleport[tele_i]
    _stand_on_tele(demo.hero, tele)
    try_hero_teleport(demo)
    demo.hero_room = events.hero_room if demo.hero is not None else demo.hero_room


def _play_until_done(demo: MapDemo, seq, limit: int = 500) -> None:
    box = demo.box if demo.box is not None else BoxControl()
    demo.box = box
    only = demo.hero_only
    for i in range(limit):
        clock.timer = i * 0.05
        if box.activated != 0:
            only.action = TRUE
        seq = play_sequence(seq, box, only)
        only.action = 0
        if seq is None:
            demo.seq = None
            return
    raise AssertionError("sequence did not finish")


def _objs(demo: MapDemo):
    return demo.objects_by_room[demo.hero_room]


def _named(demo: MapDemo, suffix: str):
    suffix = suffix.lower()
    for obj in _objs(demo):
        if obj.id.replace("\\", "/").lower().endswith(suffix):
            return obj
    return None


def _pick_up_sapling(demo: MapDemo) -> None:
    sapling = _named(demo, "sapling.xml")
    assert sapling is not None, "room 1 has no sapling"
    hero = demo.hero
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    sapling.perimeter_x = 16
    sapling.perimeter_y = 8
    hero.direction = DIR_UP
    hero.coords_x = sapling.coords_x
    hero.coords_y = sapling.coords_y + 7
    demo.hero_only.action = TRUE
    seq = try_action_sequence(hero, demo.hero_only, _objs(demo))
    assert seq is not None, "sapling action sequence did not start"
    demo.hero_only.action = 0
    _play_until_done(demo, seq)
    assert demo.hero_only.has_weapon == 0
    assert demo.hero_only.weapon == 0
    assert now[3] != 0


def _cut_south_bushes(demo: MapDemo) -> None:
    bushes = [
        o
        for o in _objs(demo)
        if o.unique_id == u_bush and int(o.coords_y) == 496
    ]
    assert len(bushes) == 3, "the three south bushes that block the town path"
    for bush in bushes:
        bush.dmg_id = DF_MAIN_CHAR
        LLObject_DamageCalc(bush)
    for i in range(40):
        clock.timer = i * 0.05
        tick_objects(_objs(demo))
        if all(b.impassable == 0 or b.dead != 0 for b in bushes):
            break
    assert all(b.impassable == 0 or b.dead != 0 for b in bushes)


def _drain_entry_seq(demo: MapDemo) -> None:
    if demo.seq is None:
        return
    _play_until_done(demo, demo.seq)


def test_critical_path_as_far_as_ported():
    """Player route through everything the port currently implements.

    Today that ends at Moenia's front door. When powder / ice / Grult (and
    later dungeons) ship, keep appending onto this function in route order.
    """
    demo = _new_game()
    assert _map_stem(demo) == "forest_fall"
    assert demo.hero_room == 0
    assert demo.hero_only.weapon == -1

    # Overworld south strip -> sapling grove.
    _take_tele(demo, 0)
    assert demo.hero_room == 1

    _pick_up_sapling(demo)
    _cut_south_bushes(demo)

    # Grove south -> field -> town north edge.
    _take_tele(demo, 1)
    assert demo.hero_room == 2
    _take_tele(demo, 1)
    assert demo.hero_room == 4

    # Town portal pad -> Interport hub -> Moenia entry 0.
    _take_tele(demo, 10)
    assert _map_stem(demo) == "interport"
    _drain_entry_seq(demo)
    _take_tele(demo, 0)
    assert _map_stem(demo) == "moenia"
    assert demo.hero_room == 0
    assert demo.hero_only.weapon == 0
    assert now[3] != 0
