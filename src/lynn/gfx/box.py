"""FB make_box / blit_box — typewriter + Space to confirm. No yes/no."""

from __future__ import annotations

from dataclasses import dataclass, field

from lynn import clock
from lynn.constants import FALSE, TRUE
from lynn.gfx.image import LLSystem_ImageLoad, frame_surface
from lynn.gfx.menu import graphicalString
from lynn.gfx.palette import LLPalette

TEXTBOX_REGULAR = 0
TEXTBOX_CONFIRMATION = 1
TEXTBOX_SHUTDOWN = 2


@dataclass
class BoxControl:
    activated: int = 0
    text: str = ""
    state: int = 0
    opcount: int = 0
    timer: float = 0.0
    speed: float = 0.021813
    box_IsInited: int = 0
    surf: object | None = None
    font_menu: object | None = None


def make_box(box: BoxControl, text: str, palette: LLPalette | None = None, menu=None) -> None:
    box.activated = TRUE
    box.text = text
    box.state = TEXTBOX_REGULAR
    box.opcount = 0
    box.timer = clock.timer
    box.box_IsInited = TRUE
    box.font_menu = menu
    if palette is not None and box.surf is None:
        header = LLSystem_ImageLoad("data/pictures/textbox.spr")
        if header.frames:
            box.surf = frame_surface(header, 0, palette)


def tick_box(box: BoxControl, action: int) -> None:
    if box.activated == 0:
        return
    if box.state == TEXTBOX_REGULAR:
        if action != 0:
            box.opcount = len(box.text)
            box.state = TEXTBOX_CONFIRMATION
            return
        if clock.timer >= box.timer + box.speed:
            box.timer = clock.timer
            if box.opcount < len(box.text):
                box.opcount += 1
            if box.opcount >= len(box.text):
                box.state = TEXTBOX_CONFIRMATION
    elif box.state == TEXTBOX_CONFIRMATION:
        if action != 0:
            box.state = TEXTBOX_SHUTDOWN
            box.activated = FALSE
            box.box_IsInited = FALSE


def blit_box(canvas, box: BoxControl) -> None:
    if box.activated == 0 and box.state != TEXTBOX_SHUTDOWN:
        return
    if box.activated == 0:
        return
    if box.surf is not None:
        canvas.blit(box.surf, (0, 0))
    shown = box.text[: box.opcount]
    if box.font_menu is not None and shown:
        graphicalString(canvas, box.font_menu, shown, 9, 8)
