"""Special-case nudge for one bad Ignia entry.

FB places entry coords as stored. Ignia entry 8 (return from maceget.map)
sits inside a walk-through static rock, so Lynn overlaps scenery until the
player walks clear. That is tolerable in FB with a fade; with instant
enter_map it reads as a stuck embed. Only that landing is adjusted.
"""

from __future__ import annotations

from pathlib import Path

from lynn.map.collision import check_bounds
from lynn.object.char import CharType

# ignia.map entry 8 → room 14 at (248, 416); static at (256, 416) overlaps.
_IGNIA_MACE_ENTRY = 8
_MAX_RADIUS = 16


def _is_ignia(game_map) -> bool:
    name = str(getattr(game_map, "filename", "") or "").replace("\\", "/").lower()
    return Path(name).stem == "ignia"


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


def resolve_ignia_mace_return(
    hero: CharType | None,
    game_map,
    entry_i: int,
    others=None,
) -> bool:
    """If this is Ignia entry 8, nudge Lynn off overlapping room objects.

    Cheap no-op for every other map/entry. Returns True when coords changed.
    """
    if hero is None or entry_i != _IGNIA_MACE_ENTRY or not _is_ignia(game_map):
        return False
    if not others:
        return False
    x0 = float(hero.coords_x)
    y0 = float(hero.coords_y)
    if not _object_overlap(hero, x0, y0, others):
        return False
    for radius in range(1, _MAX_RADIUS + 1):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                x = x0 + dx
                y = y0 + dy
                if x < 0 or y < 0:
                    continue
                if _object_overlap(hero, x, y, others):
                    continue
                hero.coords_x = x
                hero.coords_y = y
                return True
    return False
