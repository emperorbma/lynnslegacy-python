#!/usr/bin/env python3
"""Compare shipped 1.1 reference assets against this tree.

Usage:
  tools/ref_game/fetch.sh
  python tools/ref_game/compare_assets.py
"""

from __future__ import annotations

import hashlib
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = Path(__import__("os").environ.get("REF_GAME_DIR", ROOT / "ref/ll-1.1-linux"))

# Visual / text path that must match the distributed build.
GOLDEN = (
    "data/palette/ll.pal",
    "data/pictures/textbox.spr",
    "data/pictures/llfont.spr",
    "data/pictures/emptybox.spr",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def zlib_unwrap(blob: bytes) -> bytes:
    """FB zLib_SaveFile layout: 'ZLIB' + i32 uncomp + i32 comp + payload."""
    if len(blob) < 12 or blob[:4] != b"ZLIB":
        raise ValueError("not a ZLIB-wrapped Lynn blob")
    uncomp, comp = struct.unpack_from("<ii", blob, 4)
    payload = blob[12 : 12 + comp]
    raw = zlib.decompress(payload)
    if len(raw) != uncomp:
        raise ValueError(f"size mismatch: got {len(raw)} expected {uncomp}")
    return raw


def main() -> int:
    if not (REF / ".ref_game_ready").is_file():
        print(f"missing reference tree at {REF}; run tools/ref_game/fetch.sh", file=sys.stderr)
        return 2

    print(f"ref:  {REF}")
    print(f"repo: {ROOT}")
    failed = 0

    print("\n== golden visual assets ==")
    for rel in GOLDEN:
        a, b = ROOT / rel, REF / rel
        if not b.is_file():
            print(f"MISS  {rel} (not in ref)")
            failed += 1
            continue
        same = a.read_bytes() == b.read_bytes()
        mark = "OK  " if same else "DIFF"
        if not same:
            failed += 1
        print(f"{mark}  {rel}  repo={sha256(a)[:12]} ref={sha256(b)[:12]}")

    print("\n== map payloads (repo uncompressed vs ref ZLIB body) ==")
    map_dir = REF / "data/map"
    checked = 0
    for ref_map in sorted(map_dir.glob("*.map")):
        rel = ref_map.relative_to(REF)
        repo_map = ROOT / rel
        if not repo_map.is_file():
            print(f"MISS  {rel}")
            failed += 1
            continue
        blob = ref_map.read_bytes()
        if blob[:4] != b"ZLIB":
            print(f"SKIP  {rel} (ref not ZLIB)")
            continue
        try:
            raw = zlib_unwrap(blob)
        except (ValueError, zlib.error) as exc:
            print(f"FAIL  {rel} decompress: {exc}")
            failed += 1
            continue
        repo_raw = repo_map.read_bytes()
        same = raw == repo_raw
        mark = "OK  " if same else "DIFF"
        note = f"raw={len(raw)} repo={len(repo_raw)}"
        if not same:
            failed += 1
            if len(raw) == len(repo_raw):
                for i, (x, y) in enumerate(zip(repo_raw, raw)):
                    if x != y:
                        snippet = repo_raw[max(0, i - 4) : i + 20]
                        note += f" first@{i} {snippet!r}"
                        break
            else:
                note += " size mismatch"
        print(f"{mark}  {rel}  {note}")
        checked += 1

    print(f"\nmaps checked: {checked}")
    if failed:
        print(f"mismatches: {failed}")
        return 1
    print("all compared paths match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
