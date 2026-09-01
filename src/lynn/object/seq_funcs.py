"""Sequence actors used by the sapling pickup (and later scripts)."""

from __future__ import annotations

import lynn.events as events
from lynn import clock
from lynn.constants import TRUE
from lynn.object.char import CharType
from lynn.object.dispatch import register_func

# FB unique_id values that stay visible after __cripple (chests, rocks, buttons, ghut).
_CRIPPLE_KEEP_VISIBLE = frozenset({2, 3, 4, 5, 6, 33, 34, 35, 36})


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
    """FB object_modification.bas: hide corpse after a short hold (not chests/rocks)."""
    if this.unique_id in _CRIPPLE_KEEP_VISIBLE:
        this.invisible = 0
    else:
        this.invisible = TRUE
    if this.dead_hold == 0:
        this.dead_hold = clock.timer + 0.1
    this.strength = 0
    this.impassable = 0
    this.animating = 0
    this.total_dead = TRUE
    if clock.timer > this.dead_hold:
        this.dead_hold = 0
        return 1
    return 0


def _make_active_anim(n: int):
    def _fn(this: CharType) -> int:
        this.current_anim = n
        this.frame = 0
        return 1

    _fn.__name__ = f"__active_anim_{n}"
    return _fn


def __dir_down(this: CharType) -> int:
    this.direction = 2
    return 1


def __eat_lynn_action(this: CharType) -> int:
    if events.hero_only is not None:
        events.hero_only.action = 0
    return 1


def __fade_to_white(this: CharType) -> int:
    return 1


def __fade_down_to_color(this: CharType) -> int:
    return 1


def __fade_to_red(this: CharType) -> int:
    return 1


def __fade_to_black(this: CharType) -> int:
    return 1


for _name, _fn in list(globals().items()):
    if _name.startswith("__") and callable(_fn) and _name != "__active_animate":
        register_func(_name, _fn)

for _n in range(16):
    register_func(f"__active_anim_{_n}", _make_active_anim(_n))
