import lynn.events as events
from lynn import clock
from lynn.object.char import CharType
from lynn.object.seq_funcs import __color_off, __fade_up_to_color, __red_tint


def _fade_up(mode_fn):
    events.reset_events()
    this = CharType()
    mode_fn(this)
    assert events.color_mode != 0
    for _ in range(400):
        clock.timer += 0.05
        if __fade_up_to_color(this):
            break
    return this


def test_fade_up_restores_after_color_off():
    _fade_up(__color_off)
    assert events.color_mode == 0
    assert events.fade_black == 0


def test_fade_up_restores_after_red_tint():
    _fade_up(__red_tint)
    assert events.color_mode == 0
    assert events.fade_black == 0
