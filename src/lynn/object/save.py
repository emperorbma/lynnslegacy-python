"""FB object_etc.bas __do_menu_save / __handle_menu (JSON first cut)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import lynn.events as events
from lynn import clock
from lynn.constants import TRUE, u_savepoint
from lynn.object.char import CharType
from lynn.object.dispatch import register_func
from lynn.paths import project_root


@dataclass
class SaveData:
    hp: int = 6
    maxhp: int = 6
    gold: int = 0
    weapon: int = -1
    hasItem: list[int] = field(default_factory=lambda: [0] * 6)
    bar: int = 0
    hasCostume: list[int] = field(default_factory=lambda: [0] * 9)
    isWearing: int = 0
    key: int = 0
    b_key: int = 0
    map: str = ""
    entry: int = 0
    happen: list[int] = field(default_factory=list)
    rooms: int = 0


def save_path(slot: int) -> Path:
    return project_root() / f"ll_save{slot + 1}.sav"


def LLSystem_ReadSaveFile(name: str) -> SaveData | None:
    path = Path(name)
    if not path.is_file():
        path = project_root() / name
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    data = SaveData()
    for key in (
        "hp",
        "maxhp",
        "gold",
        "weapon",
        "bar",
        "isWearing",
        "key",
        "b_key",
        "map",
        "entry",
        "rooms",
    ):
        if key in raw:
            setattr(data, key, raw[key])
    if isinstance(raw.get("hasItem"), list):
        data.hasItem = list(raw["hasItem"]) + [0] * 6
        data.hasItem = data.hasItem[:6]
    if isinstance(raw.get("hasCostume"), list):
        data.hasCostume = list(raw["hasCostume"]) + [0] * 9
        data.hasCostume = data.hasCostume[:9]
    if isinstance(raw.get("happen"), list):
        data.happen = [int(x) for x in raw["happen"]]
    return data


def LLSystem_WriteSaveFile(name: str, entry: int) -> None:
    hero = events.hero
    only = events.hero_only
    payload = {
        "hp": int(hero.hp) if hero is not None else 6,
        "maxhp": int(hero.maxhp) if hero is not None else 6,
        "gold": int(hero.money) if hero is not None else 0,
        "weapon": int(only.has_weapon) if only is not None else -1,
        "hasItem": list(only.hasItem) if only is not None else [0] * 6,
        "bar": int(only.has_bar) if only is not None else 0,
        "hasCostume": list(only.hasCostume) if only is not None else [0] * 9,
        "isWearing": int(only.isWearing) if only is not None else 0,
        "key": int(hero.key) if hero is not None else 0,
        "b_key": int(only.b_key) if only is not None else 0,
        "map": events.map_filename,
        "entry": int(entry),
        "happen": [i for i, v in enumerate(events.now) if v != 0],
        "rooms": 0,
    }
    path = Path(name)
    if not path.is_absolute():
        path = project_root() / name
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def __do_menu_save(this: CharType) -> int:
    hero = events.hero
    only = events.hero_only
    if hero is not None:
        hero.menu_sel = 2
    events.do_hud = 0
    events.box_entity = this
    if only is not None:
        only.action_lock = TRUE

    if this.menu_lock != 0:
        if events.keys.escape == 0:
            this.menu_lock = 0
            this.menu_sel = 0
            this.read_lock = 0
            if hero is not None:
                hero.menu_sel = 0
            events.do_hud = TRUE
            events.box_entity = None
            if only is not None:
                only.action_lock = 0
            return -2

    if this.read_lock == 0:
        this.save = [
            LLSystem_ReadSaveFile("ll_save1.sav"),
            LLSystem_ReadSaveFile("ll_save2.sav"),
            LLSystem_ReadSaveFile("ll_save3.sav"),
            LLSystem_ReadSaveFile("ll_save4.sav"),
        ]
        this.read_lock = TRUE

    if events.keys.down != 0:
        if this.walk_hold == 0:
            this.menu_sel += 1
            if this.menu_sel == 4:
                this.menu_sel = 0
            this.walk_hold = clock.timer + (this.walk_speed or 1)
    elif events.keys.up != 0:
        if this.walk_hold == 0:
            this.menu_sel -= 1
            if this.menu_sel == -1:
                this.menu_sel = 3
            this.walk_hold = clock.timer + (this.walk_speed or 1)
    else:
        this.walk_hold = 0
    if clock.timer >= this.walk_hold:
        this.walk_hold = 0

    if events.keys.enter_pulse != 0:
        LLSystem_WriteSaveFile(f"ll_save{this.menu_sel + 1}.sav", this.chap)
        from lynn.audio import play_sample, sound_switch

        play_sample(sound_switch)
        this.read_lock = 0

    if events.keys.escape != 0:
        this.menu_lock = 1
    return 0


def blit_save_menu(canvas, savepoint: CharType, anims: list, hud) -> None:
    """FB __handle_menu case 2: four file slots + HUD overlay if occupied."""
    from lynn.gfx.hud import hud_pip_frame

    if savepoint is None or not anims:
        return
    for menu_sels in range(4):
        m_opt = menu_sels * 50
        anim_i = menu_sels * 2 + 7 + (1 if savepoint.menu_sel == menu_sels else 0)
        if 0 <= anim_i < len(anims) and anims[anim_i]:
            canvas.blit(anims[anim_i][0], (0, m_opt))
        link = None
        if menu_sels < len(savepoint.save):
            link = savepoint.save[menu_sels]
        if link is None or hud is None or not hud.img:
            continue
        pips = hud.img[0] if hud.img else []
        if len(pips) >= 3:
            for p in range(30):
                x_opt = ((p % 15) << 3) + 8
                y_opt = ((p // 15) << 3) + 8
                canvas.blit(pips[hud_pip_frame(link.hp, link.maxhp, p)], (49 + x_opt, y_opt + m_opt))
        if len(hud.img) > 2 and hud.img[2]:
            canvas.blit(hud.img[2][0], (275, 16 + m_opt))
        money = max(0, min(999, int(link.gold)))
        digits = hud.img[3] if len(hud.img) > 3 else []
        mny = f"{money:03d}"
        for nums in range(3):
            d = ord(mny[nums]) - 48
            if digits and 0 <= d < len(digits):
                canvas.blit(digits[d], (289 + (nums << 3), 16 + m_opt))


def is_savepoint(obj: CharType) -> bool:
    return obj.unique_id == u_savepoint


register_func("__do_menu_save", __do_menu_save)
