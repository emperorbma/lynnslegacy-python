"""FB data/controls.xml + config.bas scancodes. DOS set-1 codes, not SDL."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pygame

from lynn.constants import TRUE
from lynn.paths import project_root

CONTROLS_XML = "data/controls.xml"
LL_INI = "ll.ini"

# FreeBASIC fbgfx SC_* (set-1).
SC_ESCAPE = 1
SC_1 = 2
SC_2 = 3
SC_3 = 4
SC_4 = 5
SC_5 = 6
SC_6 = 7
SC_7 = 8
SC_8 = 9
SC_9 = 10
SC_0 = 11
SC_MINUS = 12
SC_EQUALS = 13
SC_BACKSPACE = 14
SC_TAB = 15
SC_Q = 16
SC_W = 17
SC_E = 18
SC_R = 19
SC_T = 20
SC_Y = 21
SC_U = 22
SC_I = 23
SC_O = 24
SC_P = 25
SC_LEFTBRACKET = 26
SC_RIGHTBRACKET = 27
SC_ENTER = 28
SC_CONTROL = 29
SC_A = 30
SC_S = 31
SC_D = 32
SC_F = 33
SC_G = 34
SC_H = 35
SC_J = 36
SC_K = 37
SC_L = 38
SC_SEMICOLON = 39
SC_QUOTE = 40
SC_TILDE = 41
SC_LSHIFT = 42
SC_BACKSLASH = 43
SC_Z = 44
SC_X = 45
SC_C = 46
SC_V = 47
SC_B = 48
SC_N = 49
SC_M = 50
SC_COMMA = 51
SC_PERIOD = 52
SC_SLASH = 53
SC_RSHIFT = 54
SC_MULTIPLY = 55
SC_ALT = 56
SC_SPACE = 57
SC_CAPSLOCK = 58
SC_F1 = 59
SC_F2 = 60
SC_F3 = 61
SC_F4 = 62
SC_F5 = 63
SC_F6 = 64
SC_F7 = 65
SC_F8 = 66
SC_F9 = 67
SC_F10 = 68
SC_NUMLOCK = 69
SC_SCROLLLOCK = 70
SC_HOME = 71
SC_UP = 72
SC_PAGEUP = 73
SC_LEFT = 75
SC_RIGHT = 77
SC_PLUS = 78
SC_END = 79
SC_DOWN = 80
SC_PAGEDOWN = 81
SC_INSERT = 82
SC_DELETE = 83
SC_F11 = 87
SC_F12 = 88

_RESERVED = frozenset({SC_ENTER, SC_ESCAPE, SC_PERIOD, SC_COMMA})

# config.bas return_code_string (short labels under each action).
_SC_NAME = {
    0: "null",
    SC_ESCAPE: "esc",
    SC_1: "1",
    SC_2: "2",
    SC_3: "3",
    SC_4: "4",
    SC_5: "5",
    SC_6: "6",
    SC_7: "7",
    SC_8: "8",
    SC_9: "9",
    SC_0: "0",
    SC_MINUS: "-",
    SC_EQUALS: "=",
    SC_BACKSPACE: "bs",
    SC_TAB: "tab",
    SC_Q: "q",
    SC_W: "w",
    SC_E: "e",
    SC_R: "r",
    SC_T: "t",
    SC_Y: "y",
    SC_U: "u",
    SC_I: "i",
    SC_O: "o",
    SC_P: "p",
    SC_LEFTBRACKET: "[",
    SC_RIGHTBRACKET: "]",
    SC_ENTER: "enter",
    SC_CONTROL: "ctrl",
    SC_A: "a",
    SC_S: "s",
    SC_D: "d",
    SC_F: "f",
    SC_G: "g",
    SC_H: "h",
    SC_J: "j",
    SC_K: "k",
    SC_L: "l",
    SC_SEMICOLON: ";",
    SC_QUOTE: "'",
    SC_TILDE: "~",
    SC_LSHIFT: "l shft",
    SC_BACKSLASH: "\\",
    SC_Z: "z",
    SC_X: "x",
    SC_C: "c",
    SC_V: "v",
    SC_B: "b",
    SC_N: "n",
    SC_M: "m",
    SC_COMMA: ",",
    SC_PERIOD: ".",
    SC_SLASH: "/",
    SC_RSHIFT: "r shft",
    SC_MULTIPLY: "*",
    SC_ALT: "alt",
    SC_SPACE: "space",
    SC_CAPSLOCK: "caps",
    SC_F1: "f1",
    SC_F2: "f2",
    SC_F3: "f3",
    SC_F4: "f4",
    SC_F5: "f5",
    SC_F6: "f6",
    SC_F7: "f7",
    SC_F8: "f8",
    SC_F9: "f9",
    SC_F10: "f10",
    SC_NUMLOCK: "num",
    SC_SCROLLLOCK: "scrl",
    SC_HOME: "home",
    SC_UP: "\x18",
    SC_PAGEUP: "pg up",
    SC_LEFT: "<-",
    SC_RIGHT: "->",
    SC_PLUS: "+",
    SC_END: "end",
    SC_DOWN: "\x19",
    SC_PAGEDOWN: "pg dn",
    SC_INSERT: "ins",
    SC_DELETE: "del",
    SC_F11: "f11",
    SC_F12: "f12",
}

# One FB scancode may match several pygame keys (L/R ctrl, alt, shift).
_SC_TO_PY: dict[int, tuple[int, ...]] = {
    SC_ESCAPE: (pygame.K_ESCAPE,),
    SC_1: (pygame.K_1,),
    SC_2: (pygame.K_2,),
    SC_3: (pygame.K_3,),
    SC_4: (pygame.K_4,),
    SC_5: (pygame.K_5,),
    SC_6: (pygame.K_6,),
    SC_7: (pygame.K_7,),
    SC_8: (pygame.K_8,),
    SC_9: (pygame.K_9,),
    SC_0: (pygame.K_0,),
    SC_MINUS: (pygame.K_MINUS,),
    SC_EQUALS: (pygame.K_EQUALS,),
    SC_BACKSPACE: (pygame.K_BACKSPACE,),
    SC_TAB: (pygame.K_TAB,),
    SC_Q: (pygame.K_q,),
    SC_W: (pygame.K_w,),
    SC_E: (pygame.K_e,),
    SC_R: (pygame.K_r,),
    SC_T: (pygame.K_t,),
    SC_Y: (pygame.K_y,),
    SC_U: (pygame.K_u,),
    SC_I: (pygame.K_i,),
    SC_O: (pygame.K_o,),
    SC_P: (pygame.K_p,),
    SC_LEFTBRACKET: (pygame.K_LEFTBRACKET,),
    SC_RIGHTBRACKET: (pygame.K_RIGHTBRACKET,),
    SC_ENTER: (pygame.K_RETURN, pygame.K_KP_ENTER),
    SC_CONTROL: (pygame.K_LCTRL, pygame.K_RCTRL),
    SC_A: (pygame.K_a,),
    SC_S: (pygame.K_s,),
    SC_D: (pygame.K_d,),
    SC_F: (pygame.K_f,),
    SC_G: (pygame.K_g,),
    SC_H: (pygame.K_h,),
    SC_J: (pygame.K_j,),
    SC_K: (pygame.K_k,),
    SC_L: (pygame.K_l,),
    SC_SEMICOLON: (pygame.K_SEMICOLON,),
    SC_QUOTE: (pygame.K_QUOTE,),
    SC_TILDE: (pygame.K_BACKQUOTE,),
    SC_LSHIFT: (pygame.K_LSHIFT,),
    SC_BACKSLASH: (pygame.K_BACKSLASH,),
    SC_Z: (pygame.K_z,),
    SC_X: (pygame.K_x,),
    SC_C: (pygame.K_c,),
    SC_V: (pygame.K_v,),
    SC_B: (pygame.K_b,),
    SC_N: (pygame.K_n,),
    SC_M: (pygame.K_m,),
    SC_COMMA: (pygame.K_COMMA,),
    SC_PERIOD: (pygame.K_PERIOD,),
    SC_SLASH: (pygame.K_SLASH,),
    SC_RSHIFT: (pygame.K_RSHIFT,),
    SC_MULTIPLY: (pygame.K_KP_MULTIPLY,),
    SC_ALT: (pygame.K_LALT, pygame.K_RALT),
    SC_SPACE: (pygame.K_SPACE,),
    SC_CAPSLOCK: (pygame.K_CAPSLOCK,),
    SC_F1: (pygame.K_F1,),
    SC_F2: (pygame.K_F2,),
    SC_F3: (pygame.K_F3,),
    SC_F4: (pygame.K_F4,),
    SC_F5: (pygame.K_F5,),
    SC_F6: (pygame.K_F6,),
    SC_F7: (pygame.K_F7,),
    SC_F8: (pygame.K_F8,),
    SC_F9: (pygame.K_F9,),
    SC_F10: (pygame.K_F10,),
    SC_NUMLOCK: (pygame.K_NUMLOCK,),
    SC_SCROLLLOCK: (pygame.K_SCROLLLOCK,),
    SC_HOME: (pygame.K_HOME,),
    SC_UP: (pygame.K_UP,),
    SC_PAGEUP: (pygame.K_PAGEUP,),
    SC_LEFT: (pygame.K_LEFT,),
    SC_RIGHT: (pygame.K_RIGHT,),
    SC_PLUS: (pygame.K_KP_PLUS,),
    SC_END: (pygame.K_END,),
    SC_DOWN: (pygame.K_DOWN,),
    SC_PAGEDOWN: (pygame.K_PAGEDOWN,),
    SC_INSERT: (pygame.K_INSERT,),
    SC_DELETE: (pygame.K_DELETE,),
    SC_F11: (pygame.K_F11,),
    SC_F12: (pygame.K_F12,),
}

_PY_TO_SC: dict[int, int] = {}
for _sc, _keys in _SC_TO_PY.items():
    for _k in _keys:
        _PY_TO_SC[_k] = _sc


@dataclass
class KeyChart:
    """FB config.bas key_config + extra XML tags the engine keeps."""

    ukey: int = SC_W
    rkey: int = SC_D
    dkey: int = SC_S
    lkey: int = SC_A
    atkkey: int = SC_CONTROL
    actkey: int = SC_SPACE
    itmkey: int = SC_ALT
    item_up: int = SC_END
    item_down: int = SC_DELETE
    menu: int = SC_ESCAPE


chart = KeyChart()


def scancode_name(code: int) -> str:
    return _SC_NAME.get(int(code), "")


def pygame_keys_for(scancode: int) -> tuple[int, ...]:
    return _SC_TO_PY.get(int(scancode), ())


def scancode_from_pygame(key: int) -> int:
    return _PY_TO_SC.get(int(key), 0)


def scancode_held(pressed, scancode: int) -> int:
    for key in pygame_keys_for(scancode):
        if 0 <= key < len(pressed) and pressed[key]:
            return TRUE
    return 0


def check_all_codes(code: int, bound: KeyChart) -> int:
    """FB check_all_codes: TRUE if the scancode may be bound."""
    if int(code) in _RESERVED:
        return 0
    for cur in (bound.ukey, bound.rkey, bound.dkey, bound.lkey, bound.atkkey, bound.actkey, bound.itmkey):
        if int(code) == int(cur):
            return 0
    return TRUE


def _controls_path() -> Path:
    return project_root() / CONTROLS_XML


def _ini_path() -> Path:
    return project_root() / LL_INI


def _tag(root: ET.Element, name: str, default: int) -> int:
    el = root.find(name)
    if el is None or el.text is None:
        return default
    try:
        return int(el.text.strip())
    except ValueError:
        return default


def load_controls(path: Path | None = None) -> KeyChart:
    """FB engine_init xml_Load of data/controls.xml."""
    global chart
    dest = path or _controls_path()
    loaded = KeyChart()
    if dest.is_file():
        try:
            root = ET.fromstring(dest.read_text(encoding="latin-1"))
            loaded.actkey = _tag(root, "action", loaded.actkey)
            loaded.atkkey = _tag(root, "attack", loaded.atkkey)
            loaded.itmkey = _tag(root, "item", loaded.itmkey)
            loaded.ukey = _tag(root, "move_up", loaded.ukey)
            loaded.rkey = _tag(root, "move_right", loaded.rkey)
            loaded.dkey = _tag(root, "move_down", loaded.dkey)
            loaded.lkey = _tag(root, "move_left", loaded.lkey)
            loaded.item_down = _tag(root, "item_down", loaded.item_down)
            loaded.item_up = _tag(root, "item_up", loaded.item_up)
            loaded.menu = _tag(root, "menu", loaded.menu)
        except ET.ParseError:
            loaded = KeyChart()
    if path is None:
        chart = loaded
    return loaded


def save_controls(bound: KeyChart, path: Path | None = None) -> None:
    dest = path or _controls_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "",
        "<key_map>",
        "",
        f"  <action> {int(bound.actkey)} </action>",
        f"  <attack> {int(bound.atkkey)} </attack>",
        f"  <item> {int(bound.itmkey)} </item>",
        f"  <move_up> {int(bound.ukey)} </move_up>",
        f"  <move_right> {int(bound.rkey)} </move_right>",
        f"  <move_down> {int(bound.dkey)} </move_down>",
        f"  <move_left> {int(bound.lkey)} </move_left>",
        f"  <item_down> {int(bound.item_down)} </item_down>",
        f"  <item_up> {int(bound.item_up)} </item_up>",
        f"  <menu> {int(bound.menu)} </menu>",
        "",
        "</key_map>",
        "",
    ]
    dest.write_text("\n".join(lines), encoding="latin-1")


def load_fullscreen(path: Path | None = None) -> int:
    """FB isFullscreen: ll.ini contains FULLSCREEN and YES."""
    dest = path or _ini_path()
    if not dest.is_file():
        return 0
    try:
        text = dest.read_text(encoding="latin-1")
    except OSError:
        return 0
    upper = text.upper()
    if "FULLSCREEN" in upper and "YES" in upper:
        return 1
    return 0


def save_fullscreen(enabled: int, path: Path | None = None) -> None:
    dest = path or _ini_path()
    dest.write_text(f"Fullscreen = {'Yes' if enabled != 0 else 'No'}\n", encoding="latin-1")
