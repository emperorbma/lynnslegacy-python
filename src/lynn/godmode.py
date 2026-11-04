"""Godmode console.

F9 opens Load, Save, Heal, Money, and MaxHP. Load and Save open the file-slot
list. Heal / Money / MaxHP open the shared FerUs line console (events.console)
with amount prompts. Esc steps back; Esc on the root console closes it.
"""

from __future__ import annotations

import json
import zlib
from dataclasses import dataclass, field

from lynn.object.save import example_short_name, list_example_saves, load_save_data

SLOT_ROWS = 4
ROOT_COMMANDS = ("Load", "Save", "Heal", "Money", "MaxHP")
PROMPT_MAX_LEN = 4


@dataclass
class GodEntry:
    kind: str
    label: str
    save: object = None
    slot: int = 0


@dataclass
class GodMenu:
    open: bool = False
    page: str = "root"
    index: int = 0
    entries: list = field(default_factory=list)
    anims: list | None = None
    prompt_kind: str = ""


def _slot_path(slot: int):
    from lynn.object import save as save_mod

    return save_mod.project_root() / f"ll_save{slot}.sav"


def _read_save(path):
    if path is None or not path.is_file():
        return None
    try:
        return load_save_data(path)
    except (OSError, ValueError, EOFError, zlib.error, json.JSONDecodeError, UnicodeDecodeError):
        return None


def load_rows() -> list[GodEntry]:
    """Live slots that exist, then fixture saves."""
    rows: list[GodEntry] = []
    for slot in range(1, 5):
        data = _read_save(_slot_path(slot))
        if data is not None:
            rows.append(GodEntry("load", f"slot {slot}", data, slot))
    for path in list_example_saves():
        data = _read_save(path)
        if data is None:
            continue
        rows.append(GodEntry("load", example_short_name(path.name), data))
    return rows


def save_rows() -> list[GodEntry]:
    """The four live slots. Empty ones can still be written."""
    return [
        GodEntry("save", f"slot {slot}", _read_save(_slot_path(slot)), slot)
        for slot in range(1, 5)
    ]


def god_menu_count(menu: GodMenu) -> int:
    if menu.page == "root":
        return len(ROOT_COMMANDS)
    return len(menu.entries)


def god_menu_open(menu: GodMenu) -> None:
    menu.open = True
    menu.page = "root"
    menu.index = 0
    menu.entries = []
    menu.prompt_kind = ""


def god_menu_close(menu: GodMenu) -> None:
    from lynn.console import close_console

    menu.open = False
    menu.prompt_kind = ""
    close_console()


def god_menu_move(menu: GodMenu, delta: int) -> None:
    import lynn.events as events

    # Amount entry owns the keyboard while the FerUs console is up.
    if events.console is not None and not events.console.done:
        return
    count = god_menu_count(menu)
    if count <= 0 or delta == 0:
        return
    menu.index = (menu.index + delta) % count


def _prompt_root_index(kind: str) -> int:
    if kind == "heal":
        return 2
    if kind == "money":
        return 3
    if kind == "maxhp":
        return 4
    return 0


def god_menu_back(menu: GodMenu) -> None:
    """Esc steps from a list/prompt back to the console, and from the console out."""
    import lynn.events as events
    from lynn.console import close_console

    if events.console is not None and not events.console.done:
        close_console()
        menu.index = _prompt_root_index(menu.prompt_kind)
        menu.prompt_kind = ""
        menu.page = "root"
        return
    if menu.page == "load":
        menu.page = "root"
        menu.index = 0
        menu.entries = []
        return
    if menu.page == "save":
        menu.page = "root"
        menu.index = 1
        menu.entries = []
        return
    god_menu_close(menu)


def _parse_amount(text: str) -> int | None:
    raw = (text or "").strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def god_menu_begin_prompt(menu: GodMenu, kind: str, hero=None) -> None:
    """Open the shared FerUs line console for an amount."""
    from lynn.console import open_console

    menu.page = "root"
    menu.prompt_kind = kind

    if kind == "money":
        prompt, text = "Gold +> ", "10"
    elif kind == "maxhp":
        prompt, text = "MaxHP +> ", "1"
    else:
        prompt, text = "Heal +> ", ""

    def _submit(entered: str) -> None:
        from lynn.console import close_console

        amount = _parse_amount(entered)
        if kind == "money":
            apply_money(hero, 10 if amount is None else amount)
        elif kind == "maxhp":
            apply_maxhp(hero, 1 if amount is None else amount)
        else:
            apply_heal(hero, None if amount is None else amount)
        menu.index = _prompt_root_index(kind)
        menu.prompt_kind = ""
        close_console()

    def _cancel() -> None:
        from lynn.console import close_console

        menu.index = _prompt_root_index(kind)
        menu.prompt_kind = ""
        close_console()

    open_console(
        prompt=prompt,
        text=text,
        max_entry=PROMPT_MAX_LEN,
        digits_only=True,
        on_submit=_submit,
        on_cancel=_cancel,
    )


def god_menu_confirm(menu: GodMenu, hero=None) -> GodEntry | None:
    """Enter. None means the console opened a list/prompt instead of a load/save."""
    import lynn.events as events

    if events.console is not None and not events.console.done:
        return None
    if menu.page == "root":
        label = ROOT_COMMANDS[menu.index % len(ROOT_COMMANDS)]
        if label == "Load":
            menu.page = "load"
            menu.index = 0
            menu.entries = load_rows()
            return None
        if label == "Save":
            menu.page = "save"
            menu.index = 0
            menu.entries = save_rows()
            return None
        if label == "Heal":
            god_menu_begin_prompt(menu, "heal", hero)
            return None
        if label == "Money":
            god_menu_begin_prompt(menu, "money", hero)
            return None
        if label == "MaxHP":
            god_menu_begin_prompt(menu, "maxhp", hero)
            return None
        return None
    if not menu.entries:
        return None
    menu.index %= len(menu.entries)
    return menu.entries[menu.index]


def visible_rows(menu: GodMenu) -> tuple[int, list[GodEntry]]:
    """Four rows, same as the save screen. The highlight stays on screen."""
    entries: list[GodEntry] = menu.entries
    count = len(entries)
    if count <= SLOT_ROWS:
        start = 0
    else:
        start = menu.index - 1
        if start < 0:
            start = 0
        if start > count - SLOT_ROWS:
            start = count - SLOT_ROWS
        if menu.index < start:
            start = menu.index
        if menu.index >= start + SLOT_ROWS:
            start = menu.index - SLOT_ROWS + 1
    return start, entries[start : start + SLOT_ROWS]


def resume_entry(game_map, hero, room_i: int) -> int:
    """Map entry in this room closest to Lynn. Saves resume there."""
    if game_map is None or hero is None:
        return 0
    best_i = 0
    best_d = None
    for i, ent in enumerate(getattr(game_map, "entry", ()) or ()):
        if int(ent.room) != int(room_i):
            continue
        dist = abs(int(ent.x) - int(hero.coords_x)) + abs(int(ent.y) - int(hero.coords_y))
        if best_d is None or dist < best_d:
            best_d = dist
            best_i = i
    return best_i


def write_god_slot(slot: int, entry: int):
    """Write the live hero into ll_saveN.sav and return the file just written."""
    from lynn.object.save import LLSystem_ReadSaveFile, LLSystem_WriteSaveFile

    LLSystem_WriteSaveFile(f"ll_save{slot}.sav", entry)
    return LLSystem_ReadSaveFile(f"ll_save{slot}.sav")


def _refresh_money_gates() -> None:
    """Clear sticky poor-refusal sel_seq so shops re-check after godmode gold.

    FB healthguy/outfit branches only raise sel_seq when short on gold; they
    never clear it until the actor respawns. Godmode money mid-room would
    otherwise leave the healthguy stuck on the "come back later" line.
    """
    import lynn.events as events
    from lynn.constants import u_healthguy

    for obj in events.current_others or []:
        if obj is None:
            continue
        if int(getattr(obj, "unique_id", 0) or 0) == u_healthguy:
            obj.sel_seq = 0
            continue
        # Outfit shop pieces use chap as the price and sel_seq 1 as the refuse.
        if int(getattr(obj, "sel_seq", 0) or 0) == 1 and int(getattr(obj, "chap", 0) or 0) > 0:
            funcs = getattr(obj, "funcs", None)
            if funcs is None:
                continue
            for state in getattr(funcs, "func", ()) or ():
                for fn in state or ():
                    name = getattr(fn, "__name__", "")
                    if name == "__outfit_branch":
                        obj.sel_seq = 0
                        break


def apply_money(hero, amount: int = 10) -> None:
    """Add gold. The HUD draws at most 999."""
    if hero is None:
        return
    add = max(0, int(amount))
    hero.money = min(999, int(getattr(hero, "money", 0) or 0) + add)
    _refresh_money_gates()


def apply_heal(hero, amount: int | None = None) -> None:
    """Restore HP. ``amount is None`` (blank prompt) fills up to maxhp."""
    if hero is None:
        return
    maxhp = int(hero.maxhp or hero.hp or 6)
    if amount is None:
        hero.hp = maxhp
    else:
        hero.hp = min(maxhp, max(0, int(hero.hp or 0) + max(0, int(amount))))
    hero.dead = 0
    hero.hurt = 0
    hero.dmg_id = 0


def apply_maxhp(hero, amount: int = 1) -> None:
    """Increase maxhp and current hp by the same gain."""
    if hero is None:
        return
    add = max(0, int(amount))
    if add == 0:
        return
    old = int(hero.maxhp or 0)
    hero.maxhp = min(99, old + add)
    gained = int(hero.maxhp) - old
    hero.hp = min(int(hero.maxhp), int(hero.hp or 0) + gained)
    hero.dead = 0


def _slot_anims(palette) -> list:
    from lynn.gfx.image import frame_surfaces
    from lynn.object.char import CharType
    from lynn.object.xml_load import LLSystem_ObjectFromXML

    obj = CharType()
    obj.id = "data/object/savepoint.xml"
    LLSystem_ObjectFromXML(obj, load_images=True)
    return [frame_surfaces(anim, palette) if anim.frames else [] for anim in obj.anim]


def _blit_console(canvas, font_menu, menu: GodMenu) -> None:
    import pygame

    from lynn.gfx.menu import graphicalString

    panel = pygame.Surface((160, 28 + 16 * (len(ROOT_COMMANDS) + 1)))
    panel.fill((0, 0, 32))
    panel.set_alpha(230)
    canvas.blit(panel, (16, 16))
    if font_menu is None:
        return
    graphicalString(canvas, font_menu, "GODMODE", 24, 22)
    for i, label in enumerate(ROOT_COMMANDS):
        mark = ">" if i == menu.index else " "
        graphicalString(canvas, font_menu, f"{mark} {label}", 24, 42 + i * 16)


def blit_god_menu(canvas, font_menu, menu: GodMenu, palette, hud) -> None:
    """Console on the root page. Load and Save use the save-slot screen.

    Amount prompts paint through ``lynn.console.draw_console`` (FerUs line).
    """
    from lynn.gfx.menu import graphicalString
    from lynn.object.char import CharType
    from lynn.object.save import blit_save_menu

    if menu.page == "root":
        _blit_console(canvas, font_menu, menu)
        return
    if menu.anims is None and palette is not None:
        menu.anims = _slot_anims(palette)
    start, shown = visible_rows(menu)
    holder = CharType()
    holder.menu_sel = menu.index - start if shown else 0
    holder.save = [row.save for row in shown]
    while len(holder.save) < SLOT_ROWS:
        holder.save.append(None)
    blit_save_menu(canvas, holder, menu.anims or [], hud)
    if font_menu is None:
        return
    for i, row in enumerate(shown):
        graphicalString(canvas, font_menu, row.label[:16], 168, i * 50 + 4)
