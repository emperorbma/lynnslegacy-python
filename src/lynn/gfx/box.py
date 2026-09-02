"""FB make_box / init_box / blit_box — wrap, {NEWLINE}, typewriter, 4-line pages."""

from __future__ import annotations

from dataclasses import dataclass, field

from lynn import clock
import lynn.events as events
from lynn.constants import FALSE, TRUE, conf_Box
from lynn.gfx.image import LLSystem_ImageLoad, frame_surface
from lynn.gfx.menu import graphicalString
from lynn.gfx.palette import LLPalette

TEXTBOX_REGULAR = 0
TEXTBOX_CONFIRMATION = 1
TEXTBOX_SHUTDOWN = 2

box_jump_back = 0
box_kill_switch = 1

BOX_COLS = 36
BOX_CENTER = 38
PAGE_LINES = 4
LINE_H = 16
TEXT_X = 9
TEXT_Y = 8


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
    next_surf: object | None = None
    font_menu: object | None = None
    rows: list[str] = field(default_factory=list)
    current_line: int = 0
    jump_switch: int = 0
    flashbox: int = 0
    flashhook: float = 0.0
    confBox: int = 0
    selected: int = 0


def parse_text(text: str) -> str:
    """FB parseText: expand {tokens}. {NEWLINE} is kept for wrapping."""
    if not text:
        return ""
    res: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "{":
            j = i
            while j < n and text[j] != "}":
                j += 1
            if j < n:
                tok = text[i : j + 1]
                upper = tok.upper()
                if upper == "{NEWLINE}":
                    res.append("{NEWLINE}")
                elif upper == "{HEALTHNOW}":
                    hero = events.hero
                    res.append(str(int(hero.maxhp) if hero is not None else 6))
                elif upper == "{HEALTHUP}":
                    hero = events.hero
                    res.append(str(int(hero.maxhp) + 1 if hero is not None else 7))
                elif upper == "{HEALTHPRICE}":
                    hero = events.hero
                    hp = int(hero.maxhp) if hero is not None else 6
                    res.append(str(50 + (hp - 6) * 5))
                i = j + 1
                if i >= n:
                    break
        res.append(text[i])
        i += 1
    return "".join(res)


def _split_words(buf: str) -> list[str]:
    """FB init_box: split on space, keep the trailing space on each word."""
    words: list[str] = [""]
    for ch in buf:
        words[-1] += ch
        if ch == " ":
            words.append("")
    if words and words[-1] == "":
        words.pop()
    return words or [""]


def wrap_lines(text: str) -> list[str]:
    """FB init_box wrap: < 36 chars, hard break on '{NEWLINE} '."""
    buf = parse_text(text)
    words = _split_words(buf)
    lines: list[str] = []
    msgline = ""
    wi = 0
    while True:
        if wi < len(words):
            word = words[wi]
            if word != "{NEWLINE} " and (not msgline or len(msgline) + len(word) < BOX_COLS):
                msgline += word
                wi += 1
            else:
                if word == "{NEWLINE} ":
                    wi += 1
                lines.append(msgline)
                msgline = ""
        else:
            lines.append(msgline)
            break
    return lines or [""]


def _center_line(line: str) -> str:
    """FB: pad into 37 bytes, left offset (38 - len) // 2."""
    pad = (BOX_CENTER - len(line)) // 2
    if pad < 0:
        pad = 0
    return (" " * pad) + line


def make_box(
    box: BoxControl,
    text: str,
    palette: LLPalette | None = None,
    menu=None,
    conf: int = 0,
) -> None:
    box.activated = TRUE
    box.text = text
    box.state = TEXTBOX_REGULAR
    box.opcount = 0
    box.timer = clock.timer
    box.box_IsInited = TRUE
    box.font_menu = menu
    box.rows = [_center_line(line) for line in wrap_lines(text)]
    box.current_line = 0
    box.jump_switch = 0
    box.flashbox = 0
    box.flashhook = 0.0
    box.confBox = TRUE if conf == conf_Box or conf == TRUE else 0
    box.selected = 0
    if palette is not None and box.surf is None:
        header = LLSystem_ImageLoad("data/pictures/textbox.spr")
        if header.frames:
            box.surf = frame_surface(header, 0, palette)
        nxt = LLSystem_ImageLoad("data/pictures/textdown.spr")
        if nxt.frames:
            box.next_surf = frame_surface(nxt, 0, palette)


def _line_len(box: BoxControl) -> int:
    if 0 <= box.current_line < len(box.rows):
        return len(box.rows[box.current_line])
    return 0


def _skip_spaces(box: BoxControl) -> None:
    row = box.rows[box.current_line] if 0 <= box.current_line < len(box.rows) else ""
    while box.opcount < len(row) and (row[box.opcount] == " " or row[box.opcount] == "\0"):
        box.opcount += 1


def tick_box(box: BoxControl, action: int) -> None:
    if box.activated == 0:
        return
    if box.state == TEXTBOX_REGULAR:
        if action != 0:
            while True:
                if box.current_line >= len(box.rows) - 1:
                    box.jump_switch = box_kill_switch
                    break
                if (box.current_line & 3) == 3:
                    break
                box.current_line += 1
            box.opcount = max(0, _line_len(box) - 1)
            box.state = TEXTBOX_CONFIRMATION
            return
        if clock.timer >= box.timer + box.speed:
            box.timer = clock.timer
            box.opcount += 1
            _skip_spaces(box)
        if box.opcount >= _line_len(box):
            if box.current_line >= len(box.rows) - 1:
                box.opcount = max(0, _line_len(box) - 1)
                box.state = TEXTBOX_CONFIRMATION
                box.jump_switch = box_kill_switch
            elif (box.current_line & 3) == 3:
                box.opcount = max(0, _line_len(box) - 1)
                box.state = TEXTBOX_CONFIRMATION
                box.jump_switch = box_jump_back
            else:
                box.opcount = 0
                box.current_line += 1
                _skip_spaces(box)
    elif box.state == TEXTBOX_CONFIRMATION:
        if box.confBox != 0:
            if events.keys.right != 0:
                box.selected = 1
            if events.keys.left != 0:
                box.selected = 0
            if events.keys.enter_pulse != 0:
                box.state = TEXTBOX_SHUTDOWN
                box.activated = FALSE
                box.box_IsInited = FALSE
            return
        if action != 0:
            if box.jump_switch == box_kill_switch:
                box.state = TEXTBOX_SHUTDOWN
                box.activated = FALSE
                box.box_IsInited = FALSE
            else:
                box.state = TEXTBOX_REGULAR
                box.current_line += 1
                box.opcount = 0
                box.timer = clock.timer
                _skip_spaces(box)


def blit_box(canvas, box: BoxControl) -> None:
    if box.activated == 0:
        return
    if box.surf is not None:
        canvas.blit(box.surf, (0, 0))
    if box.font_menu is None or not box.rows:
        return
    page_base = box.current_line & ~3
    page_row = box.current_line & 3
    for i in range(page_row):
        li = page_base + i
        if 0 <= li < len(box.rows):
            graphicalString(canvas, box.font_menu, box.rows[li], TEXT_X, TEXT_Y + i * LINE_H)
    if 0 <= box.current_line < len(box.rows):
        shown = box.rows[box.current_line][: box.opcount + 1]
        graphicalString(canvas, box.font_menu, shown, TEXT_X, TEXT_Y + page_row * LINE_H)
    if box.state == TEXTBOX_CONFIRMATION and box.confBox != 0:
        yes = "> Yes" if box.selected == 0 else "  Yes"
        no = "> No" if box.selected == 1 else "  No"
        graphicalString(canvas, box.font_menu, yes, 9 + (10 << 3), 8 + (3 << 4))
        graphicalString(canvas, box.font_menu, no, 9 + (26 << 3), 8 + (3 << 4))
    elif box.state == TEXTBOX_CONFIRMATION and box.jump_switch != box_kill_switch:
        if clock.timer >= box.flashhook:
            box.flashhook = clock.timer + 0.18
            box.flashbox = 0 if box.flashbox != 0 else TRUE
        if box.flashbox != 0 and box.next_surf is not None:
            canvas.blit(box.next_surf, (304, 64))
