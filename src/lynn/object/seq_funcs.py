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


def __do_nothing(this: CharType) -> int:
    return 1


def __end(this: CharType) -> int:
    events.request_quit = TRUE
    return 0


def __do_menu(this: CharType) -> int:
    """FB object_etc.bas: title Begin / Continue / Quit."""
    hero = events.hero
    events.box_entity = this
    if this.menu_lock != 0:
        if events.keys.enter == 0:
            if this.menu_sel == 0:
                if hero is not None:
                    hero.menu_sel = 0
                this.return_trig = 1
                return 0
            if this.menu_sel == 1:
                if hero is not None:
                    hero.menu_sel = 2
                this.menu_sel = 0
                this.state_shift = 2
                this.menu_lock = 0
                return 0
            this.menu_lock = 0
    if hero is not None:
        hero.menu_sel = 1
    if events.keys.right != 0:
        if this.walk_hold == 0:
            this.menu_sel += 1
            if this.menu_sel == 3:
                this.menu_sel = 0
            this.walk_hold = clock.timer + (this.walk_speed or 1)
    elif events.keys.left != 0:
        if this.walk_hold == 0:
            this.menu_sel -= 1
            if this.menu_sel == -1:
                this.menu_sel = 2
            this.walk_hold = clock.timer + (this.walk_speed or 1)
    else:
        this.walk_hold = 0
    if clock.timer >= this.walk_hold:
        this.walk_hold = 0
    if events.keys.escape != 0:
        events.request_quit = TRUE
        return 0
    if events.keys.enter != 0:
        if this.menu_sel == 2:
            events.request_quit = TRUE
            return 0
        this.menu_lock = 1
    return 0


def __do_menu_continue(this: CharType) -> int:
    """FB object_etc.bas: title file slots. Enter on an occupied slot loads."""
    hero = events.hero
    only = events.hero_only
    if hero is not None:
        hero.menu_sel = 2
    events.box_entity = this
    if this.menu_lock != 0:
        if events.keys.escape == 0:
            this.menu_lock = 0
            this.menu_sel = 0
            this.read_lock = 0
            this.state_shift = 1
            if hero is not None:
                hero.menu_sel = 1
            return 0
    if this.read_lock == 0:
        from lynn.object.save import LLSystem_ReadSaveFile

        this.save = [
            LLSystem_ReadSaveFile("ll_save1.sav"),
            LLSystem_ReadSaveFile("ll_save2.sav"),
            LLSystem_ReadSaveFile("ll_save3.sav"),
            LLSystem_ReadSaveFile("ll_save4.sav"),
        ]
        this.read_lock = TRUE
    if events.keys.down != 0:
        if this.walk_hold == 0:
            this.menu_sel += 1
            if this.menu_sel == 4:
                this.menu_sel = 0
            this.walk_hold = clock.timer + (this.walk_speed or 1)
    elif events.keys.up != 0:
        if this.walk_hold == 0:
            this.menu_sel -= 1
            if this.menu_sel == -1:
                this.menu_sel = 3
            this.walk_hold = clock.timer + (this.walk_speed or 1)
    else:
        this.walk_hold = 0
    if clock.timer >= this.walk_hold:
        this.walk_hold = 0
    if events.keys.enter_pulse != 0:
        if 0 <= this.menu_sel < len(this.save) and this.save[this.menu_sel] is not None:
            if only is not None:
                only.isLoading = TRUE
    if events.keys.escape != 0:
        this.menu_lock = 1
    return 0


def health_formula(maxhp: int) -> int:
    """FB healthFormula: 50 + (maxhp - 6) * 5."""
    return 50 + (int(maxhp) - 6) * 5


def __healthguy_branch(this: CharType) -> int:
    hero = events.hero
    if hero is None:
        return 1
    if hero.money < health_formula(hero.maxhp):
        this.sel_seq = 2
    if hero.maxhp == 30:
        this.sel_seq = 1
    return 1


def __buy_health(this: CharType) -> int:
    hero = events.hero
    if hero is None:
        return 1
    hero.money -= health_formula(hero.maxhp)
    if hero.money < 0:
        hero.money = 0
    hero.maxhp += 1
    return 1


def __translate_result(this: CharType) -> int:
    from lynn.sequence import sequence_FullReset

    seq = events.current_seq
    box = events.seq_box
    only = events.hero_only
    if seq is not None and only is not None:
        sequence_FullReset(seq, only)
    sel = box.selected if box is not None else 0
    idx = int(this.dest_x if sel == 0 else this.dest_y)
    this.dest_x = 0
    this.dest_y = 0
    if 0 <= idx < len(this.seq):
        nxt = this.seq[idx]
        nxt.current_command = 0
        for cmd in nxt.Command:
            for ent in cmd.ent:
                ent.ent_func = 0
        events.pending_seq = nxt
    if only is not None:
        only.dropoutSequence = TRUE
    return 0


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


def __dir_up(this: CharType) -> int:
    this.direction = 0
    return 1


def __dir_right(this: CharType) -> int:
    this.direction = 1
    return 1


def __dir_down(this: CharType) -> int:
    this.direction = 2
    return 1


def __dir_left(this: CharType) -> int:
    this.direction = 3
    return 1


def __inc_sel_seq(this: CharType) -> int:
    this.sel_seq += 1
    return 1


def __dec_sel_seq(this: CharType) -> int:
    this.sel_seq -= 1
    return 1


def __give_100_gold(this: CharType) -> int:
    hero = events.hero
    if hero is not None:
        hero.money += 100
    return 1


def __give_outfit(this: CharType) -> int:
    only = events.hero_only
    hero = events.hero
    chap = int(this.chap)
    if only is not None and 0 <= chap < len(only.hasCostume):
        only.hasCostume[chap] = TRUE
    if hero is not None:
        prices = {1: 10, 2: 35, 4: 70, 5: 50}
        hero.money -= prices.get(chap, 0)
    return 1


def __set_camera(this: CharType) -> int:
    return 1


def __invis_entry(this: CharType) -> int:
    only = events.hero_only
    if only is not None:
        only.invisibleEntry = TRUE
    return 1


def __black_text_on(this: CharType) -> int:
    return 1


def __fade_off(this: CharType) -> int:
    return 1


def __kill_song(this: CharType) -> int:
    from lynn.audio import LLMusic_Stop

    LLMusic_Stop()
    return 1


def __stop_sound(this: CharType) -> int:
    return 1


def __fade_music_out(this: CharType) -> int:
    """FB object_etc.bas: 4s / 64 slices, ticked by LLMusic_Fade."""
    from lynn.audio import SongFadingType

    only = events.hero_only
    if only is not None:
        only.songFade = SongFadingType(pulseLength=4 / 64)
    return 1


def __chapter_1_on(this: CharType) -> int:
    """FB object_modification.bas: hide the room and show hero.anim[hero.chap]."""
    events.do_chap = 1
    return 1


def __chapter_1_off(this: CharType) -> int:
    events.do_chap = 0
    return 1


def __color_on(this: CharType) -> int:
    return 1


def __color_off(this: CharType) -> int:
    return 1


def __flash(this: CharType) -> int:
    """FB object--gfx_palette.bas: white palette hold ~0.125s."""
    if this.pause == 0:
        this.pause = clock.timer + 0.125
        return 0
    if clock.timer > this.pause:
        this.pause = 0
        return 1
    return 0


def __flash_down(this: CharType) -> int:
    return 1


def __flash_down_gray(this: CharType) -> int:
    return 1


def __play_song(this: CharType) -> int:
    """FB object_sound.bas: LLMusic_Start(music_strings(this.chap))."""
    from lynn.audio import LLMusic_StartIndex

    LLMusic_StartIndex(int(this.chap))
    return 1


def __play_sound(this: CharType) -> int:
    return 1


def __set_fade(this: CharType) -> int:
    return 1


def __set_vol_fade(this: CharType) -> int:
    return 1


def __set_white_fade(this: CharType) -> int:
    return 1


def __set_gray_fade(this: CharType) -> int:
    return 1


def __flicker(this: CharType) -> int:
    return 1


def __change_map(this: CharType) -> int:
    """FB object_etc.bas: start a map-change tele from this.chap, drop the seq."""
    only = events.hero_only
    hero = events.hero
    if only is not None:
        only.dropoutSequence = TRUE
    if hero is not None:
        hero.switch_room = int(this.chap)
        room = events.current_room
        if room is not None and 0 <= hero.switch_room < len(room.teleport):
            tele = room.teleport[hero.switch_room]
            hero.to_map = tele.to_map
            hero.to_entry = tele.to_room
    return 1


def __after_slime(this: CharType) -> int:
    if events.now[1150] != 0:
        this.sel_seq = 3
        return 1
    return 0


def __fade_up_to_color(this: CharType) -> int:
    """FB palette restore after fade-to-black. Black overlay stands in for palette."""
    if this.fade_timer == 0:
        events.fade_black = max(0, int(events.fade_black) - 4)
        events.fade_white = 0
        this.fade_count += 1
        this.fade_timer = clock.timer + (this.fade_time or 0.01)
    if clock.timer >= this.fade_timer:
        this.fade_timer = 0
    if this.fade_count >= 64 or events.fade_black <= 0:
        events.fade_black = 0
        this.fade_count = 0
        this.fade_timer = 0
        return 1
    return 0


def __eat_lynn_action(this: CharType) -> int:
    if events.hero_only is not None:
        events.hero_only.action = 0
    return 1


def __fade_to_white(this: CharType) -> int:
    """FB object--gfx_palette.bas: wash toward white. Overlay stands in for palette."""
    step = 4
    if this.fade_timer == 0:
        events.fade_white = min(255, int(events.fade_white) + step)
        this.fade_timer = clock.timer + (this.fade_time or 0.01)
    if clock.timer >= this.fade_timer:
        this.fade_timer = 0
    if events.fade_white >= 250:
        events.fade_white = 255
        this.fade_timer = 0
        return 1
    return 0


def __fade_down_to_color(this: CharType) -> int:
    """FB: 64 steps from white back to the room palette."""
    if this.fade_timer == 0:
        events.fade_white = max(0, int(events.fade_white) - 4)
        this.fade_count += 1
        this.fade_timer = clock.timer + (this.fade_time or 0.01)
    if clock.timer >= this.fade_timer:
        this.fade_timer = 0
    if this.fade_count >= 64 or events.fade_white <= 0:
        events.fade_white = 0
        this.fade_count = 0
        this.fade_timer = 0
        return 1
    return 0


def __fade_to_red(this: CharType) -> int:
    return 1


def __fade_to_black(this: CharType) -> int:
    """FB palette darken. Black overlay stands in for palette steps of 4."""
    if this.fade_timer == 0:
        events.fade_black = min(255, int(events.fade_black) + 4)
        this.fade_timer = clock.timer + (this.fade_time or 0.01)
    if clock.timer >= this.fade_timer:
        this.fade_timer = 0
    if events.fade_black >= 250:
        events.fade_black = 255
        this.fade_timer = 0
        return 1
    return 0


for _name, _fn in list(globals().items()):
    if _name.startswith("__") and callable(_fn) and _name != "__active_animate":
        register_func(_name, _fn)

for _n in range(16):
    register_func(f"__active_anim_{_n}", _make_active_anim(_n))
