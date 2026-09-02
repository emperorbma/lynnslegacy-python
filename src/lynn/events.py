"""FB llg(now) happen flags. Sequence funcs read/write this."""

from __future__ import annotations

from dataclasses import dataclass

from lynn.constants import LL_EVENTS_MAX, TRUE

now: list[int] = [0] * LL_EVENTS_MAX
hero_only = None
hero = None
current_room = None
current_others = None
do_hud = TRUE
box_entity = None
map_filename = ""
hero_room = 0
fade_white = 0
fade_black = 0
do_chap = 0
pending_seq = None
current_seq = None
seq_box = None
pending_load = None
request_quit = 0
goto_title = 0
song = 0
song_fade = 0
song_wait = 0


@dataclass
class KeyState:
    up: int = 0
    down: int = 0
    left: int = 0
    right: int = 0
    enter: int = 0
    escape: int = 0
    enter_pulse: int = 0


keys = KeyState()


def reset_events() -> None:
    global hero_only, hero, current_room, current_others, do_hud, box_entity, map_filename, hero_room, fade_white, fade_black, do_chap, pending_seq, current_seq, seq_box, pending_load, request_quit, goto_title, song, song_fade, song_wait
    for i in range(len(now)):
        now[i] = 0
    hero_only = None
    hero = None
    current_room = None
    current_others = None
    do_hud = TRUE
    box_entity = None
    map_filename = ""
    hero_room = 0
    fade_white = 0
    fade_black = 0
    do_chap = 0
    pending_seq = None
    current_seq = None
    seq_box = None
    pending_load = None
    request_quit = 0
    goto_title = 0
    song = 0
    song_fade = 0
    song_wait = 0
    keys.up = keys.down = keys.enter = keys.escape = keys.enter_pulse = 0
    keys.left = keys.right = 0


def bind_hero_only(only) -> None:
    global hero_only
    hero_only = only


def bind_hero(h) -> None:
    global hero
    hero = h


def bind_room(room, others=None) -> None:
    global current_room, current_others
    current_room = room
    current_others = others
