"""Can we finish the game, as far as the port currently goes?

This is the live player route, not a pile of one-off map checks. Append the
next shipped dungeon or boss at the bottom of
``test_critical_path_as_far_as_ported`` so a break on the way to the ending
fails in one place.

Shipped so far: forest sapling → town portal → Interport → Moenia → Grult →
seed portal back to town, then Lynn can walk.
"""

from pathlib import Path

import lynn.object  # noqa: F401

from lynn import clock
from lynn.constants import DF_MAIN_CHAR, TRUE, u_bush, u_gold, u_grult
from lynn.demos import MapDemo, consume_title_events, try_hero_teleport
from lynn.events import bind_hero, bind_hero_only, bind_room, now, reset_events
import lynn.events as events
from lynn.gfx.box import BoxControl
from lynn.gfx.palette import load_pal
from lynn.hero import DIR_DOWN, DIR_UP, ctor_hero, ctor_hero_only, hero_walk_step, place_hero
from lynn.map.loader import load_mapV
from lynn.object.combat import LLObject_DamageCalc
from lynn.object.tick import LLObject_CheckSpawn, tick_objects
from lynn.paths import data_file, resolve_map_path
from lynn.sequence import play_sequence, try_action_sequence, try_touch_sequence


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


def _play_until_done(demo: MapDemo, seq, limit: int = 2000) -> None:
    box = demo.box if demo.box is not None else BoxControl()
    demo.box = box
    only = demo.hero_only
    room = (
        demo.game_map.room[demo.hero_room]
        if demo.hero_room < len(demo.game_map.room)
        else None
    )
    objs = _objs(demo)
    bind_room(room, objs)
    for i in range(limit):
        clock.timer = i * 0.05
        if box.activated != 0:
            only.action = TRUE
        seq = play_sequence(seq, box, only)
        only.action = 0
        for obj in objs:
            LLObject_CheckSpawn(obj)
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
        if all(b.invisible != 0 for b in bushes):
            break
    assert all(b.dead != 0 for b in bushes)
    assert all(b.impassable == 0 for b in bushes)
    assert all(b.invisible != 0 for b in bushes)


def _drain_entry_seq(demo: MapDemo) -> None:
    if demo.seq is None:
        return
    _play_until_done(demo, demo.seq)


def _moenia_to_grult(demo: MapDemo) -> None:
    """Shortest tele chain r0 -> r22."""
    for tele_i, dest in (
        (2, 13),
        (2, 14),
        (1, 15),
        (1, 16),
        (1, 17),
        (1, 18),
        (3, 20),
        (1, 21),
        (1, 22),
    ):
        _take_tele(demo, tele_i)
        assert demo.hero_room == dest, (tele_i, dest, demo.hero_room)


def _defeat_grult(demo: MapDemo) -> None:
    objs = _objs(demo)
    bind_room(demo.game_map.room[22], objs)
    grult = next(o for o in objs if o.unique_id == u_grult)
    events.dark = 1
    tick_objects(objs)
    assert grult.funcs.active_state == grult.stun_state
    grult.hp = 0
    for i in range(80):
        clock.timer = 20 + i * 0.05
        tick_objects(objs)
        if events.pending_seq is not None:
            demo.seq = events.pending_seq
            events.pending_seq = None
            break
    assert demo.seq is not None, "Grult death sequence did not start"
    _play_until_done(demo, demo.seq)
    assert now[199] != 0
    gold = next(o for o in _objs(demo) if o.id.replace("\\", "/").endswith("gold.xml"))
    assert gold.unique_id == u_gold
    assert gold.spawn_wait_trig != 0


def _seed_portal_home(demo: MapDemo) -> None:
    seed = _named(demo, "seedfloat.xml")
    assert seed is not None, "boss room has no seed"
    hero = demo.hero
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    seed.perimeter_x = 16
    seed.perimeter_y = 16
    hero.coords_x = seed.coords_x
    hero.coords_y = seed.coords_y + 8
    seq = try_touch_sequence(hero, _objs(demo))
    assert seq is not None, "seed touch sequence did not start"
    _play_until_done(demo, seq)
    consume_title_events(demo)
    demo.hero_room = events.hero_room
    assert _map_stem(demo) == "forest_fall"
    assert demo.hero_room == 4
    from lynn.audio import last_song, room_song_index

    assert now[199] != 0
    assert room_song_index(demo.game_map.room[4]) == 21
    assert last_song.replace("\\", "/").endswith("town.it")
    _drain_entry_seq(demo)
    assert demo.seq is None
    assert demo.hero_only.action_lock == 0
    assert last_song.replace("\\", "/").endswith("town.it")


def test_critical_path_as_far_as_ported():
    """Player route through everything the port currently implements.

    Today that ends after Grult, the seed portal, and walking in town.
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

    _moenia_to_grult(demo)
    assert demo.hero_room == 22
    _defeat_grult(demo)
    _seed_portal_home(demo)

    room = demo.game_map.room[demo.hero_room]
    before = (demo.hero.coords_x, demo.hero.coords_y)
    clock.timer += 1.0
    hero_walk_step(demo.hero, room, DIR_DOWN, _objs(demo))
    assert (demo.hero.coords_x, demo.hero.coords_y) != before
    assert demo.hero_only.action_lock == 0
    assert now[199] != 0
    assert now[1001] != 0
    assert now[1002] != 0


def test_post_moenia_real_save_can_play():
    """ll_save4.sav is a real-game post-Moenia slot (ported from our save)."""
    import pytest
    from lynn.demos import set_up_room_enemies
    from lynn.object.save import LLSystem_ReadSaveFile, apply_save_happen, apply_save_hero
    from lynn.paths import project_root

    path = project_root() / "ll_save4.sav"
    if not path.is_file():
        pytest.skip("ll_save4.sav not next to the project")
    save = LLSystem_ReadSaveFile(str(path))
    assert save is not None
    assert save.map == "forest_fall.map"
    assert save.entry == 21
    assert save.weapon == 0
    assert save.hasItem[0] == TRUE
    assert save.b_key == 0
    assert save.hp >= 6
    assert save.maxhp >= 6
    assert 199 in save.happen
    assert 1001 in save.happen
    assert 1002 in save.happen
    demo = _new_game()
    apply_save_happen(save)
    apply_save_hero(demo.hero, demo.hero_only, save)
    demo.hero_room = place_hero(demo.hero, demo.game_map, save.entry)
    events.hero_room = demo.hero_room
    set_up_room_enemies(demo, demo.hero_room, load_images=False)
    _drain_entry_seq(demo)
    assert demo.seq is None
    assert demo.hero_only.action_lock == 0
    assert demo.hero_only.hasItem[0] == TRUE
    room = demo.game_map.room[demo.hero_room]
    before = (demo.hero.coords_x, demo.hero.coords_y)
    clock.timer += 1.0
    hero_walk_step(demo.hero, room, DIR_DOWN, _objs(demo))
    assert (demo.hero.coords_x, demo.hero.coords_y) != before
