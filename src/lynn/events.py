"""FB llg(now) happen flags. Sequence funcs read/write this."""

from __future__ import annotations

from lynn.constants import LL_EVENTS_MAX

now: list[int] = [0] * LL_EVENTS_MAX
hero_only = None
current_room = None
current_others = None


def reset_events() -> None:
    global hero_only, current_room, current_others
    for i in range(len(now)):
        now[i] = 0
    hero_only = None
    current_room = None
    current_others = None


def bind_hero_only(only) -> None:
    global hero_only
    hero_only = only


def bind_room(room, others=None) -> None:
    global current_room, current_others
    current_room = room
    current_others = others
