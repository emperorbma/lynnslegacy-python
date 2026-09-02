"""FB object_etc.bas __do_menu_save / __handle_menu.

New saves are JSON. Original FB files are a 12-byte ZLIB header plus zlib
payload (stdlib zlib; same as compress2).
"""

from __future__ import annotations

import json
import zlib
from dataclasses import dataclass, field
from pathlib import Path

import lynn.events as events
from lynn import clock
from lynn.constants import LL_EVENTS_MAX, TRUE, u_savepoint
from lynn.object.char import CharType
from lynn.object.dispatch import register_func
from lynn.paths import project_root
from lynn.vfile import VFile


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
    hasVisited: list[int] = field(default_factory=list)


def save_path(slot: int) -> Path:
    return project_root() / f"ll_save{slot + 1}.sav"


def example_save_dir() -> Path:
    return project_root() / "tests" / "fixtures"


def resolve_save_spec(spec: str) -> Path:
    """Find a save for loading. `1` / `test_example_save1` → fixtures; else game-root or path."""
    raw = spec.strip().replace("\\", "/")
    if not raw:
        raise FileNotFoundError("empty save spec")
    names: list[str] = []
    if raw.isdigit():
        names.append(f"test_example_save{raw}.sav")
        names.append(f"ll_save{raw}.sav")
    else:
        names.append(Path(raw).name)
        if not Path(raw).name.lower().endswith(".sav"):
            names.append(Path(raw).name + ".sav")
            names.append(f"test_example_save{Path(raw).name}.sav")
    candidates = [Path(raw)]
    for name in names:
        candidates.append(example_save_dir() / name)
        candidates.append(project_root() / name)
        candidates.append(project_root() / raw)
    seen: set[Path] = set()
    for cand in candidates:
        try:
            resolved = cand.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    raise FileNotFoundError(f"save not found: {spec}")


def apply_save_happen(data: SaveData) -> None:
    """Restore llg(now) happen flags. Call after reset_events, before room spawn."""
    for i in range(len(events.now)):
        events.now[i] = 0
    for i in data.happen:
        if 0 <= i < len(events.now):
            events.now[i] = TRUE


def apply_save_hero(hero, only, data: SaveData) -> None:
    """Copy inventory / HP / gold from a save onto the live hero."""
    if hero is not None:
        hero.hp = int(data.hp)
        hero.maxhp = int(data.maxhp)
        hero.money = int(data.gold)
        hero.key = int(data.key)
    if only is not None:
        only.has_weapon = int(data.weapon)
        only.weapon = int(data.weapon)
        only.hasItem = (list(data.hasItem) + [0] * 6)[:6]
        only.has_bar = int(data.bar)
        only.hasCostume = (list(data.hasCostume) + [0] * 9)[:9]
        only.isWearing = int(data.isWearing)
        only.b_key = int(data.b_key)


def sequence_LoadGame(saved_info: SaveData | None) -> None:
    """FB sequence_LoadGame: copy the slot onto the live hero, then change_room type 1."""
    if saved_info is None:
        return
    apply_save_happen(saved_info)
    apply_save_hero(events.hero, events.hero_only, saved_info)
    hero = events.hero
    only = events.hero_only
    if hero is not None:
        hero.to_map = saved_info.map
        hero.to_entry = int(saved_info.entry)
        hero.switch_room = -2
        hero.chap = 0
        hero.menu_sel = 0
    if only is not None:
        only.action_lock = 0
        only.isLoading = 0
    events.do_hud = TRUE
    events.box_entity = None


def _resolve_save_path(name: str) -> Path | None:
    path = Path(name)
    if path.is_absolute():
        return path if path.is_file() else None
    rooted = project_root() / path
    if rooted.is_file():
        return rooted
    if path.is_file():
        return path
    return None


def _s8(v: int) -> int:
    return v - 256 if v >= 128 else v


def _read_binary_save(blob: bytes) -> SaveData:
    """FB zLib_DeCompress + VFile_Get layout in LLSystem_ReadSaveFile."""
    if len(blob) < 12 or blob[:4] != b"ZLIB":
        raise ValueError("not a Lynn ZLIB save")
    uncomp = int.from_bytes(blob[4:8], "little", signed=True)
    comp = int.from_bytes(blob[8:12], "little", signed=True)
    payload = blob[12 : 12 + max(comp, 0)]
    raw = zlib.decompress(payload)
    if uncomp > 0 and len(raw) != uncomp:
        raise ValueError(f"save size {len(raw)} != header {uncomp}")
    vf = VFile(raw)
    data = SaveData()
    data.hp = vf.i32()
    data.maxhp = vf.i32()
    data.gold = vf.i32()
    data.weapon = vf.i32()
    data.hasItem = [vf.i32() for _ in range(6)]
    data.bar = vf.i32()
    data.hasCostume = [_s8(b) for b in vf.raw(9)]
    data.isWearing = vf.i32()
    data.key = vf.i32()
    data.b_key = vf.i32()
    data.map = vf.hstring()
    data.entry = vf.i32()
    happen = vf.raw(LL_EVENTS_MAX)
    data.happen = [i for i, v in enumerate(happen) if v != 0]
    data.rooms = vf.i32()
    if data.rooms != 0:
        data.hasVisited = [vf.u8() for _ in range(data.rooms)]
    return data


def _read_json_save(text: str) -> SaveData:
    raw = json.loads(text)
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
    if isinstance(raw.get("hasVisited"), list):
        data.hasVisited = [int(x) for x in raw["hasVisited"]]
    return data


def LLSystem_ReadSaveFile(name: str) -> SaveData | None:
    path = _resolve_save_path(name)
    if path is None:
        return None
    blob = path.read_bytes()
    if blob.startswith(b"ZLIB"):
        try:
            return _read_binary_save(blob)
        except (OSError, ValueError, EOFError, zlib.error):
            return None
    try:
        return _read_json_save(blob.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


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


def blit_title_menu(canvas, menu_obj: CharType, anims: list, hud) -> None:
    """FB __handle_menu cases 1–2: Begin/Continue/Quit or four file slots."""
    hero = events.hero
    if hero is None:
        return
    if hero.menu_sel == 1:
        if anims and anims[0]:
            canvas.blit(anims[0][0], (32, 32))
        for menu_sels in range(3):
            anim_i = menu_sels * 2 + 1 + (1 if menu_obj.menu_sel == menu_sels else 0)
            if anims and 0 <= anim_i < len(anims) and anims[anim_i]:
                canvas.blit(anims[anim_i][0], (64 * (menu_sels + 1), 96))
        return
    if hero.menu_sel == 2:
        blit_save_menu(canvas, menu_obj, anims, hud)


def blit_save_menu(canvas, savepoint: CharType, anims: list, hud) -> None:
    """FB __handle_menu case 2: file slots, lynnstatus preview, items, HP, gold."""
    from lynn.gfx.hud import hud_pip_frame

    if savepoint is None:
        return
    for menu_sels in range(4):
        m_opt = menu_sels * 50
        anim_i = menu_sels * 2 + 7 + (1 if savepoint.menu_sel == menu_sels else 0)
        if anims and 0 <= anim_i < len(anims) and anims[anim_i]:
            canvas.blit(anims[anim_i][0], (0, m_opt))
        link = None
        if menu_sels < len(savepoint.save):
            link = savepoint.save[menu_sels]
        if link is None or hud is None:
            continue
        weap = int(link.weapon) % 3
        if weap < 0:
            weap = 0
        sav = getattr(hud, "sav_img", None) or []
        if 0 <= weap < len(sav) and sav[weap]:
            canvas.blit(sav[weap][0], (32, m_opt))
        items = hud.img[1] if hud.img and len(hud.img) > 1 else []
        has_item = list(link.hasItem) + [0] * 6
        for put_h in range(6):
            if has_item[put_h] == 0:
                continue
            frame_i = put_h + 1
            if items and 0 <= frame_i < len(items):
                canvas.blit(items[frame_i], (57 + (put_h * 16), m_opt + 26))
        if not hud.img:
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
