"""FB object_etc.bas __logosta_console: the PASS> terminal prompt."""

from __future__ import annotations

from dataclasses import dataclass

import lynn.events as events

PROMPT = "PASS> "
PASSWORD = "FerUs686"
MAX_ENTRY = 10
CURSOR_RATE = 0.6


@dataclass
class ConsoleState:
    obj: object
    text: str = ""
    done: bool = False


def feed_key(con: ConsoleState, key_code: int, char: str) -> None:
    if con.done:
        return
    if key_code == 8:
        con.text = con.text[:-1]
    elif key_code == 13:
        con.done = True
    elif char and char.isprintable() and len(con.text) != MAX_ENTRY:
        con.text += char


def draw_console(canvas, now: float) -> None:
    from lynn.gfx.config_ui import gfxprint

    con = events.console
    if con is None or con.done:
        return
    cursor = "_" if int(now / CURSOR_RATE) % 2 == 0 else ""
    gfxprint(canvas, PROMPT + con.text + cursor, 0, 48, (255, 255, 255))
