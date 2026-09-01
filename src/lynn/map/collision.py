"""FB matrices.bas check_bounds + engine--LL.bas check_walk / check_teleports / move_object."""

from __future__ import annotations

from lynn.constants import FALSE, TRUE
from lynn.macros import LLObject_CalculateFrame, quad_calc, testbit
from lynn.map.types import RoomType, TeleportType
from lynn.object.char import CharType

# vector_pair as (u.x, u.y, v.x, v.y) — FB matrices.bas
BoundsBox = tuple[float, float, float, float]


def check_bounds(m: BoundsBox, n: BoundsBox) -> int:
    """0 if AABBs overlap, -1 otherwise. FB matrices.bas (edge-touch is not overlap)."""
    touching_x = 0
    touching_y = 0
    if m[0] + m[2] > n[0]:
        if m[0] < (n[0] + n[2]):
            touching_x = TRUE
    if m[1] + m[3] > n[1]:
        if m[1] < n[1] + n[3]:
            touching_y = TRUE
    if touching_x and touching_y:
        return 0
    return -1


def check_teleports(
    char: CharType,
    teles: list[TeleportType],
    num_tele: int | None = None,
) -> int:
    """Index of the first tele whose AABB overlaps the char, else -1. FB engine--LL.bas."""
    origin: BoundsBox = (char.coords_x, char.coords_y, char.perimeter_x, char.perimeter_y)
    n = len(teles) if num_tele is None else min(num_tele, len(teles))
    for tele_check in range(n):
        tele = teles[tele_check]
        target: BoundsBox = (tele.x, tele.y, tele.w, tele.h)
        if check_bounds(origin, target) == 0:
            return tele_check
    return -1


def check_against_teles(o: CharType, room: RoomType) -> int:
    """FB check_against_teles: first overlapping tele, or -1.

    Same-map teles have empty to_map. Map-change teles copy to_map and to_entry
    (FB stores the dest entry index in TeleportType.to_room).
    """
    tele_i = check_teleports(o, room.teleport, room.teleports)
    if tele_i == -1:
        return -1
    tele = room.teleport[tele_i]
    if tele.to_map != "":
        o.to_map = tele.to_map
        o.to_entry = tele.to_room
    return tele_i


def check_walk(o: CharType, d: int, room: RoomType, psfing: int = 0) -> int:
    room_px = room.x << 4
    room_py = room.y << 4
    if (
        o.coords_x < 0
        or o.coords_y < 0
        or (o.coords_x + o.perimeter_x) > room_px
        or (o.coords_y + o.perimeter_y) > room_py
    ):
        return FALSE

    x_tile_2 = int(o.coords_x) >> 3
    y_tile_2 = int(o.coords_y) >> 3
    x_offset_2 = int(o.coords_x) & 7
    y_offset_2 = int(o.coords_y) & 7
    quads_x = int(o.perimeter_x) >> 3
    quads_y = int(o.perimeter_y) >> 3
    x_aligned = 0
    y_aligned = 0
    if x_offset_2 != 0:
        quads_x += 1
    else:
        x_aligned = 1
    if y_offset_2 != 0:
        quads_y += 1
    else:
        y_aligned = 1

    tile_free = TRUE
    psf_free = TRUE
    crawl_axis = quads_x if (d % 2) == 0 else quads_y

    for layer in range(3):
        if layer >= len(room.layout):
            break
        layout = room.layout[layer]
        for crawl in range(crawl_axis):
            if d == 0:
                x_opt = x_tile_2 + crawl
                y_opt = y_tile_2 - y_aligned
            elif d == 1:
                x_opt = (quads_x - 1) + x_tile_2 + x_aligned
                y_opt = y_tile_2 + crawl
            elif d == 2:
                x_opt = x_tile_2 + crawl
                y_opt = (quads_y - 1) + y_tile_2 + y_aligned
            else:
                x_opt = x_tile_2 - x_aligned
                y_opt = y_tile_2 + crawl

            t_index = ((y_opt << 3) >> 4) * room.x + ((x_opt << 3) >> 4)
            if t_index < 0 or t_index >= len(layout):
                blocked = TRUE
            else:
                tile = layout[t_index]
                bit_index = 15 - quad_calc(x_opt, y_opt)
                blocked = TRUE if testbit(tile, bit_index) != 0 else FALSE
            if blocked != 0:
                if psfing != 0:
                    psf_free = FALSE
                else:
                    tile_free = FALSE

    if psfing != 0:
        return psf_free
    return tile_free


def _frame_shell(o: CharType):
    if not o.anim or o.current_anim >= len(o.anim):
        return None
    anim = o.anim[o.current_anim]
    fi = LLObject_CalculateFrame(o)
    if fi < 0 or fi >= len(anim.frame):
        return None
    return anim.frame[fi]


def _impassable(o: CharType, face_i: int) -> int:
    shell = _frame_shell(o)
    if shell is None or shell.faces == 0:
        return int(getattr(o, "impassable", 0) or 0)
    if 0 <= face_i < len(shell.face):
        return int(shell.face[face_i].impassable)
    return int(getattr(o, "impassable", 0) or 0)


def _boxes(o: CharType, dx: float, dy: float) -> list[tuple[float, float, float, float]]:
    x = o.coords_x + dx
    y = o.coords_y + dy
    shell = _frame_shell(o)
    if shell is None or shell.faces == 0:
        return [(x, y, o.perimeter_x, o.perimeter_y)]
    ctrl = o.animControl[o.current_anim] if o.animControl else None
    x_off = ctrl.x_off if ctrl else 0
    y_off = ctrl.y_off if ctrl else 0
    boxes = []
    for face in shell.face:
        boxes.append((x + face.x - x_off, y + face.y - y_off, face.w, face.h))
    return boxes


def _overlap(a, b) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax + aw > bx and ax < bx + bw and ay + ah > by and ay < by + bh


def check_against(o: CharType, other: CharType, d: int) -> int:
    """1 if the 1px step in direction d hits an impassable other."""
    if o is other or o.num == other.num:
        return 0
    if o.dead != 0 or other.dead != 0:
        return 0
    step = ((0, -1), (1, 0), (0, 1), (-1, 0))
    dx, dy = step[d] if 0 <= d < 4 else (0, 0)
    for i, box_o in enumerate(_boxes(o, dx, dy)):
        for j, box_n in enumerate(_boxes(other, 0, 0)):
            if not _overlap(box_o, box_n):
                continue
            if _impassable(o, i) == 0 and _impassable(other, j) == 0:
                continue
            return 1
    return 0


def check_against_entities(o: CharType, d: int, others: list[CharType] | None) -> int:
    if not others:
        return 0
    for other in others:
        if check_against(o, other, d) == 1:
            return 1
    return 0


def move_object(
    o: CharType,
    room: RoomType,
    only_looking: int = 0,
    moment: float = 1,
    recurring: int = 0,
    others: list[CharType] | None = None,
) -> int:
    mx = 0
    my = 0
    psfing = TRUE if (only_looking != 0 or recurring != 0) else FALSE
    d = o.direction
    unstop_tile = o.unstoppable_by_tile != 0
    unstop_screen = o.unstoppable_by_screen != 0
    room_px = room.x << 4
    room_py = room.y << 4

    def _try(dir_id: int, screen_ok: bool, apply) -> int:
        if not (screen_ok or unstop_screen):
            return 0
        if check_walk(o, dir_id, room, psfing) == 0 and not unstop_tile:
            return 0
        if o.unstoppable_by_object == 0 and check_against_entities(o, dir_id, others) == 1:
            return 0
        if only_looking == 0:
            apply()
        return 1

    if d == 0:
        my = _try(0, o.coords_y > 0, lambda: setattr(o, "coords_y", o.coords_y - moment))
    elif d == 1:
        mx = _try(
            1,
            o.coords_x < room_px - o.perimeter_x,
            lambda: setattr(o, "coords_x", o.coords_x + moment),
        )
    elif d == 2:
        my = _try(
            2,
            o.coords_y < room_py - o.perimeter_y,
            lambda: setattr(o, "coords_y", o.coords_y + moment),
        )
    elif d == 3:
        mx = _try(3, o.coords_x > 0, lambda: setattr(o, "coords_x", o.coords_x - moment))
    elif d == 4:
        my = _try(0, o.coords_y > 0, lambda: setattr(o, "coords_y", o.coords_y - moment))
        mx = _try(3, o.coords_x > 0, lambda: setattr(o, "coords_x", o.coords_x - moment))
    elif d == 5:
        my = _try(0, o.coords_y > 0, lambda: setattr(o, "coords_y", o.coords_y - moment))
        mx = _try(
            1,
            o.coords_x < room_px - o.perimeter_x,
            lambda: setattr(o, "coords_x", o.coords_x + moment),
        )
    elif d == 6:
        my = _try(
            2,
            o.coords_y < room_py - o.perimeter_y,
            lambda: setattr(o, "coords_y", o.coords_y + moment),
        )
        mx = _try(
            1,
            o.coords_x < room_px - o.perimeter_x,
            lambda: setattr(o, "coords_x", o.coords_x + moment),
        )
    elif d == 7:
        my = _try(
            2,
            o.coords_y < room_py - o.perimeter_y,
            lambda: setattr(o, "coords_y", o.coords_y + moment),
        )
        mx = _try(3, o.coords_x > 0, lambda: setattr(o, "coords_x", o.coords_x - moment))

    return (mx << 16) | my
