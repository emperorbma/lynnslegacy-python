# Lynn's Legacy (Python)

Faithful gameplay port of *Lynn's Legacy* from FreeBASIC to Python / pygame-ce.

This is not a rewrite and not a map-editor port. Function names, field names, and binary layouts follow the original engine.

## License

Public domain ([Unlicense](http://unlicense.org/)), same as the original FreeBASIC game and the LÖVE port. See `LICENSE`.

## Source trees

| Role | Path |
|---|---|
| This project | `C:\lynn2py\lynnslegacy` |
| FreeBASIC source of truth | `C:\lynn2py\lynnslegacy-fbsrc` |
| Love2D crib (annotated 1:1) | `C:\lynn2py\lynnslegacy-lua` |
| Unity C# (types only; incomplete) | `C:\lynn2unity\lynnslegacy` |

## Setup

```text
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Runtime data lives in `data/` (copied from the Lua tree: uncompressed maps, sprites, objects, sounds, music).

## Run

Double-click `run.bat`, or from the project root:

```text
run.bat                      objects PoC (island3 + idle XML entities)
run.bat map                  island3 tiles only
run.bat map valley           another map (stem, file, or path)
run.bat objects inhouse
run.bat palette              256-color ramp + lynn24.spr
run.bat test                 pytest (same as python -m lynn test)
run.bat test --map valley    demo/map tests against that map
.\.venv\Scripts\python.exe -m lynn [objects|map|palette|test] [map]
```

Keys:

- Arrow keys / WASD — pan camera
- `[` `]` or PageUp / PageDown — previous / next room
- Esc — quit
- F11 / Alt+Enter — toggle fullscreen
- F12 — cycle integer scale (fit, then 1x–6x)

The window loads `data/map/island3.map` (first real map). `title.map` is the boot/loading sequence, not a place.

## Porting conventions

- Keep FreeBASIC names (`enemy_main`, `__walk`, `x_origin`).
- `TRUE = -1`, `FALSE = 0`. Compare with `!= 0` / `== 0`.
- Use `iif(cond, a, b)` (real ternary). Do not use Python truthiness on engine integers.
- 0-based lists. Preserve FB tile-array padding (`x * (y + 1) + 1`).
- Wall-clock `timer` for gameplay (`time.perf_counter()`), not frame `dt`.
- When Lua comments say “rewritten” / “FIXME”, read the FreeBASIC file.

## Current milestone

`island3.map` tiles plus idle XML objects (moths and red teles at spawn). Layer 2 still draws over entities, like the original.
