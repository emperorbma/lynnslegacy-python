"""FB act_key_in_sub cases 5/6 and their per-frame effects.

Item 5 is the Adrenaline Booster: it costs 3 HP and, for six seconds, adds
damage to every weapon hit. Item 6 is the Healing Symbol: it trades 2 gold
for 1 HP and plays a short sparkle over Lynn.
"""

from __future__ import annotations

from lynn import clock
from lynn.audio import play_sample, sound_heal
from lynn.object.char import CharType

ADRENALINE_SECONDS = 6
ADRENALINE_COST_HP = 3
HEAL_COST_GOLD = 2
HEAL_FRAMES = 5
HEAL_FRAME_SECONDS = 0.1
HEAL_SPRITE_Y_OFF = -8
_ADRENALINE_BONUS = {0: 1, 1: 1, 2: 2}

_adrenaline_state = 0
_healing_timer = 0.0


def use_adrenaline(hero: CharType, only) -> None:
    if only.adrenaline is None and hero.hp > ADRENALINE_COST_HP:
        only.adrenaline = clock.timer + ADRENALINE_SECONDS
        hero.hp -= ADRENALINE_COST_HP
    only.attacking = 0


def use_healing(hero: CharType, only) -> None:
    if only.healing == 0 and hero.hp < hero.maxhp and hero.money > 1:
        hero.hp += 1
        hero.money -= HEAL_COST_GOLD
        only.healing = -1
        play_sample(sound_heal, 80)
    only.attacking = 0


def use_item(hero: CharType, only) -> bool:
    """Run item 5 or 6. Returns False for any other selection."""
    if only.selected_item == 5:
        use_adrenaline(hero, only)
        return True
    if only.selected_item == 6:
        use_healing(hero, only)
        return True
    return False


def adrenaline_bonus(only, weapon: int) -> int:
    if only is None or only.adrenaline is None:
        return 0
    return _ADRENALINE_BONUS.get(int(weapon), 0)


def tick_item_effects(hero: CharType, only) -> None:
    """FB hero_main: the booster's flash and expiry, then the heal sparkle."""
    global _adrenaline_state, _healing_timer
    from lynn.object.seq_funcs import __flash, __flash_down

    if only.adrenaline is not None:
        if _adrenaline_state == 0:
            _adrenaline_state += __flash(hero)
        elif _adrenaline_state == 1:
            _adrenaline_state += __flash_down(hero)
        if clock.timer > only.adrenaline:
            only.adrenaline = None
            _adrenaline_state = 0
            only.crazy_points = 0
    else:
        _adrenaline_state = 0

    if only.healing != 0:
        if _healing_timer == 0:
            _healing_timer = clock.timer + HEAL_FRAME_SECONDS
        if clock.timer > _healing_timer:
            only.healingFrame += 1
            _healing_timer = 0
        if only.healingFrame == HEAL_FRAMES:
            only.healingFrame = 0
            only.healing = 0
            _healing_timer = 0
