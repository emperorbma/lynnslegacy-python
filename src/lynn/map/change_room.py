"""FB engine--LL.bas change_room static FSM.

Walk-on teles and scripted __change_map arm this machine. Each tick advances
one state: invincible → fade out → swap room/map → fade in → vulnerable →
start pending room/entry seq and clear switch_room.

Port-only preserve: Ignia mace landing nudge and pending_visited still run
inside enter_map. ItemSwitch defaults stay Original.
"""

from __future__ import annotations

import lynn.events as events
from lynn import clock
from lynn.constants import LLFADE_GRAY, LLFADE_NORMAL, LLFADE_WHITE, TRUE
from lynn.object.char import CharType
from lynn.object.seq_funcs import (
    __fade_down_to_color,
    __fade_down_to_gray,
    __fade_to_black,
    __fade_to_white,
    __fade_up_to_color,
    __make_invincible,
    __make_vulnerable,
)

_switch_type = -1
_switch_state = -1
_pending_seq = None


def init_change_room(t: int) -> None:
    """FB change_room(0, -1, t): arm the FSM for type 0 (room) or 1 (map)."""
    global _switch_type, _switch_state, _pending_seq
    _switch_type = int(t)
    _switch_state = 0
    _pending_seq = None


def change_room_active() -> bool:
    return _switch_state >= 0


def reset_change_room() -> None:
    global _switch_type, _switch_state, _pending_seq
    _switch_type = -1
    _switch_state = -1
    _pending_seq = None


def _filename_key(name: str | None) -> str:
    return str(name or "").replace("\\", "/").lower()


def _stash_seq(seq_list) -> None:
    global _pending_seq
    if seq_list:
        _pending_seq = seq_list[0]
    else:
        _pending_seq = None


def _arm_type0_song(demo, tele_i: int) -> None:
    from lynn.audio import room_song_index

    room = demo.game_map.room[demo.hero_room]
    dest_i = int(room.teleport[tele_i].to_room)
    if not (0 <= dest_i < len(demo.game_map.room)):
        return
    events.song_wait = room_song_index(demo.game_map.room[dest_i])
    if events.song and events.song != events.song_wait:
        events.song_fade = TRUE


def _arm_type1_song(demo, hero: CharType) -> None:
    if hero.switch_room == -2:
        events.song_fade = TRUE
        events.song_wait = -1
        return
    room = demo.game_map.room[demo.hero_room]
    if not (0 <= hero.switch_room < len(room.teleport)):
        return
    tele = room.teleport[hero.switch_room]
    to_song = int(tele.to_song)
    fname = _filename_key(demo.game_map.filename)
    now = events.now

    def regular_change() -> None:
        events.song_wait = to_song
        events.song_fade = TRUE

    # FB house/town hacks: after Grult (happen 199), keep the current track
    # when leaving inhouse with to_song 9, or leaving forest_fall town (r4).
    if fname.endswith("inhouse.map") and to_song == 9 and now[199] != 0:
        return
    if fname.endswith("forest_fall.map") and demo.hero_room == 4 and now[199] != 0:
        return
    if to_song != events.song:
        regular_change()


def _do_same_map_swap(demo, hero: CharType) -> None:
    from lynn.demos import del_room_enemies, set_up_room_enemies
    from lynn.map.minimap import mark_visited

    room = demo.game_map.room[demo.hero_room]
    tele = room.teleport[hero.switch_room]
    hero.coords_x = tele.dx
    hero.coords_y = tele.dy
    dest_room = int(tele.to_room)
    if dest_room != demo.hero_room:
        load_images = demo.load_images != 0
        del_room_enemies(demo, demo.hero_room)
        demo.hero_room = dest_room
        events.hero_room = dest_room
        events.dark = demo.game_map.room[dest_room].dark
        set_up_room_enemies(demo, dest_room, load_images=load_images)
        _stash_seq(demo.game_map.room[dest_room].seq)


def _do_map_swap(demo, hero: CharType) -> None:
    from lynn.demos import enter_map

    dest = hero.to_map
    entry_i = int(hero.to_entry)
    enter_map(
        demo,
        dest,
        entry_i,
        load_images=demo.load_images != 0,
        load_tileset=demo.load_tileset != 0,
        from_change_room=True,
    )
    entry = None
    if demo.game_map.entry and 0 <= entry_i < len(demo.game_map.entry):
        entry = demo.game_map.entry[entry_i]
    elif demo.game_map.entry:
        entry = demo.game_map.entry[0]
    if entry is not None:
        _stash_seq(entry.seq)


def _start_song_after_swap(demo) -> None:
    from lynn.audio import LLMusic_StartIndex, room_song_index, start_room_song

    if events.song_wait == -1:
        room_i = demo.hero_room
        if 0 <= room_i < len(demo.game_map.room):
            events.song_wait = room_song_index(demo.game_map.room[room_i])
    if events.song_fade != 0:
        # to_song 0 on several seed teles means "unset", not "play silence".
        # Seat the dest room theme (town.it after Grult, etc.).
        if events.song_wait == 0 and 0 <= demo.hero_room < len(demo.game_map.room):
            events.song_wait = room_song_index(demo.game_map.room[demo.hero_room])
        events.song = int(events.song_wait)
        LLMusic_StartIndex(events.song)
    else:
        # Keep current track (house/town hacks). Still seat a theme if silent.
        if not events.song and 0 <= demo.hero_room < len(demo.game_map.room):
            start_room_song(room_song_index(demo.game_map.room[demo.hero_room]))


def _apply_visibility(demo) -> None:
    from lynn.demos import _apply_enter_visibility

    only = getattr(demo, "hero_only", None)
    _apply_enter_visibility(demo.hero, only)


def _promote_pending_seq(demo) -> None:
    global _pending_seq
    seq = _pending_seq
    _pending_seq = None
    if seq is None or demo.hero is None:
        return
    from lynn.sequence import bind_sequence_ents

    seq.current_command = 0
    for cmd in seq.Command:
        for ent in cmd.ent:
            ent.ent_func = 0
    room_objs = (
        demo.objects_by_room[demo.hero_room]
        if demo.hero_room < len(demo.objects_by_room)
        else []
    )
    bind_sequence_ents(seq, demo.hero, room_objs)
    demo.seq = seq
    events.do_hud = 0
    demo.do_hud = 0


def tick_change_room(demo) -> None:
    """FB change_room(hero): one FSM step. No-op when not armed."""
    global _switch_type, _switch_state

    hero = demo.hero
    if hero is None or hero.switch_room == -1 or _switch_state < 0:
        return

    only = getattr(demo, "hero_only", None)
    if _switch_state == 0:
        for i in range(min(4, len(hero.momentum))):
            hero.momentum[i] = 0.0
        if _switch_type == 0:
            _arm_type0_song(demo, hero.switch_room)
        elif _switch_type == 1:
            _arm_type1_song(demo, hero)
        _switch_state += __make_invincible(hero)
        return

    if _switch_state == 1:
        if only is not None and (only.fadeStyle & LLFADE_WHITE) != 0:
            _switch_state += __fade_to_white(hero)
        else:
            if hero.fade_out == 0:
                hero.fade_out = 63
            _switch_state += __fade_to_black(hero)
        if _switch_state == 2:
            hero.fade_out = 0
            hero.song_fade_count = 0
            if events.song_fade != 0:
                from lynn.audio import LLMusic_Stop

                LLMusic_Stop()
        return

    if _switch_state == 2:
        if _switch_type == 0:
            events.current_seq = None
            demo.seq = None
            _do_same_map_swap(demo, hero)
            _switch_state += 1
        else:
            _do_map_swap(demo, hero)
            _switch_state += 1
        _start_song_after_swap(demo)
        if only is not None and only.isLoading != 0:
            only.isLoading = 0
            events.do_hud = TRUE
            demo.do_hud = TRUE
        _apply_visibility(demo)
        return

    if _switch_state == 3:
        if only is not None and (only.fadeStyle & LLFADE_GRAY) != 0:
            _switch_state += __fade_down_to_gray(hero)
        elif only is not None and (only.fadeStyle & LLFADE_WHITE) != 0:
            _switch_state += __fade_down_to_color(hero)
        else:
            _switch_state += __fade_up_to_color(hero)
        if _switch_state == 4:
            events.song_fade = 0
        return

    if _switch_state == 4:
        _switch_state += __make_vulnerable(hero)
        return

    if _switch_state == 5:
        _promote_pending_seq(demo)
        hero.switch_room = -1
        hero.to_map = ""
        if demo.game_map.isDungeon != 0:
            from lynn.map.minimap import mark_visited

            mark_visited(demo.minimap, demo.hero_room)
        if only is not None:
            only.fadeStyle = LLFADE_NORMAL
        _switch_state = -1
        _switch_type = -1


def finish_change_room(demo, limit: int = 8000) -> None:
    """Advance the FSM to completion (tests / sync load helpers)."""
    hero = demo.hero
    if hero is None or hero.switch_room == -1:
        return
    for _ in range(limit):
        clock.timer += max(float(hero.fade_time or 0.003), 0.003)
        tick_change_room(demo)
        if hero.switch_room == -1:
            return
    raise AssertionError("change_room FSM did not finish")


def arm_walk_teleport(demo) -> bool:
    """FB check_against_teles: if on a pad, set switch_room and init the FSM."""
    hero = demo.hero
    if hero is None or hero.switch_room != -1:
        return False
    room_i = demo.hero_room
    if not (0 <= room_i < len(demo.game_map.room)):
        return False
    room = demo.game_map.room[room_i]
    from lynn.map.collision import check_teleports

    tele_i = check_teleports(hero, room.teleport, room.teleports)
    if tele_i == -1:
        return False
    tele = room.teleport[tele_i]
    if tele.to_map != "":
        hero.to_map = tele.to_map
        hero.to_entry = tele.to_room
        init_change_room(1)
    else:
        init_change_room(0)
    hero.switch_room = tele_i
    hero.fade_time = 0.003
    return True
