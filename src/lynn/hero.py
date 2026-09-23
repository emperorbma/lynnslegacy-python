"""ctor_hero, walk input, camera. FB ll_build.bas / engine--LL.bas (trimmed)."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field

from lynn import clock
from lynn.constants import SCREEN_H, SCREEN_W, TRUE
from lynn.macros import check_ice
from lynn.map.collision import check_against_teles, move_object
from lynn.map.types import MapType, RoomType
from lynn.object.char import CharType
from lynn.object.gfx_frame import LLObject_IncrementFrame
from lynn.object.xml_load import LLSystem_CopyNewObject


@dataclass
class MainCharType:
    """FB lynn_structures.bi main_char_type — inventory / HUD fields."""

    attacking: int = 0
    action: int = 0
    action_lock: int = 0
    hasItem: list[int] = field(default_factory=lambda: [0] * 6)
    has_weapon: int = -1
    selected_item: int = 0
    powder: int = 0
    weapon: int = -1
    hasCostume: list[int] = field(default_factory=lambda: [0] * 9)
    isWearing: int = 0
    has_bar: int = 0
    b_key: int = 0
    crazy_points: int = 0
    crazy_cache: int = 0
    crazy_dcache: int = 0
    adrenaline: object | None = None
    dropoutSequence: int = 0
    invisibleEntry: int = 0
    isLoading: int = 0
    songFade: object | None = None

DIR_UP = 0
DIR_RIGHT = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIR_UP_LEFT = 4
DIR_UP_RIGHT = 5
DIR_DOWN_RIGHT = 6
DIR_DOWN_LEFT = 7

# FB dir_keys / calc_slide. Log is natural log.
SLIDE_ADD = 0.02
SLIDE_FRICTION = 0.01
SLIDE_PERIOD = 0.01 - (0.01 * (abs(math.log(0.01)) / 100.0 * 5.0))

_DIAGONAL = {
    (0, -1): DIR_UP,
    (1, 0): DIR_RIGHT,
    (0, 1): DIR_DOWN,
    (-1, 0): DIR_LEFT,
    (-1, -1): DIR_UP_LEFT,
    (1, -1): DIR_UP_RIGHT,
    (1, 1): DIR_DOWN_RIGHT,
    (-1, 1): DIR_DOWN_LEFT,
}


def _held_cardinals(keys_dir: int | Iterable[int] | None) -> list[int]:
    if keys_dir is None:
        return []
    if isinstance(keys_dir, int):
        return [keys_dir]
    return [int(d) for d in keys_dir]


def walk_from_held(keys_dir: int | Iterable[int] | None) -> tuple[int | None, int | None]:
    """FB dir_keys: every held axis moves; facing is last of L,R,D,U.

    Opposite keys on one axis cancel. Returns (face 0–3, move_dir 0–7).
    """
    held = set(_held_cardinals(keys_dir))
    dx = (1 if DIR_RIGHT in held else 0) - (1 if DIR_LEFT in held else 0)
    dy = (1 if DIR_DOWN in held else 0) - (1 if DIR_UP in held else 0)
    move_dir = _DIAGONAL.get((dx, dy))
    if move_dir is None:
        return None, None
    face = DIR_RIGHT if dx > 0 else (DIR_LEFT if dx < 0 else None)
    if dy > 0:
        face = DIR_DOWN
    if dy < 0:
        face = DIR_UP
    return face, move_dir


def ctor_hero(load_images: bool = True) -> CharType:
    hero = CharType()
    hero.id = "data/object/lynn.xml"
    LLSystem_CopyNewObject(hero, load_images=load_images)
    hero.num = -1
    hero.hp = 6
    hero.maxhp = 6
    hero.money = 0
    hero.switch_room = -1
    from lynn.audio import sound_lynn_die

    hero.dead_sound = sound_lynn_die
    if not hero.walk_speed:
        hero.walk_speed = 0.009
    return hero


def ctor_hero_only() -> MainCharType:
    """FB ctor_hero side effects on llg(hero_only): empty weapon and items."""
    only = MainCharType()
    only.weapon = -1
    only.has_weapon = -1
    only.hasItem = [0] * 6
    only.selected_item = 0
    only.powder = 0
    only.hasCostume = [0] * 9
    only.hasCostume[0] = TRUE
    only.isWearing = 0
    only.crazy_points = 0
    only.crazy_cache = 0
    only.crazy_dcache = 0
    only.adrenaline = None
    return only


_cache_wait = 0.0
_crazy_delay = 0.0


def cache_crazy(only: MainCharType) -> None:
    """FB engine--LL.bas: drain crazy_cache/dcache into crazy_points (~100/s)."""
    global _cache_wait
    if _cache_wait == 0:
        if only.crazy_cache > 0:
            only.crazy_points += 1
            only.crazy_cache -= 1
        if only.crazy_dcache > 0:
            only.crazy_points -= 1
            only.crazy_dcache -= 1
        _cache_wait = clock.timer + 0.01
    if clock.timer > _cache_wait:
        _cache_wait = 0


def decay_crazy(only: MainCharType) -> None:
    """FB engine--LL.bas: one decay tick every 0.3s while the bar is charged."""
    global _crazy_delay
    if _crazy_delay == 0:
        _crazy_delay = clock.timer + 0.3
        if only.crazy_points > 0:
            if only.crazy_points > 105:
                only.crazy_points = 105
            only.crazy_dcache += 1
    if clock.timer > _crazy_delay:
        _crazy_delay = 0


def place_hero(hero: CharType, game_map: MapType, entry_i: int = 0) -> int:
    if not game_map.entry:
        return 0
    entry = game_map.entry[entry_i] if entry_i < len(game_map.entry) else game_map.entry[0]
    hero.coords_x = entry.x
    hero.coords_y = entry.y
    hero.direction = entry.direction
    return entry.room


def update_cam(hero: CharType, room: RoomType) -> tuple[int, int]:
    cam_x = int(hero.coords_x) - (((SCREEN_W) - (int(hero.perimeter_x) >> 1)) >> 1) - 1
    cam_y = int(hero.coords_y) - (((SCREEN_H) - (int(hero.perimeter_y) >> 1)) >> 1) - 1
    max_x = max(0, (room.x << 4) - SCREEN_W)
    max_y = max(0, (room.y << 4) - SCREEN_H)
    if cam_x < 0:
        cam_x = 0
    if cam_x > max_x:
        cam_x = max_x
    if cam_y < 0:
        cam_y = 0
    if cam_y > max_y:
        cam_y = max_y
    return cam_x, cam_y


def _ensure_momentum(hero: CharType) -> None:
    if len(getattr(hero, "momentum", []) or []) < 8:
        hero.momentum = [0.0] * 8
    if len(getattr(hero, "momentum_history", []) or []) < 8:
        hero.momentum_history = [0.0] * 8


def _stop_grip(hero: CharType) -> None:
    _ensure_momentum(hero)
    for i in range(8):
        hero.momentum_history[i] = hero.momentum[i]
        hero.momentum[i] = 0.0


def _calc_slide(hero: CharType) -> None:
    _ensure_momentum(hero)
    n, hero.slide_hold = clock.pop_due(hero.slide_hold, SLIDE_PERIOD)
    for _ in range(n):
        for i in range(8):
            v = hero.momentum[i] - SLIDE_FRICTION
            hero.momentum[i] = 0.0 if v < 0.0 else v


def _momentum_move(hero: CharType, room: RoomType, others: list[CharType] | None) -> int:
    """FB __momentum_move: one move_object per dir with leftover momentum."""
    _ensure_momentum(hero)
    moved = 0
    face = hero.direction
    for d in range(8):
        mom = hero.momentum[d]
        if mom == 0.0:
            continue
        hero.direction = d
        look = move_object(hero, room, only_looking=0, moment=mom, others=others)
        if look == 0 and hero.is_psfing == 0 and hero.is_pushing == 0:
            hero.momentum[d] = 0.0
        elif look != 0:
            moved = 1
    hero.direction = face
    return moved


def _hero_ice_step(
    hero: CharType,
    room: RoomType,
    held: list[int],
    face: int | None,
    others: list[CharType] | None,
) -> int:
    if face is not None:
        hero.direction = face
    speed = hero.walk_speed or 0.009
    held_set = set(held)
    n, hero.walk_hold = clock.pop_due(hero.walk_hold, speed)
    moved = 0
    for _ in range(n):
        for d in (DIR_LEFT, DIR_RIGHT, DIR_DOWN, DIR_UP):
            if d in held_set:
                hero.momentum[d] = min(1.0, hero.momentum[d] + SLIDE_ADD)
        if _momentum_move(hero, room, others):
            moved = 1
    _calc_slide(hero)
    if moved == 0:
        hero.moving = 0
        return 0
    hero.moving = 1
    if LLObject_IncrementFrame(hero) != 0:
        hero.frame = 0
        rate = hero.animControl[hero.current_anim].rate if hero.animControl else 0.08
        hero.frame_hold = clock.timer + rate
    return moved


def hero_walk_step(
    hero: CharType,
    room: RoomType,
    keys_dir: int | Iterable[int] | None,
    others: list[CharType] | None = None,
) -> int:
    """FB dir_keys + momentum_move; ice keeps fractional momentum and slides."""
    _ensure_momentum(hero)
    hero.last_cycle_ice = hero.on_ice
    check_ice(hero, room)
    if hero.on_ice == 0:
        hero.coords_x = int(hero.coords_x)
        hero.coords_y = int(hero.coords_y)
    if hero.on_ice != 0 and hero.last_cycle_ice == 0:
        for i in range(4):
            hero.momentum[i] = hero.momentum_history[i]
    held = _held_cardinals(keys_dir)
    face, move_dir = walk_from_held(held)
    if hero.on_ice != 0:
        return _hero_ice_step(hero, room, held, face, others)
    _stop_grip(hero)
    if move_dir is None:
        hero.moving = 0
        hero.walk_hold = 0
        hero.is_psfing = 0
        return 0
    hero.direction = face
    speed = hero.walk_speed or 0.009
    n, hero.walk_hold = clock.pop_due(hero.walk_hold, speed)
    moved = 0
    for _ in range(n):
        hero.direction = move_dir
        step = move_object(hero, room, only_looking=0, moment=1, others=others)
        hero.direction = face
        if step == 0 and hero.is_psfing == 0:
            hero.walk_hold = clock.timer + speed
            break
        moved = 1
    if moved == 0:
        hero.moving = 0
        return 0
    hero.moving = 1
    if LLObject_IncrementFrame(hero) != 0:
        hero.frame = 0
        rate = hero.animControl[hero.current_anim].rate if hero.animControl else 0.08
        hero.frame_hold = clock.timer + rate
    return moved


def try_same_map_room_teleport(hero: CharType, game_map: MapType, room_i: int) -> int:
    """Instant same-map room tele (no fade, song, or map reload). FB change_room case 0, state 2.

    If standing on a tele with empty to_map, set coords to dx,dy and return to_room.
    Map teles are left for enter_map (to_map / to_entry already set by check_against_teles).
    """
    if hero.switch_room != -1:
        return room_i
    if not (0 <= room_i < len(game_map.room)):
        return room_i
    room = game_map.room[room_i]
    tele_i = check_against_teles(hero, room)
    if tele_i == -1:
        return room_i
    tele = room.teleport[tele_i]
    if tele.to_map != "":
        return room_i
    dest_room = tele.to_room
    if dest_room < 0 or dest_room >= game_map.rooms:
        return room_i
    hero.coords_x = tele.dx
    hero.coords_y = tele.dy
    hero.switch_room = -1
    return dest_room


def item_l_key(only: MainCharType) -> None:
    """FB item_l_key_in_sub: cycle selected_item down, skip empty slots."""
    last_selected = only.selected_item
    while True:
        only.selected_item -= 1
        if only.selected_item == -1:
            only.selected_item = 6
        if only.selected_item == last_selected:
            break
        if only.selected_item == 0:
            continue
        if only.hasItem[only.selected_item - 1]:
            break


def item_r_key(only: MainCharType) -> None:
    """FB item_r_key_in_sub: cycle selected_item up, skip empty slots."""
    last_selected = only.selected_item
    while True:
        only.selected_item += 1
        if only.selected_item == 7:
            only.selected_item = 0
        if only.selected_item == last_selected:
            break
        if only.selected_item == 0:
            continue
        if only.hasItem[only.selected_item - 1]:
            break
