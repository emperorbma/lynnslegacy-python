"""Dump loot, puzzles, and doors for a map — any dungeon, not just Moenia.

Use this when a chest/door/button stalls: sequences and missing XML procs
show up here. Behavior reference for "what should happen" is the shipped
original at C:\\Games\\lynn\\ll.exe (data next to it).

Examples:
  python tools/dump_dungeon.py moenia
  python tools/dump_dungeon.py forest_fall ignia gelidus
  python tools/dump_dungeon.py --all
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lynn.object.dispatch import FUNC_REGISTRY
from lynn.paths import chdir_project_root, data_root, resolve_map_path

INTERESTING = (
    "chest",
    "bluechest",
    "bluechestitem",
    "pushrock",
    "gbutton",
    "button",
    "keydoor",
    "fkeydoor",
    "bardoor",
    "gold",
    "health",
    "crate",
    "bombrock",
    "hotrock",
    "coldrock",
    "greyrock",
    "goldblock",
    "savepoint",
    "hsavepoint",
    "portal",
    "grult",
    "dyssius",
    "anger",
    "sterach",
    "divine",
    "core",
    "ferus",
    "steelstrider",
    "boss5",
    "battleseed",
    "biglarva",
)

_FUNC_TAG = re.compile(r"<func>\s*([^<]+?)\s*</func>", re.I)
_MACRO_TAG = re.compile(r"<block_macro>\s*([^<]+?)\s*</block_macro>", re.I)
_xml_cache: dict[str, str] = {}


def _stem(id_path: str) -> str:
    return Path(str(id_path).replace("\\", "/")).stem.lower()


def _interesting(id_path: str) -> bool:
    name = _stem(id_path)
    return any(name == key or name.startswith(key + "_") or name.endswith(key) for key in INTERESTING)


def _object_xml(id_path: str) -> str:
    from lynn.object.xml_load import get_object_xml

    key = id_path.replace("\\", "/").lower()
    if key not in _xml_cache:
        try:
            _xml_cache[key] = get_object_xml(id_path)
        except Exception as exc:
            _xml_cache[key] = f"<!-- load failed: {exc} -->"
    return _xml_cache[key]


def _xml_func_names(id_path: str) -> list[str]:
    text = _object_xml(id_path)
    names: list[str] = []
    for raw in _FUNC_TAG.findall(text):
        names.append("__" + raw.strip())
    for raw in _MACRO_TAG.findall(text):
        names.append(raw.strip())
    return names


def _missing_funcs(id_path: str) -> list[str]:
    missing = []
    seen: set[str] = set()
    for name in _xml_func_names(id_path):
        if name in seen:
            continue
        seen.add(name)
        if name not in FUNC_REGISTRY and not name.startswith("dead_") and not name.endswith("_block"):
            # block macros expand; skip those names, flag their inner funcs via XML only
            if name not in FUNC_REGISTRY:
                missing.append(name)
    # Macros are not in FUNC_REGISTRY; only flag real __funcs.
    return [n for n in missing if n.startswith("__")]


def _dump_seq(e, indent: str = "      ") -> None:
    for si, seq in enumerate(e.seq or []):
        print(f"{indent}seq{si} cmds={seq.commands} ent_code={seq.ent_code}")
        for ci, cmd in enumerate(seq.Command):
            for ent in cmd.ent:
                t = (ent.text or "").replace("\n", " ")[:80]
                extra = (
                    f"c{ci} ae={ent.active_ent} s={ent.ent_state} "
                    f"chap={ent.chap} jumps={ent.jump_count} "
                    f"carries={ent.carries_all} dest={ent.dest_x},{ent.dest_y}"
                )
                if t:
                    extra += " " + repr(t)
                print(indent + " ", extra)


def dump_map(stem: str) -> None:
    from lynn.map.loader import load_mapV

    path = resolve_map_path(stem)
    m = load_mapV(str(path), load_tileset=False)
    print(f"=== {path.stem} rooms={m.rooms} ===")
    any_hit = False
    map_missing: dict[str, list[str]] = {}
    for ri, room in enumerate(m.room):
        hits = []
        for ei, e in enumerate(room.enemy):
            if _interesting(e.id):
                hits.append((ei, e))
        if not hits:
            continue
        any_hit = True
        print(f" r{ri} dark={room.dark} enemies={len(room.enemy)}")
        for ei, e in hits:
            name = Path(str(e.id).replace("\\", "/")).name
            miss = _missing_funcs(e.id)
            miss_s = f" missing={miss}" if miss else ""
            if miss:
                map_missing.setdefault(name, miss)
            print(
                f"   {ei:2d} {name:22s} xy={e.x_origin:4d},{e.y_origin:4d} "
                f"chap={e.chap} seqs={len(e.seq or [])}{miss_s}"
            )
            _dump_seq(e)
    if not any_hit:
        print("  (no chests, doors, rocks, buttons, or bosses)")
    if map_missing:
        print(" missing procs on this map:")
        for name, miss in sorted(map_missing.items()):
            print(f"   {name}: {', '.join(miss)}")


def _all_map_stems() -> list[str]:
    return sorted(p.stem for p in (data_root() / "map").glob("*.map"))


def main(argv: list[str] | None = None) -> int:
    chdir_project_root()
    import lynn.object  # noqa: F401 — register XML procs

    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "maps",
        nargs="*",
        help="map stems (moenia, ignia, ...). Default: all maps with loot/puzzles.",
    )
    parser.add_argument("--all", action="store_true", help="dump every .map")
    args = parser.parse_args(argv)
    stems = list(args.maps)
    if args.all or not stems:
        stems = _all_map_stems()
    for stem in stems:
        dump_map(stem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
