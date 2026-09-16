"""Convert Lynn save files both ways: original ZLIB <-> debug JSON.

Game slots stay ZLIB (ll.exe can load them). JSON is for inspection.

Examples:
  python tools/convert_save.py ll_save1.sav
  python tools/convert_save.py ll_save1.sav --to json -o ll_save1.json
  python tools/convert_save.py ll_save1.json --to zlib -o ll_save1.sav
  python tools/convert_save.py ll_save1-orig.sav --to json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lynn.object.save import convert_save, detect_save_format
from lynn.paths import chdir_project_root, project_root


def _resolve(spec: str) -> Path:
    p = Path(spec)
    if p.is_file():
        return p
    rooted = project_root() / spec
    if rooted.is_file():
        return rooted
    raise FileNotFoundError(spec)


def main(argv: list[str] | None = None) -> int:
    chdir_project_root()
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("saves", nargs="+", help="save path(s) or ll_saveN.sav")
    parser.add_argument(
        "--to",
        choices=("json", "zlib", "sav"),
        help="output format (default: the other format)",
    )
    parser.add_argument("-o", "--output", help="output path (only with a single input)")
    args = parser.parse_args(argv)
    if args.output and len(args.saves) != 1:
        parser.error("-o can only be used with one input file")
    for spec in args.saves:
        src = _resolve(spec)
        src_fmt = detect_save_format(src)
        dest = convert_save(src, dest=args.output, to=args.to)
        print(f"{src.name} ({src_fmt}) -> {dest}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
