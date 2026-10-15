"""Logosta dungeon: console, wave core, turret triggers."""

from __future__ import annotations

import lynn.events as events
import lynn.object  # noqa: F401  registers funcs
import lynn.object.seq_funcs  # noqa: F401
from lynn.console import ConsoleState, feed_key
from lynn.constants import u_core
from lynn.object.char import CharType
from lynn.object.dispatch import FUNC_REGISTRY
from lynn.object.tick import tick_core_waves


def _obj() -> CharType:
    o = CharType()
    o.funcs.current_func = [0] * 8
    return o


def _type(con: ConsoleState, text: str) -> None:
    for ch in text:
        feed_key(con, 0, ch)


def _research_terminal_run(password: str) -> tuple[list[str], bool]:
    from lynn import clock
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
    from lynn.gfx.box import BoxControl
    from lynn.gfx.palette import load_pal
    from lynn.hero import ctor_hero, ctor_hero_only
    from lynn.map.loader import load_mapV
    from lynn.paths import data_file, resolve_map_path
    from lynn.sequence import bind_sequence_ents, play_sequence

    reset_events()
    hero, hero_only = ctor_hero(), ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(hero_only)
    gm = load_mapV(str(resolve_map_path("l_research")), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=gm,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in gm.room]
    demo.hero, demo.hero_only, demo.box, demo.hero_room = hero, hero_only, BoxControl(), 11
    set_up_room_enemies(demo, 11, load_images=False)
    objs = demo.objects_by_room[11]
    bind_room(gm.room[11], objs)

    seq = objs[1].seq[0]
    bind_sequence_ents(seq, hero, objs)
    visited: list[int] = []
    typed = False
    for _ in range(4000):
        clock.timer += 0.05
        if events.console is not None and not typed:
            _type(events.console, password)
            feed_key(events.console, 13, "")
            typed = True
        if seq is not None and seq in objs[1].seq:
            idx = objs[1].seq.index(seq)
            if not visited or visited[-1] != idx:
                visited.append(idx)
        if demo.box.activated != 0:
            hero_only.action = 1
        seq = play_sequence(seq, demo.box, hero_only)
        hero_only.action = 0
        if seq is None:
            break
    return visited, typed


def test_research_terminal_wrong_password_reports_error():
    visited, typed = _research_terminal_run("nope")
    assert typed
    assert visited == [0, 1]
    assert events.console is None


def test_research_terminal_right_password_unlocks_log():
    visited, typed = _research_terminal_run("FerUs686")
    assert typed
    assert visited == [0, 2]


def test_arena_core_runs_four_waves_then_opens():
    from lynn import clock
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
    from lynn.gfx.box import BoxControl
    from lynn.gfx.palette import load_pal
    from lynn.hero import ctor_hero, ctor_hero_only
    from lynn.map.loader import load_mapV
    from lynn.object.tick import tick_objects
    from lynn.paths import data_file, resolve_map_path

    reset_events()
    hero, hero_only = ctor_hero(), ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(hero_only)
    gm = load_mapV(str(resolve_map_path("l_arena2")), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=gm,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in gm.room]
    demo.hero, demo.hero_only, demo.box, demo.hero_room = hero, hero_only, BoxControl(), 0
    set_up_room_enemies(demo, 0, load_images=False)
    objs = demo.objects_by_room[0]
    bind_room(gm.room[0], objs)
    core = objs[4]
    assert core.unique_id == u_core

    events.now[725] = 1
    try:
        for lo, hi in ((5, 10), (11, 18), (19, 28), (29, 48)):
            for _ in range(3):
                clock.timer += 0.05
                tick_objects(objs)
            assert all(objs[i].trigger for i in range(lo, hi + 1)), (lo, hi)
            assert not any(objs[i].trigger for i in range(hi + 1, 49))
            for i in range(lo, hi + 1):
                objs[i].dead = 1
        for _ in range(3):
            clock.timer += 0.05
            tick_objects(objs)
        assert core.shifty_state == 5
        assert core.funcs.active_state == core.jump_state
    finally:
        events.now[725] = 0


def test_console_funcs_registered():
    for name in ("__logosta_console", "__set_explosions", "__back_3", "__check_trigger"):
        assert name in FUNC_REGISTRY, name


def test_console_editing_and_limit():
    con = ConsoleState(None)
    _type(con, "FerUs686")
    assert con.text == "FerUs686"
    feed_key(con, 8, "")
    assert con.text == "FerUs68"
    _type(con, "abcdefgh")
    assert len(con.text) == 10
    feed_key(con, 13, "")
    assert con.done
    feed_key(con, 0, "x")
    assert len(con.text) == 10


def test_back_3_and_set_explosions():
    o = _obj()
    o.chap = 4
    assert FUNC_REGISTRY["__back_3"](o) == -3
    assert FUNC_REGISTRY["__set_explosions"](o) == 1
    assert o.explosions == 4


def test_check_trigger_only_fires_when_triggered():
    o = _obj()
    o.invincible = 1
    assert FUNC_REGISTRY["__check_trigger"](o) == 1
    assert o.invincible == 1
    o.trigger = 1
    assert FUNC_REGISTRY["__check_trigger"](o) == 1
    assert o.invincible == 0


def test_core_waves_release_in_order(monkeypatch):
    import lynn.audio as audio

    monkeypatch.setattr(audio, "play_sample", lambda *a, **k: None)
    events.now[725] = 1
    try:
        objs = [_obj() for _ in range(49)]
        core = objs[0]
        core.unique_id = u_core
        for wave, lo, hi in ((0, 5, 10), (1, 11, 18), (2, 19, 28), (3, 29, 48)):
            tick_core_waves(core, objs)
            assert all(objs[i].trigger for i in range(lo, hi + 1))
            assert not any(o.trigger for o in objs[hi + 1 :])
            tick_core_waves(core, objs)
            assert core.shifty_state == wave + 1
            for i in range(lo, hi + 1):
                objs[i].dead = 1
        tick_core_waves(core, objs)
        assert core.shifty_state == 5
        assert core.invincible == 0
    finally:
        events.now[725] = 0


def test_core_waves_idle_without_switch():
    events.now[725] = 0
    objs = [_obj() for _ in range(49)]
    tick_core_waves(objs[0], objs)
    assert objs[0].shifty_state == 0
