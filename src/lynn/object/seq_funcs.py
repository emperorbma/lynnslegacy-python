"""Sequence actors used by the sapling pickup (and later scripts)."""

from __future__ import annotations

import lynn.events as events
from lynn.constants import TRUE
from lynn.object.char import CharType
from lynn.object.dispatch import register_func


def __return_trig(this: CharType) -> int:
    this.return_trig = 1
    return 1


def __give_weapon(this: CharType) -> int:
    only = events.hero_only
    if only is None:
        return 1
    only.has_weapon += 1
    only.weapon = only.has_weapon
    return 1


def __set_happen(this: CharType) -> int:
    chap = int(this.chap)
    if 0 <= chap < len(events.now):
        events.now[chap] = TRUE
    return 1


def __make_visible(this: CharType) -> int:
    this.invisible = 0
    return 1


def __make_invisible(this: CharType) -> int:
    this.invisible = 1
    return 1


def __make_invincible(this: CharType) -> int:
    this.invincible = 1
    return 1


def __make_vulnerable(this: CharType) -> int:
    this.invincible = 0
    return 1


def __make_dead(this: CharType) -> int:
    this.dead = TRUE
    this.invisible = 0
    return 1


def __cripple(this: CharType) -> int:
    return 1


def __active_anim_0(this: CharType) -> int:
    this.current_anim = 0
    this.frame = 0
    return 1


def __active_anim_1(this: CharType) -> int:
    this.current_anim = 1
    this.frame = 0
    return 1


def __fade_to_white(this: CharType) -> int:
    return 1


def __fade_down_to_color(this: CharType) -> int:
    return 1


for _name, _fn in list(globals().items()):
    if _name.startswith("__") and callable(_fn) and _name != "__active_animate":
        register_func(_name, _fn)
