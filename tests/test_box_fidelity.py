import pygame

from lynn import clock
from lynn.gfx import box as boxmod
from lynn.gfx.box import BoxControl, blit_box, make_box, tick_box
from lynn.gfx.menu import font_state, reset_font_colors


class _Surf:
    def __init__(self):
        self.blits = []

    def blit(self, s, pos):
        self.blits.append(pos)


def setup_function(_):
    reset_font_colors()


def test_invis_skips_background_and_arrow():
    b = BoxControl()
    make_box(b, "Hi", invis=1)
    b.surf = pygame.Surface((4, 4))
    c = _Surf()
    blit_box(c, b)
    assert (0, 0) not in c.blits


def test_visible_box_blits_background_at_offset():
    b = BoxControl()
    make_box(b, "Hi", y=16)
    b.surf = pygame.Surface((4, 4))
    c = _Surf()
    blit_box(c, b)
    assert c.blits[0] == (0, 16)


def test_color_applied_then_restored_on_shutdown():
    b = BoxControl()
    make_box(b, "Hi", color=92)
    assert font_state["fg"] == 92
    b.state = boxmod.TEXTBOX_CONFIRMATION
    b.jump_switch = boxmod.box_kill_switch
    tick_box(b, 1)
    assert font_state["fg"] == 15


def test_auto_dismiss():
    b = BoxControl()
    make_box(b, "Hi", auto=1.0)
    b.state = boxmod.TEXTBOX_CONFIRMATION
    b.jump_switch = boxmod.box_kill_switch
    tick_box(b, 0)
    assert b.activated
    clock.timer += 2.0
    tick_box(b, 0)
    assert not b.activated
