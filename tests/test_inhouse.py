"""inhouse.map talk sequences must hand control back after the last box."""

import lynn.object  # noqa: F401
import lynn.object.move_ai  # noqa: F401

from lynn import clock
from lynn.constants import TRUE
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.gfx.box import BoxControl
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.loader import load_mapV
from lynn.object.char import CharType
from lynn.object.dispatch import FUNC_REGISTRY, lookup_func, __noop
from lynn.object.move_ai import __home
from lynn.object.seq_funcs import __inc_sel_seq
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import resolve_map_path
from lynn.sequence import bind_sequence_ents, play_sequence, try_action_sequence

SF_BOX = 1024


def _inhouse_room(room_i: int):
    reset_events()
    m = load_mapV(str(resolve_map_path("inhouse")), load_tileset=False)
    room = m.room[room_i]
    objs = []
    for stub in room.enemy:
        obj = spawn_from_stub(stub, load_images=False)
        obj.num = len(objs)
        objs.append(obj)
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero_only(only)
    bind_hero(hero)
    bind_room(room, objs)
    return m, hero, only, objs, room


def _play(seq, only, ticks=8000):
    box = BoxControl()
    for i in range(ticks):
        clock.timer = i * 0.05
        only.action = TRUE
        events.keys.enter_pulse = TRUE
        seq = play_sequence(seq, box, only)
        if seq is None:
            events.keys.enter_pulse = 0
            only.action = 0
            return None, i
        only.action = 0
        events.keys.enter_pulse = 0
    return seq, ticks


def test_home_and_inc_sel_seq_are_real():
    assert lookup_func("__home") is not lookup_func("__noop")
    assert lookup_func("__inc_sel_seq") is not lookup_func("__noop")
    o = CharType()
    o.sel_seq = 0
    assert __inc_sel_seq(o) == 1
    assert o.sel_seq == 1


def test_home_reaches_dest_without_a_room():
    reset_events()
    o = CharType()
    o.coords_x = 10
    o.coords_y = 20
    o.dest_x = 48
    o.dest_y = 88
    o.walk_speed = 0.01
    clock.timer = 1.0
    assert __home(o) == 1
    assert (o.coords_x, o.coords_y) == (48, 88)


def test_scientist_intro_hands_back_control():
    _m, hero, only, objs, _room = _inhouse_room(6)
    scientist = next(o for o in objs if o.id.replace("\\", "/").endswith("scientist.xml"))
    hero.coords_x = scientist.coords_x
    hero.coords_y = scientist.coords_y + 16
    hero.direction = 0
    only.action = TRUE
    seq = try_action_sequence(hero, only, objs)
    assert seq is not None
    only.action = 0
    seq, ticks = _play(seq, only)
    assert seq is None, f"scientist seq still running after {ticks} ticks"
    assert only.action_lock == 0
    assert events.do_hud != 0
    assert scientist.sel_seq == 1


def test_book_letter_hands_back_control():
    _m, hero, only, objs, _room = _inhouse_room(0)
    book = next(o for o in objs if o.id.replace("\\", "/").endswith("book.xml"))
    hero.coords_x = book.coords_x
    hero.coords_y = book.coords_y + 16
    hero.direction = 0
    only.action = TRUE
    seq = try_action_sequence(hero, only, objs)
    assert seq is not None
    only.action = 0
    seq, ticks = _play(seq, only)
    assert seq is None, f"book seq still running after {ticks} ticks"
    assert only.action_lock == 0
    assert events.do_hud != 0


def test_deadguy_line_hands_back_control():
    _m, hero, only, objs, _room = _inhouse_room(0)
    dead = next(o for o in objs if o.id.replace("\\", "/").endswith("deadguy.xml"))
    seq = dead.seq[0]
    seq.current_command = 0
    bind_sequence_ents(seq, hero, objs)
    seq, ticks = _play(seq, only)
    assert seq is None, f"deadguy seq still running after {ticks} ticks"
    assert only.action_lock == 0


def _stem(obj) -> str:
    return obj.id.replace("\\", "/").rsplit("/", 1)[-1]


def _func_name(fn) -> str:
    for key, val in FUNC_REGISTRY.items():
        if val is fn:
            return key
    if fn is __noop:
        return "__NOOP"
    return getattr(fn, "__name__", "?")


def _block_names(obj, state: int) -> list[str]:
    if state < 0 or state >= len(obj.funcs.func):
        return [f"MISSING_STATE_{state}"]
    return [_func_name(fn) for fn in obj.funcs.func[state]]


def _inhouse_seq_stalls() -> list[str]:
    """Sequence commands whose actor func block still contains a missing/NOOP."""
    hero = ctor_hero(load_images=False)
    game_map = load_mapV(str(resolve_map_path("inhouse")), load_tileset=False)
    hits: list[str] = []
    for ri, room in enumerate(game_map.room):
        objs = [spawn_from_stub(stub, load_images=False) for stub in room.enemy]
        labeled = [("room", s) for s in room.seq]
        for oi, obj in enumerate(objs):
            for seq in obj.seq:
                labeled.append((f"e{oi}:{_stem(obj)}", seq))
        for label, seq in labeled:
            for ci, cmd in enumerate(seq.Command):
                for ent in cmd.ent:
                    if ent.active_ent == SF_BOX:
                        continue
                    if not (0 <= ent.active_ent < len(seq.ent_code)):
                        hits.append(f"r{ri} {label} cmd{ci} bad active={ent.active_ent}")
                        continue
                    code = seq.ent_code[ent.active_ent]
                    if code == -1:
                        actor, who = hero, "lynn"
                    elif 0 <= code < len(objs):
                        actor, who = objs[code], _stem(objs[code])
                    else:
                        hits.append(f"r{ri} {label} cmd{ci} bad code={code}")
                        continue
                    names = _block_names(actor, ent.ent_state)
                    if any(n == "__NOOP" or n.startswith("MISSING") for n in names):
                        hits.append(
                            f"r{ri} {label} cmd{ci} {who} state={ent.ent_state} {names}"
                        )
    return hits


def test_inhouse_sequences_have_no_missing_funcs():
    hits = _inhouse_seq_stalls()
    assert hits == [], "inhouse seq still hits missing funcs:\n" + "\n".join(hits)


def test_bar_people_hand_back_control():
    _m, hero, only, objs, _room = _inhouse_room(3)
    names = (
        "null.xml",
        "drunkard.xml",
        "drunkard2.xml",
        "samson.xml",
    )
    for name in names:
        matches = [o for o in objs if _stem(o) == name]
        if not matches:
            continue
        obj = matches[0]
        if not obj.seq:
            continue
        for si, raw in enumerate(obj.seq):
            seq = raw
            seq.current_command = 0
            for cmd in seq.Command:
                for ent in cmd.ent:
                    ent.ent_func = 0
            bind_sequence_ents(seq, hero, objs)
            finished, ticks = _play(seq, only)
            assert finished is None, f"{name} seq {si} still running after {ticks} ticks"
            assert only.action_lock == 0
            assert events.do_hud != 0


def test_all_inhouse_object_seqs_hand_back_control():
    """Every stored inhouse object sequence must be able to finish."""
    game_map = load_mapV(str(resolve_map_path("inhouse")), load_tileset=False)
    for ri, room in enumerate(game_map.room):
        _m, hero, only, objs, _room = _inhouse_room(ri)
        for obj in objs:
            for si, raw in enumerate(obj.seq):
                seq = raw
                seq.current_command = 0
                for cmd in seq.Command:
                    for ent in cmd.ent:
                        ent.ent_func = 0
                bind_sequence_ents(seq, hero, objs)
                finished, ticks = _play(seq, only)
                assert finished is None, (
                    f"room {ri} {_stem(obj)} seq {si} still running after {ticks} ticks"
                )
                assert only.action_lock == 0
