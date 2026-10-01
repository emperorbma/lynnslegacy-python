"""FB handle_MiniMap / minimap_Blit / LLMiniMap_LoadMiniMap.

M opens the map in a dungeon. Arrows pan, [ and ] change floors, Escape
closes it. A missing .mni (Ice Field) leaves the map unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

import lynn.events as events
from lynn.paths import resolve_data_path
from lynn.vfile import VFile

DOOR_OPEN = 0
DOOR_LOCKED = 1
DOOR_BARRED = 2
DOOR_FKEYLOCKED = 3
DOOR_STAIR = 4

VIEW_X = 0
VIEW_Y = 20
VIEW_W = 320
VIEW_H = 160
PAN_DELAY = 0.023
PULSE_DELAY = 0.05
PULSE = (36, 38, 40, 41, 43, 44, 43, 41, 40, 38)
_MAX_DOORS = 64
_MAX_CODES = 32


@dataclass
class MiniDoor:
    x: int
    y: int
    codes: tuple[int, ...]
    id: int


@dataclass
class MiniRoom:
    x: int
    y: int
    floor: int
    doors: tuple[MiniDoor, ...] = ()
    has_visited: int = 0


@dataclass
class MiniMap:
    rooms: tuple[MiniRoom, ...] = ()
    camera_x: int = 0
    camera_y: int = 0
    floor: int = 0
    focus: int = 0
    open: bool = False
    move_delay: float = 0.0
    pulse_i: int = 0
    pulse_timer: float = 0.0


def _mni_path(game_map) -> Path | None:
    name = str(getattr(game_map, "filename", "") or "").replace("\\", "/")
    stem = Path(name).stem
    if not stem:
        return None
    found = resolve_data_path(f"data/map/{stem}.mni")
    if found is not None:
        return found
    return resolve_data_path(str(Path(name).with_suffix(".mni")))


def load_minimap(path: Path | str, room_count: int) -> MiniMap | None:
    """FB LLMiniMap_LoadMiniMap. Missing or truncated files return None."""
    file_path = Path(path)
    if room_count < 0 or not file_path.is_file():
        return None
    try:
        vf = VFile(file_path.read_bytes())
        rooms: list[MiniRoom] = []
        for _ in range(room_count):
            x = vf.i32()
            y = vf.i32()
            floor = vf.i32()
            n_doors = vf.i32()
            if n_doors < 0 or n_doors > _MAX_DOORS:
                return None
            doors: list[MiniDoor] = []
            for _door in range(n_doors):
                dx = vf.i32()
                dy = vf.i32()
                n_codes = vf.i32()
                if n_codes < 0 or n_codes > _MAX_CODES:
                    return None
                codes = tuple(vf.i32() for _code in range(n_codes))
                door_id = vf.i32()
                doors.append(MiniDoor(dx, dy, codes, door_id))
            rooms.append(MiniRoom(x, y, floor, tuple(doors)))
    except (EOFError, OSError):
        return None
    return MiniMap(rooms=tuple(rooms))


def mark_visited(mm: MiniMap | None, room_i: int) -> None:
    if mm is None or not (0 <= room_i < len(mm.rooms)):
        return
    mm.rooms[room_i].has_visited = -1


def _apply_visited(mm: MiniMap, visited) -> None:
    if not visited or len(visited) != len(mm.rooms):
        return
    for room, byte in zip(mm.rooms, visited):
        room.has_visited = -1 if int(byte) != 0 else 0


def attach_minimap(demo, visited=None) -> MiniMap | None:
    """Load the sibling .mni when this map is a dungeon. Mark the current room."""
    game_map = demo.game_map
    mm = None
    if getattr(game_map, "isDungeon", 0) != 0:
        path = _mni_path(game_map)
        if path is not None:
            mm = load_minimap(path, len(game_map.room))
    if mm is not None:
        _apply_visited(mm, visited)
        mark_visited(mm, int(getattr(demo, "hero_room", 0) or 0))
    demo.minimap = mm
    events.minimap = mm
    return mm


def visited_bytes(mm: MiniMap) -> list[int]:
    """FB save writes hasVisited as a byte. -1 on disk is 0xFF."""
    return [255 if room.has_visited else 0 for room in mm.rooms]


def size_x(mm: MiniMap, game_map) -> int:
    acc = 0
    rooms = game_map.room
    for i, mroom in enumerate(mm.rooms):
        if mroom.floor != mm.floor or i >= len(rooms):
            continue
        combine = rooms[i].x + mroom.x
        if combine > acc:
            acc = combine
    return acc


def size_y(mm: MiniMap, game_map) -> int:
    acc = 0
    rooms = game_map.room
    for i, mroom in enumerate(mm.rooms):
        if mroom.floor != mm.floor or i >= len(rooms):
            continue
        combine = rooms[i].y + mroom.y
        if combine > acc:
            acc = combine
    return acc


def top_floor(mm: MiniMap) -> int:
    if not mm.rooms:
        return 0
    return max(room.floor for room in mm.rooms)


def bottom_floor(mm: MiniMap) -> int:
    if not mm.rooms:
        return 0
    return min(room.floor for room in mm.rooms)


def center_on_room(mm: MiniMap, game_map, room_i: int) -> None:
    if not (0 <= room_i < len(mm.rooms)) or room_i >= len(game_map.room):
        return
    mroom = mm.rooms[room_i]
    groom = game_map.room[room_i]
    mm.camera_x = (mroom.x + (groom.x >> 1)) - 160
    mm.camera_y = (mroom.y + (groom.y >> 1)) - 80
    mm.floor = mroom.floor
    mm.focus = room_i


def update_minimap_cam(mm: MiniMap, game_map) -> None:
    """FB LLMiniMap_UpdateCam. A floor smaller than the view pins the camera at 0."""
    limit_x = size_x(mm, game_map) - VIEW_W
    limit_y = size_y(mm, game_map) - VIEW_H
    if mm.camera_x > limit_x:
        mm.camera_x = limit_x
    if mm.camera_x < 0:
        mm.camera_x = 0
    if mm.camera_y > limit_y:
        mm.camera_y = limit_y
    if mm.camera_y < 0:
        mm.camera_y = 0


def pan_minimap(mm: MiniMap, now: float, up, right, down, left) -> None:
    """FB handle_MiniMap. All four arrows can move in the same tick."""
    if now > mm.move_delay:
        if up:
            mm.camera_y -= 1
        if right:
            mm.camera_x += 1
        if down:
            mm.camera_y += 1
        if left:
            mm.camera_x -= 1
        mm.move_delay = now + PAN_DELAY


def step_floor(mm: MiniMap, delta: int) -> None:
    """FB [ / ]. One floor per press, including numbers that have no rooms."""
    if delta < 0 and mm.floor > bottom_floor(mm):
        mm.floor -= 1
    elif delta > 0 and mm.floor < top_floor(mm):
        mm.floor += 1


def open_minimap(mm: MiniMap, game_map, room_i: int) -> None:
    mm.open = True
    mm.focus = room_i
    center_on_room(mm, game_map, room_i)
    update_minimap_cam(mm, game_map)


def close_minimap(mm: MiniMap, room_i: int) -> None:
    mm.open = False
    if 0 <= room_i < len(mm.rooms):
        mm.floor = mm.rooms[room_i].floor


def _happen(code: int) -> int:
    if code < 0 or code >= len(events.now):
        return 0
    return -1 if events.now[code] != 0 else 0


def door_color(door: MiniDoor) -> int | None:
    """Palette index for a 3x3 door marker, or None when this id is not drawn."""
    if not door.codes:
        if door.id == DOOR_OPEN:
            return 36
        if door.id == DOOR_STAIR:
            return 170
        return None
    achieved = -1
    for code in door.codes:
        if code != -1:
            achieved &= _happen(code)
        else:
            achieved = 0
    if achieved != 0:
        return 36
    if door.id == DOOR_LOCKED:
        return 15
    if door.id == DOOR_BARRED:
        return 245
    if door.id == DOOR_FKEYLOCKED:
        return 27
    return None


def _fb_str(n: int) -> str:
    """FB Str() keeps a column for the sign, so positive numbers lead with a space."""
    if n < 0:
        return str(n)
    return " " + str(n)


def floor_label(floor: int) -> str:
    if floor > -1:
        return "F" + _fb_str(floor + 1)
    return "B" + _fb_str(-floor)


def _palette_color(palette, index: int, dark: int) -> tuple[int, int, int]:
    colors = getattr(palette, "colors", None) or ()
    if 0 <= index < len(colors):
        rgb = colors[index]
    else:
        rgb = (0, 0, 0)
    if dark <= 0:
        return rgb
    brightness = (5.0 - (dark * 0.66)) / 5.0
    if brightness <= 0:
        return (0, 0, 0)
    if brightness >= 1:
        return rgb
    return tuple(int(channel * brightness) for channel in rgb)


def _advance_pulse(mm: MiniMap, now: float) -> None:
    if mm.pulse_timer == 0:
        mm.pulse_i += 1
        if mm.pulse_i >= len(PULSE):
            mm.pulse_i = 0
        mm.pulse_timer = now + PULSE_DELAY
    if now > mm.pulse_timer:
        mm.pulse_timer = 0


def blit_minimap(canvas, demo, now: float) -> None:
    """FB minimap_Blit. The view is y 20..179. Name and floor labels sit outside it."""
    from lynn.gfx.menu import graphicalString

    mm = demo.minimap
    if mm is None:
        return
    game_map = demo.game_map
    palette = demo.palette
    dark = int(getattr(events, "dark", 0) or 0)
    canvas.fill(_palette_color(palette, 0, dark))
    menu = demo.menu
    name = getattr(game_map, "dungeonName", "") or ""
    if menu is not None:
        graphicalString(canvas, menu, name, 160 - (len(name) << 2), 2)

    span_x = size_x(mm, game_map)
    span_y = size_y(mm, game_map)
    gx = ((VIEW_W - span_x) >> 1) if span_x < VIEW_W else 0
    gy = ((VIEW_H - span_y) >> 1) if span_y < VIEW_H else 0
    pulse = PULSE[mm.pulse_i % len(PULSE)]
    pulsed = False
    canvas.set_clip(pygame.Rect(VIEW_X, VIEW_Y, VIEW_W, VIEW_H))
    try:
        for i, mroom in enumerate(mm.rooms):
            if not mroom.has_visited or mroom.floor != mm.floor:
                continue
            if i >= len(game_map.room):
                continue
            groom = game_map.room[i]
            if groom.x <= 0 or groom.y <= 0:
                continue
            room_x = gx + mroom.x - mm.camera_x
            room_y = gy + mroom.y + VIEW_Y - mm.camera_y
            rect = pygame.Rect(room_x, room_y, groom.x, groom.y)
            if i == mm.focus:
                color = pulse
                pulsed = True
            else:
                color = 36
            canvas.fill(_palette_color(palette, color, dark), rect)
            pygame.draw.rect(canvas, _palette_color(palette, 15, dark), rect, 1)
            for door in mroom.doors:
                marker = door_color(door)
                if marker is None:
                    continue
                door_x = door.x + room_x
                door_y = door.y + room_y
                canvas.fill(
                    _palette_color(palette, marker, dark),
                    pygame.Rect(door_x - 1, door_y - 1, 3, 3),
                )
    finally:
        canvas.set_clip(None)
    if pulsed:
        _advance_pulse(mm, now)
    if menu is None:
        return
    label = floor_label(mm.floor)
    graphicalString(canvas, menu, "Floor dn: [", 8, 182)
    graphicalString(canvas, menu, label, 160 - (len(label) << 2), 182)
    graphicalString(canvas, menu, "Floor up: ]", 224, 182)
