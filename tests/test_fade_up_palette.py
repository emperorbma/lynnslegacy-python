import lynn.events as events
from lynn import clock
from lynn.gfx.palette import LLPalette
from lynn.object.char import CharType
from lynn.object.seq_funcs import __color_off, __fade_up_to_color, __red_tint


def _pal() -> LLPalette:
    pal = LLPalette()
    pal.master = [(0, 0, 0)] * 256
    pal.colors = list(pal.master)
    pal.master[26] = (255, 20, 20)
    pal.colors[26] = (255, 20, 20)
    return pal


def _finish_fade(mode_fn) -> LLPalette:
    events.reset_events()
    pal = _pal()
    events.palette = pal
    this = CharType()
    this.fade_time = 0.01
    mode_fn(this)
    done = 0
    for _ in range(400):
        clock.timer += 0.05
        done = __fade_up_to_color(this)
        if done:
            break
    assert done == 1
    return pal


def test_baked_frame_keeps_index_zero_clear_and_the_palette_color():
    import pygame

    pygame.display.init()
    pygame.display.set_mode((32, 32))
    from lynn.gfx.image import LLSystem_FrameShell, LLSystem_ImageHeader, frame_surface

    header = LLSystem_ImageHeader(x=2, y=1, frames=1)
    header.frame = [LLSystem_FrameShell(pixels=bytes((0, 26)), width=2, height=1)]
    surf = frame_surface(header, 0, _pal())
    assert surf.get_at((0, 0))[3] == 0
    assert surf.get_at((1, 0))[:3] == (255, 20, 20)

    padded = LLSystem_ImageHeader(x=2, y=1, frames=1)
    padded.frame = [LLSystem_FrameShell(pixels=bytes((26,)), width=1, height=1)]
    wide = frame_surface(padded, 0, _pal())
    assert wide.get_at((0, 0))[:3] == (255, 20, 20)
    assert wide.get_at((1, 0))[3] == 0


def test_fade_up_midpoint_is_half_the_master_color():
    """FB Int() once. The extra /5 left slice 32 near black, so the card looked stuck."""
    pal = _pal()
    pal.write_fade_up(0, 0)
    assert pal.colors[26] == (0, 0, 0)
    pal.write_fade_up(32, 0)
    assert pal.colors[26] == (124, 8, 8)
    pal.write_fade_up(63, 0)
    assert pal.colors[26] == (248, 16, 16)


def test_fade_up_restores_after_color_off():
    events.reset_events()
    pal = _pal()
    events.palette = pal
    __color_off(CharType())
    assert pal.colors[26] == (0, 0, 0)
    pal = _finish_fade(__color_off)
    assert pal.colors[26] == (255, 20, 20)
    assert events.fade_black == 0


def test_fade_up_restores_after_red_tint():
    events.reset_events()
    pal = _pal()
    events.palette = pal
    __red_tint(CharType())
    assert pal.colors[26] == (0, 0, 20)
    pal = _finish_fade(__red_tint)
    assert pal.colors[26] == (255, 20, 20)
    assert events.fade_black == 0
