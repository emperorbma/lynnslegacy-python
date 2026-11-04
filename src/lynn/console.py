"""FB object_etc.bas __logosta_console: shared line-entry terminal.

Logosta uses PASS> / FerUs686. Godmode reuses the same feed_key + draw path
with a custom prompt, optional digit filter, and submit/cancel hooks.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import lynn.events as events

PROMPT = "PASS> "
PASSWORD = "FerUs686"
MAX_ENTRY = 10
CURSOR_RATE = 0.6


@dataclass
class ConsoleState:
    obj: object = None
    text: str = ""
    done: bool = False
    cancelled: bool = False
    prompt: str = PROMPT
    max_entry: int = MAX_ENTRY
    digits_only: bool = False
    on_submit: Callable[[str], None] | None = None
    on_cancel: Callable[[], None] | None = None


def open_console(
    *,
    prompt: str = PROMPT,
    text: str = "",
    max_entry: int = MAX_ENTRY,
    digits_only: bool = False,
    obj: object = None,
    on_submit: Callable[[str], None] | None = None,
    on_cancel: Callable[[], None] | None = None,
) -> ConsoleState:
    """Arm ``events.console`` so main.py feeds keys and draw_console paints."""
    con = ConsoleState(
        obj=obj,
        text=text,
        prompt=prompt,
        max_entry=max_entry,
        digits_only=digits_only,
        on_submit=on_submit,
        on_cancel=on_cancel,
    )
    events.console = con
    return con


def close_console() -> None:
    events.console = None


def feed_key(con: ConsoleState, key_code: int, char: str) -> None:
    if con.done:
        return
    # Esc cancels only when a hook asked for it (godmode). Logosta has no Esc.
    if key_code == 27 and con.on_cancel is not None:
        con.cancelled = True
        con.done = True
        con.on_cancel()
        return
    if key_code == 8:
        con.text = con.text[:-1]
        return
    if key_code == 13:
        con.done = True
        if con.on_submit is not None:
            con.on_submit(con.text)
        return
    if not char or not char.isprintable():
        return
    if con.digits_only and not char.isdigit():
        return
    if len(con.text) >= int(con.max_entry):
        return
    con.text += char


def draw_console(canvas, now: float) -> None:
    from lynn.gfx.config_ui import gfxprint

    con = events.console
    if con is None or con.done:
        return
    cursor = "_" if int(now / CURSOR_RATE) % 2 == 0 else ""
    shown = con.text if con.text != "" else ""
    gfxprint(canvas, con.prompt + shown + cursor, 0, 48, (255, 255, 255))
