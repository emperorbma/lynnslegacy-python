"""Start of game to end-game credits, headless.

Continues ``play_to_island`` through Arx → Divius → Logosta → the dry world
→ Limbo → the Dimension Seed → the final scenes, until ``__set_finish`` fires
and the credits roll to the end. Like FB and Lua, the game quits after the
credits instead of returning to the menu.
"""

from collections import deque

import pygame

import lynn.object  # noqa: F401
from lynn import clock
from lynn.constants import DF_MAIN_CHAR, u_divine_bug
from lynn.credits import PHASE_DONE, PHASE_END_KEY, CreditRoll, credits_lines
from lynn.demos import MapDemo, consume_title_events
import lynn.events as events
from lynn.events import bind_room, reset_events
from lynn.hero import update_cam
from lynn.map.loader import load_mapV
from lynn.object.combat import LLObject_ProcessHurt
from lynn.object.tick import LLObject_CheckSpawn, tick_objects
from lynn.paths import resolve_map_path
from lynn.sequence import play_sequence
from test_critical_path import _map_stem, _take_tele, play_to_island

_GRAPH = {}
_DRY_WORLD = {
    "evmount_dry", "evernight_dry", "between", "forest_dry", "inhouse",
    "valley", "cityruin", "limbo1", "limbo2", "limbo3", "thalamus",
    "limbo_arena",
}


def _gm(name: str):
    name = name.replace(".map", "")
    if name not in _GRAPH:
        _GRAPH[name] = load_mapV(str(resolve_map_path(name)), load_tileset=False)
    return _GRAPH[name]


def _pump(demo: MapDemo, frames: int, until=None, need_seq: bool = False):
    """One main-loop frame at a time, as main.py runs it."""
    seen = not need_seq
    for i in range(frames):
        room_i = demo.hero_room
        objs = demo.objects_by_room[room_i]
        bind_room(demo.game_map.room[room_i], objs)
        if demo.seq is None and events.pending_seq is not None:
            demo.seq = events.pending_seq
            events.pending_seq = None
        if demo.seq is not None:
            clock.timer += 0.05
            if demo.box.activated:
                demo.hero_only.action = 1
            demo.seq = play_sequence(demo.seq, demo.box, demo.hero_only)
            demo.hero_only.action = 0
            for o in objs:
                LLObject_CheckSpawn(o)
        if consume_title_events(demo) or events.xxyxx:
            return "end"
        demo.hero_room = events.hero_room
        room_i = demo.hero_room
        objs = demo.objects_by_room[room_i]
        bind_room(demo.game_map.room[room_i], objs)
        clock.timer += 0.017
        tick_objects(objs, update_cam(demo.hero, demo.game_map.room[room_i]))
        seen = seen or demo.seq is not None
        if until and seen and until():
            return i
    return None


def _idle(demo: MapDemo) -> bool:
    return demo.seq is None and events.pending_seq is None and not demo.hero.to_map


def _settle(demo: MapDemo, frames: int = 6000) -> None:
    _pump(demo, frames, lambda: _idle(demo))
    demo.hero_room = events.hero_room


def _step_tele(demo: MapDemo, tele_i: int) -> None:
    _take_tele(demo, tele_i)
    demo.hero_room = events.hero_room
    _settle(demo)


def _route(demo: MapDemo, target: str, allowed=None):
    """Teleport hops to the first room of ``target``, never crossing ``allowed``'s outside."""
    start = (_map_stem(demo), demo.hero_room)
    prev = {start: None}
    q = deque([start])
    while q:
        node = q.popleft()
        m, r = node
        if m == target:
            path = []
            while prev[node]:
                path.append(prev[node][1])
                node = prev[node][0]
            return path[::-1]
        for ti, t in enumerate(_gm(m).room[r].teleport):
            if t.to_map == "":
                nxt = (m, t.to_room)
            else:
                nm = t.to_map.replace(".map", "")
                nxt = (nm, _gm(nm).entry[t.to_room].room)
            if nxt in prev or (allowed is not None and nxt[0] not in allowed):
                continue
            prev[nxt] = (node, (m, r, ti))
            q.append(nxt)
    return None


def _goto(demo: MapDemo, target: str, allowed=None) -> None:
    for _ in range(80):
        cur = _map_stem(demo)
        if cur == target:
            return
        path = _route(demo, target, allowed)
        assert path, (cur, demo.hero_room, target)
        m, r, ti = path[0]
        assert (m, r) == (cur, demo.hero_room)
        _step_tele(demo, ti)
    raise AssertionError(f"never reached {target}")


def _goto_room(demo: MapDemo, target: int) -> None:
    gm = demo.game_map
    start = demo.hero_room
    prev = {start: None}
    q = deque([start])
    while q:
        r = q.popleft()
        if r == target:
            break
        for ti, t in enumerate(gm.room[r].teleport):
            if t.to_map == "" and t.to_room not in prev:
                prev[t.to_room] = (r, ti)
                q.append(t.to_room)
    assert target in prev
    path = []
    r = target
    while prev[r]:
        path.append(prev[r])
        r = prev[r][0]
    for r, ti in path[::-1]:
        assert demo.hero_room == r
        _step_tele(demo, ti)


def _kill(o) -> None:
    o.invincible = 0
    o.hurt = o.hp
    o.dmg_id = DF_MAIN_CHAR
    LLObject_ProcessHurt(o)


def _find(objs, name: str):
    return next(o for o in objs if o.id.endswith(name))


def test_critical_path_start_to_credits():
    pygame.display.init()
    pygame.display.set_mode((10, 10))
    try:
        _play_start_to_credits()
    finally:
        reset_events()
        clock.timer = 0.0
        pygame.quit()


def _play_start_to_credits():
    demo = play_to_island()
    _pump(demo, 800, lambda: demo.seq is None)
    assert _map_stem(demo) in ("island", "title_flash")

    # Island → Arx → desert → Evernight → Interport → Divius.
    if _map_stem(demo) == "island":
        _take_tele(demo, 0)
    _pump(demo, 4000, lambda: _map_stem(demo) == "arx" and demo.seq is None)
    assert _map_stem(demo) == "arx"
    for stop in ("desert", "evernight", "evmount", "interport6", "divius"):
        _goto(demo, stop)
    assert _map_stem(demo) == "divius"

    # Divine fight in room 118 → chapter card → Logosta.
    _goto_room(demo, 118)
    objs = demo.objects_by_room[118]
    statue, bug = objs[20], objs[22]
    statue.hp = 0
    _pump(demo, 3000, lambda: bug.unique_id == u_divine_bug and events.now[681] != 0)
    bug.hp = 0
    _pump(demo, 12000, lambda: _map_stem(demo) == "l_entry" and demo.seq is None)
    assert _map_stem(demo) == "l_entry"

    # Logosta: Ferus, then the core, then the research pod.
    _goto(demo, "l_restricted")
    _goto(demo, "l_arena")
    _settle(demo, 3000)
    objs = demo.objects_by_room[demo.hero_room]
    ferus = _find(objs, "ferus.xml")
    demo.hero.coords_x, demo.hero.coords_y = 328, 300
    _kill(ferus)
    _pump(demo, 12000, lambda: _idle(demo) and ferus.dead, need_seq=True)
    assert ferus.dead
    core = _find(objs, "core.xml")
    _kill(core)
    _pump(demo, 20000, lambda: _idle(demo) and core.dead, need_seq=True)
    assert core.dead

    for _ in range(4):
        if _map_stem(demo) == "evmount_dry":
            break
        path = _route(demo, "l_research")
        assert path
        _step_tele(demo, path[0][2])
    _pump(demo, 9000, lambda: _idle(demo) and _map_stem(demo) == "evmount_dry")
    assert _map_stem(demo) == "evmount_dry"
    assert events.color_mode == 0

    # Dry world → Limbo → Thalamus → the Dimension Seed's arena.
    for stop in ("limbo1", "limbo2", "limbo3", "limbo_arena"):
        _goto(demo, stop, _DRY_WORLD)
    assert _map_stem(demo) == "limbo_arena"

    events.load_images = 1
    demo.load_images = 1
    _pump(demo, 4000, lambda: _idle(demo), need_seq=True)
    objs = demo.objects_by_room[demo.hero_room]
    seed = _find(objs, "battleseed.xml")
    _pump(demo, 600)
    _kill(seed)
    assert seed.dead

    # Death scene → between → Moth2 → Wyvern Ray → between2 → set_finish.
    assert _pump(demo, 40000) == "end"
    assert events.xxyxx != 0
    assert _map_stem(demo) == "between2"

    # Credits run to the end; the game then quits rather than returning to the menu.
    roll = CreditRoll(events.hero, credits_lines(), moth_frames=4)
    t = 1000.0
    for _ in range(8000):
        if roll.phase == PHASE_DONE:
            break
        t += 0.08
        roll.step(t, key_down=roll.phase == PHASE_END_KEY)
    assert roll.phase == PHASE_DONE
