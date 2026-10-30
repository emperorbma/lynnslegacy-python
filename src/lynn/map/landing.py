"""Nudge Lynn off bad tele/entry landings.

Map data sometimes places dx/dy or an entry on top of another tele pad
(Ignia growl-chest north → r17) or a visible object (maceget return sits
inside a walk-through static rock). Without room-change fade, those reads
as a bounce or as Lynn stuck overlapping scenery until the player spams
out. Slide to the nearest clear pixel after a hop.
"""

from __future__ import annotations

from lynn.map.collision import check_bounds, check_teleports
from lynn.object.char import CharType


_MAX_RADIUS = 48


def _object_overlap(hero: CharType, x: float, y: float, others) -> bool:
    if not others:
        return False
    hb = (x, y, hero.perimeter_x, hero.perimeter_y)
    for other in others:
        if other is None or other is hero:
            continue
        if int(getattr(other, "invisible", 0) or 0) != 0:
            continue
        ob = (
            other.coords_x,
            other.coords_y,
            other.perimeter_x or 16,
            other.perimeter_y or 16,
        )
        if check_bounds(hb, ob) == 0:
            return True
    return False


def _tele_overlap(hero: CharType, x: float, y: float, room) -> bool:
    if room is None or not getattr(room, "teleport", None):
        return False
    ox, oy = hero.coords_x, hero.coords_y
    hero.coords_x = x
    hero.coords_y = y
    hit = check_teleports(hero, room.teleport, room.teleports)
    hero.coords_x = ox
    hero.coords_y = oy
    return hit != -1


def _blocked(hero: CharType, x: float, y: float, room, others, clear_teles: bool) -> bool:
    if x < 0 or y < 0:
        return True
    if _object_overlap(hero, x, y, others):
        return True
    if clear_teles and _tele_overlap(hero, x, y, room):
        return True
    return False


def resolve_landing(
    hero: CharType | None,
    room=None,
    others=None,
    *,
    clear_teles: bool = True,
    max_radius: int = _MAX_RADIUS,
) -> bool:
    """Move hero to the nearest pixel that clears object (and tele) overlaps.

    Returns True if the hero was nudged. No-op when already clear or when no
    clear spot exists inside max_radius.
    """
    if hero is None:
        return False
    x0 = float(hero.coords_x)
    y0 = float(hero.coords_y)
    if not _blocked(hero, x0, y0, room, others, clear_teles):
        return False
    for radius in range(1, max_radius + 1):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                x = x0 + dx
                y = y0 + dy
                if _blocked(hero, x, y, room, others, clear_teles):
                    continue
                hero.coords_x = x
                hero.coords_y = y
                return True
    return False
