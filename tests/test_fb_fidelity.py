"""FreeBASIC funcs the fidelity audit still had as stubs or missing."""

import lynn.object  # noqa: F401

from lynn import clock
from lynn.constants import LLFADE_GRAY, LLFADE_WHITE, TRUE
from lynn.events import bind_hero, bind_hero_only, reset_events
from lynn.gfx.box import BoxControl, blit_box, make_box
from lynn.gfx.palette import LLPalette
from lynn.hero import camera_target, ctor_hero_only, update_cam
from lynn.map.types import RoomType
from lynn.object.char import CharType, EFuncs
from lynn.object.dispatch import lookup_func
import lynn.events as events


def setup_function(_):
    reset_events()
    clock.timer = 10.0


def test_outfit_branch_uses_the_shop_price():
    hero = CharType()
    hero.money = 9
    bind_hero(hero)
    suit = CharType()
    suit.chap = 10
    assert lookup_func("__outfit_branch")(suit) == 1
    assert suit.sel_seq == 1
    hero.money = 10
    suit.sel_seq = 0
    lookup_func("__outfit_branch")(suit)
    assert suit.sel_seq == 0
    suit.sel_seq = 1
    hero.money = 100
    lookup_func("__outfit_branch")(suit)
    assert suit.sel_seq == 1


def test_give_costume_full_heal_and_melt():
    only = ctor_hero_only()
    bind_hero_only(only)
    lynn = CharType()
    lynn.chap = 3
    lookup_func("__give_costume")(lynn)
    assert only.hasCostume[3] == TRUE
    npc = CharType()
    npc.hp = 1
    npc.maxhp = 8
    lookup_func("__full_heal")(npc)
    assert npc.hp == 8
    bush = CharType()
    bush.melt = 1
    assert lookup_func("__melt")(bush) == 0
    assert bush.melt == 0


def test_set_func_moves_to_chap():
    actor = CharType()
    actor.funcs = EFuncs(
        active_state=0,
        states=2,
        func=[[lookup_func("__do_nothing")], [lookup_func("__do_nothing")]],
        current_func=[2, 3],
        func_count=[1, 1],
    )
    actor.chap = 1
    assert lookup_func("__set_func")(actor) == 1
    assert actor.funcs.active_state == 1
    assert actor.funcs.current_func[1] == 0


def test_fade_flags_stay_until_a_real_room_fade():
    only = ctor_hero_only()
    bind_hero_only(only)
    only.fadeStyle = 0
    lookup_func("__set_white_fade")(only)
    lookup_func("__set_gray_fade")(only)
    assert only.fadeStyle == (LLFADE_WHITE | LLFADE_GRAY)


def test_set_camera_follows_the_actor_until_it_leaves():
    room = RoomType(x=40, y=30)
    hero = CharType()
    hero.coords_x = 16
    hero.coords_y = 16
    dummy = CharType()
    dummy.coords_x = 400
    dummy.coords_y = 200
    assert camera_target(hero, [hero, dummy]) is hero
    lookup_func("__set_camera")(dummy)
    assert camera_target(hero, [hero, dummy]) is dummy
    assert update_cam(camera_target(hero, [hero, dummy]), room) != update_cam(hero, room)
    assert camera_target(hero, [hero]) is hero
    assert events.current_cam is None


def test_black_text_restores_palette_247():
    pal = LLPalette()
    pal.master = [(0, 0, 0)] * 256
    pal.colors = [(0, 0, 0)] * 256
    pal.master[247] = (161, 160, 164)
    pal.colors[247] = (4, 4, 4)
    events.palette = pal
    assert lookup_func("__black_text_on")(CharType()) == 1
    assert pal.colors[247] == (160, 160, 164)


def test_flash_down_gray_locks_on_the_seventeenth_call():
    pal = LLPalette()
    pal.master = [(0, 0, 0)] * 256
    pal.colors = [(0, 0, 0)] * 256
    pal.master[0] = (255, 0, 0)
    pal.colors[0] = (255, 0, 0)
    events.palette = pal
    gull = CharType()
    fn = lookup_func("__flash_down_gray")
    assert fn(gull) == 0
    assert pal.colors[0] == (255, 255, 255)
    for _ in range(15):
        assert fn(gull) == 0
    assert fn(gull) == 1
    # 6-bit average of (63, 0, 0) is 21. The lock shows that as 21<<2.
    assert pal.colors[0] == (84, 84, 84)
    assert gull.fade_count == 0
    assert pal.epoch > 0
    lookup_func("__color_on")(gull)
    assert pal.colors[0] == (255, 0, 0)


def test_box_lingers_for_three_hundredths_after_shutdown():
    box = BoxControl()
    make_box(box, "Hi")
    box.surf = object()
    box.state = 1
    box.jump_switch = 1
    from lynn.gfx import box as boxmod

    box.jump_switch = boxmod.box_kill_switch
    box.state = boxmod.TEXTBOX_CONFIRMATION
    clock.timer = 10.0
    from lynn.gfx.box import tick_box

    tick_box(box, 1)
    assert box.activated == 0
    assert box.hold_box == 10.03

    class _Surf:
        def __init__(self):
            self.blits = []

        def blit(self, surf, pos):
            self.blits.append(pos)

    canvas = _Surf()
    blit_box(canvas, box)
    assert canvas.blits == [(0, 0)]
    clock.timer = 10.04
    blit_box(canvas, box)
    assert box.hold_box == 0.0
    assert canvas.blits == [(0, 0)]


def test_invisible_box_does_not_linger():
    box = BoxControl()
    make_box(box, "Hi", invis=1)
    box.surf = object()
    box.activated = 0
    box.hold_box = clock.timer + 0.03

    class _Surf:
        def __init__(self):
            self.blits = []

        def blit(self, surf, pos):
            self.blits.append(pos)

    canvas = _Surf()
    blit_box(canvas, box)
    assert canvas.blits == []
