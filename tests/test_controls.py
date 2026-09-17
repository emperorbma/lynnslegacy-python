"""controls.xml scancodes and ll.ini fullscreen."""

import pygame

from lynn.controls import (
    SC_ALT,
    SC_COMMA,
    SC_CONTROL,
    SC_DOWN,
    SC_ENTER,
    SC_ESCAPE,
    SC_LEFT,
    SC_PERIOD,
    SC_RIGHT,
    SC_SPACE,
    SC_UP,
    SC_W,
    KeyChart,
    check_all_codes,
    load_controls,
    load_fullscreen,
    pygame_keys_for,
    pygame_scans_for,
    save_controls,
    save_fullscreen,
    scancode_from_pygame,
    scancode_held,
    scancode_name,
)
from lynn.main import parse_cli
from lynn.paths import project_root


def test_shipped_controls_xml_is_arrow_keys():
    chart = load_controls(project_root() / "data" / "controls.xml")
    assert chart.ukey == SC_UP
    assert chart.rkey == SC_RIGHT
    assert chart.dkey == SC_DOWN
    assert chart.lkey == SC_LEFT
    assert chart.atkkey == SC_CONTROL
    assert chart.actkey == SC_SPACE
    assert chart.itmkey == SC_ALT
    assert chart.menu == SC_ESCAPE
    assert pygame_keys_for(chart.ukey) == (pygame.K_UP,)
    assert pygame_keys_for(chart.rkey) == (pygame.K_RIGHT,)
    assert pygame_keys_for(chart.dkey) == (pygame.K_DOWN,)
    assert pygame_keys_for(chart.lkey) == (pygame.K_LEFT,)
    assert pygame_scans_for(chart.ukey) == (pygame.KSCAN_UP,)
    assert pygame_scans_for(chart.rkey) == (pygame.KSCAN_RIGHT,)
    assert pygame_scans_for(chart.dkey) == (pygame.KSCAN_DOWN,)
    assert pygame_scans_for(chart.lkey) == (pygame.KSCAN_LEFT,)
    assert scancode_from_pygame(pygame.K_UP) == SC_UP
    assert scancode_from_pygame(pygame.K_LEFT) == SC_LEFT
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    pygame.display.set_mode((32, 32))
    pressed = pygame.key.get_pressed()
    assert len(pressed) == 512
    assert pygame.K_UP >= len(pressed)
    assert pygame.KSCAN_UP < len(pressed)
    class _Pressed:
        def __init__(self, held):
            self._held = set(held)

        def __len__(self):
            return 512

        def __getitem__(self, key):
            return key in self._held

    held = _Pressed({pygame.KSCAN_UP, pygame.KSCAN_RIGHT})
    assert scancode_held(held, chart.ukey) != 0
    assert scancode_held(held, chart.rkey) != 0
    assert scancode_held(held, chart.dkey) == 0
    assert scancode_held(held, chart.lkey) == 0


def test_scancode_roundtrip_pygame():
    assert scancode_from_pygame(pygame.K_w) == SC_W
    assert scancode_from_pygame(pygame.K_SPACE) == SC_SPACE
    assert scancode_from_pygame(pygame.K_LCTRL) == SC_CONTROL
    assert scancode_from_pygame(pygame.K_RCTRL) == SC_CONTROL
    assert scancode_name(SC_SPACE) == "space"
    assert scancode_name(SC_CONTROL) == "ctrl"


def test_check_all_codes_rejects_reserved_and_duplicates():
    bound = KeyChart()
    assert check_all_codes(SC_ENTER, bound) == 0
    assert check_all_codes(SC_ESCAPE, bound) == 0
    assert check_all_codes(SC_PERIOD, bound) == 0
    assert check_all_codes(bound.ukey, bound) == 0
    assert check_all_codes(SC_W, bound) != 0  # WASD free under default arrows
    assert check_all_codes(SC_UP, bound) == 0


def test_save_and_load_controls_roundtrip(tmp_path):
    path = tmp_path / "controls.xml"
    bound = KeyChart(ukey=72, rkey=77, dkey=80, lkey=75, atkkey=29, actkey=57, itmkey=56)
    save_controls(bound, path)
    text = path.read_text(encoding="latin-1")
    assert "<move_up> 72 </move_up>" in text
    assert "<menu>" in text
    loaded = load_controls(path)
    assert loaded.ukey == 72
    assert loaded.rkey == 77
    assert loaded.actkey == 57


def test_missing_ll_ini_is_windowed(tmp_path):
    assert load_fullscreen(tmp_path / "no-such.ini") == 0


def test_fullscreen_ini_roundtrip(tmp_path):
    path = tmp_path / "ll.ini"
    save_fullscreen(0, path)
    assert load_fullscreen(path) == 0
    save_fullscreen(-1, path)
    assert load_fullscreen(path) != 0
    assert "YES" in path.read_text(encoding="latin-1").upper()


def test_parse_cli_config_mode():
    assert parse_cli(["config"]) == ("config", None, [], None)


def test_config_uses_pygame_fonts():
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    from lynn.gfx.config_ui import _ensure_fonts, draw_string, gfxprint

    pygame.init()
    pygame.display.set_mode((320, 200))
    _ensure_fonts()
    from lynn.gfx import config_ui

    assert config_ui._FONT8 is not None
    assert config_ui._FONT16 is not None
    assert config_ui._FONT8.get_height() <= 10
    assert config_ui._FONT16.get_height() <= 16
    canvas = pygame.Surface((320, 200))
    canvas.fill((0, 0, 0))
    draw_string(canvas, "Lynn's Legacy", 106, 8)
    gfxprint(canvas, "Full", 240, 10, (48, 101, 92))
    gfxprint(canvas, "Windowed", 240, 30, (252, 252, 252))
    title_ink = any(canvas.get_at((106 + x, 10))[:3] != (0, 0, 0) for x in range(40))
    full_ink = any(
        canvas.get_at((x, y))[:3] == (48, 101, 92)
        for y in range(10, 24)
        for x in range(240, 272)
    )
    assert title_ink
    assert full_ink
    pygame.quit()
