"""ctor_hero, walk input, camera. FB ll_build.bas / engine--LL.bas (trimmed)."""

from __future__ import annotations

from dataclasses import dataclass, field

from lynn import clock
from lynn.constants import SCREEN_H, SCREEN_W, TRUE
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


def hero_walk_step(
    hero: CharType,
    room: RoomType,
    keys_dir: int | None,
    others: list[CharType] | None = None,
) -> int:
    """FB dir_keys + momentum_move: 1px per walk_speed, catch up leftover time."""
    if keys_dir is None:
        hero.moving = 0
        hero.walk_hold = 0
        hero.is_psfing = 0
        return 0
    hero.direction = keys_dir
    speed = hero.walk_speed or 0.009
    n, hero.walk_hold = clock.pop_due(hero.walk_hold, speed)
    moved = 0
    for _ in range(n):
        step = move_object(hero, room, only_looking=0, moment=1, others=others)
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
