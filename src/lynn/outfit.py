"""FB engine--LL.bas set_regular / set_cougar / set_lynnity / set_ninja / set_bikini / set_rknight."""

from __future__ import annotations

from lynn import clock
from lynn.audio import (
    play_sample,
    sound_flare,
    sound_healthgrab,
    sound_ice,
    sound_mace_0,
    sound_mace_1,
    sound_mace_2,
)
from lynn.object.char import CharType
from lynn.object.xml_load import get_image_header

# slot, path, anim rate
_Piece = tuple[int, str, float]
# slot, sound, volume or None (leave the frame volume alone)
_Sound = tuple[int, int, int | None]

_REGULAR: tuple[_Piece, ...] = (
    (0, "data/pictures/char/lynn24.spr", 0.08),
    (3, "data/pictures/char/lynnattack_new.spr", 0.07),
    (4, "data/pictures/char/lynnattack_2.spr", 0.1),
    (5, "data/pictures/char/lynnattack_3.spr", 0.13),
    (6, "data/pictures/char/lynn_flare.spr", 0.07),
    (7, "data/pictures/char/lynn_ice.spr", 0.07),
    (8, "data/pictures/char/lynnfall.spr", 0.18),
    (12, "data/pictures/char/lynngetup.spr", 0.18),
)
_COUGAR: tuple[_Piece, ...] = (
    (0, "data/pictures/char/outfits/cougar/walk.spr", 0.05),
    (6, "data/pictures/char/outfits/cougar/flare.spr", 0.07),
    (7, "data/pictures/char/outfits/cougar/ice.spr", 0.07),
    (8, "data/pictures/char/outfits/cougar/die.spr", 0.18),
    (12, "data/pictures/char/outfits/cougar/getup.spr", 0.18),
)
_LYNNITY: tuple[_Piece, ...] = (
    (0, "data/pictures/char/outfits/lynnity/walk.spr", 0.08),
    (3, "data/pictures/char/outfits/lynnity/attack_1.spr", 0.07),
    (4, "data/pictures/char/outfits/lynnity/attack_2.spr", 0.1),
    (5, "data/pictures/char/outfits/lynnity/attack_3.spr", 0.13),
    (6, "data/pictures/char/outfits/lynnity/flare.spr", 0.07),
    (7, "data/pictures/char/outfits/lynnity/ice.spr", 0.07),
    (8, "data/pictures/char/outfits/lynnity/die.spr", 0.18),
    (12, "data/pictures/char/outfits/lynnity/getup.spr", 0.18),
)
_NINJA: tuple[_Piece, ...] = (
    (0, "data/pictures/char/outfits/ninja/walk.spr", 0.08),
    (3, "data/pictures/char/outfits/ninja/attack_1.spr", 0.04),
    (4, "data/pictures/char/outfits/ninja/attack_2.spr", 0.07),
    (5, "data/pictures/char/outfits/ninja/attack_3.spr", 0.1),
    (6, "data/pictures/char/outfits/ninja/flare.spr", 0.07),
    (7, "data/pictures/char/outfits/ninja/ice.spr", 0.07),
    (8, "data/pictures/char/outfits/ninja/die.spr", 0.18),
    (12, "data/pictures/char/outfits/ninja/getup.spr", 0.18),
)
_BIKINI: tuple[_Piece, ...] = (
    (0, "data/pictures/char/outfits/swimsuit/walk.spr", 0.08),
    (3, "data/pictures/char/outfits/swimsuit/attack_1.spr", 0.07),
    (4, "data/pictures/char/outfits/swimsuit/attack_2.spr", 0.1),
    (5, "data/pictures/char/outfits/swimsuit/attack_3.spr", 0.13),
    (6, "data/pictures/char/outfits/swimsuit/flare.spr", 0.07),
    (7, "data/pictures/char/outfits/swimsuit/ice.spr", 0.07),
    (8, "data/pictures/char/outfits/swimsuit/die.spr", 0.18),
    (12, "data/pictures/char/outfits/swimsuit/getup.spr", 0.18),
)
_RKNIGHT: tuple[_Piece, ...] = (
    (0, "data/pictures/char/outfits/redknight/walk.spr", 0.12),
    (6, "data/pictures/char/outfits/redknight/flare.spr", 0.07),
    (7, "data/pictures/char/outfits/redknight/ice.spr", 0.07),
    (8, "data/pictures/char/outfits/redknight/die.spr", 0.18),
    (12, "data/pictures/char/outfits/redknight/getup.spr", 0.18),
)

_ATTACK_VOL: tuple[_Sound, ...] = (
    (3, sound_mace_0, 50),
    (4, sound_mace_1, 50),
    (5, sound_mace_2, 50),
    (6, sound_flare, None),
    (7, sound_ice, None),
)
_ITEM_SOUND: tuple[_Sound, ...] = (
    (6, sound_flare, None),
    (7, sound_ice, None),
)

_BY_WEAR = {
    0: (_REGULAR, _ATTACK_VOL),
    1: (_COUGAR, _ITEM_SOUND),
    2: (_LYNNITY, _ATTACK_VOL),
    3: (_NINJA, _ATTACK_VOL),
    4: (_BIKINI, _ATTACK_VOL),
    5: (_RKNIGHT, _ITEM_SOUND + ((3, 0, 50), (4, 0, 50), (5, 0, 50))),
}

# FB __outfit_swap static. 0 shows the regular sprite, 1 restores isWearing.
_swap_state = 0


def _uni_sound(hero: CharType, slot: int, sound: int, vol: int | None) -> None:
    """FB hUniSound / hUniVol: frame 0 of each of the four directions."""
    if slot >= len(hero.anim) or slot >= len(hero.animControl):
        return
    anim = hero.anim[slot]
    if not anim.frame:
        return
    stride = int(hero.animControl[slot].dir_frames or 0)
    crawl = 0
    for _ in range(4):
        if 0 <= crawl < len(anim.frame):
            if sound:
                anim.frame[crawl].sound = sound
            if vol is not None:
                anim.frame[crawl].vol = vol
        if stride <= 0:
            break
        crawl += stride


def apply_outfit(hero: CharType | None, wearing: int) -> None:
    """Swap Lynn's anim slots for this costume. Does not change isWearing."""
    spec = _BY_WEAR.get(int(wearing))
    if hero is None or spec is None or not hero.anim or not hero.animControl:
        return
    pieces, sounds = spec
    for slot, path, rate in pieces:
        if slot >= len(hero.anim) or slot >= len(hero.animControl):
            continue
        hero.anim[slot] = get_image_header(path)
        hero.animControl[slot].rate = rate
    for slot, sound, vol in sounds:
        _uni_sound(hero, slot, sound, vol)


def tick_hero_outfit(hero: CharType, only) -> None:
    """FB hero_main: cougar is fast, the red knight is slow and regens."""
    wear = int(only.isWearing)
    if wear == 1:
        hero.walk_speed = 0.003
    elif wear == 5:
        hero.walk_speed = 0.02
    else:
        hero.walk_speed = 0.009
    if wear == 5:
        if only.healTimer == 0:
            only.healTimer = clock.timer + 6
        if clock.timer > only.healTimer:
            if hero.hp < hero.maxhp:
                hero.hp += 1
                play_sample(sound_healthgrab)
            only.healTimer = 0
    else:
        only.healTimer = 0


def outfit_swap_toggle(hero: CharType | None, wearing: int) -> None:
    """FB __outfit_swap: regular sprite, then the worn costume, alternating."""
    global _swap_state
    if _swap_state == 0:
        apply_outfit(hero, 0)
    else:
        apply_outfit(hero, wearing)
    _swap_state ^= 1
