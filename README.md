# Lynn's Legacy (Python)

Faithful gameplay port of *Lynn's Legacy* from FreeBASIC to Python / pygame-ce.

This is not a rewrite and not a map-editor port. Function names, field names, and binary layouts follow the original engine.

## License

Public domain ([Unlicense](http://unlicense.org/)), same as the original FreeBASIC game and the LÖVE port. See `LICENSE`.

Machine-local source-tree paths and credentials are not stored in this repository.

## Setup

```text
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Runtime data lives in `data/` (copied from the Lua tree: uncompressed maps, sprites, objects, sounds, music).

## Run

Double-click `run.bat`, or from the project root:

```text
run.bat                      objects PoC (forest_fall overworld)
run.bat map                  forest_fall tiles only
run.bat map valley           another map (stem, file, or path)
run.bat objects inhouse
run.bat palette              256-color ramp + lynn24.spr
run.bat test                 pytest (same as python -m lynn test)
run.bat test --map valley    demo/map tests against that map
.\.venv\Scripts\python.exe -m lynn [objects|map|palette|test] [map]
```

Keys:

- Arrow keys / WASD — walk Lynn (`objects` mode) or pan camera (`map` mode)
- `[` `]` or PageUp / PageDown — previous / next room
- Esc — pause menu (`objects`); quit (`map` / `palette`)
- Enter / Space — confirm pause-menu slot; Space also actions objects (sapling)
- Ctrl — swing sapling / current weapon
- F11 / Alt+Enter — toggle fullscreen
- F12 — cycle integer scale (fit, then 1x–6x)

Default map is `data/map/forest_fall.map` (chapter 1 overworld; `title.map` teles here). `title.map` is the boot/menu sequence. `island3` is a later island state (`run.bat objects island3`).

## Porting conventions

- Keep FreeBASIC names (`enemy_main`, `__walk`, `x_origin`).
- `TRUE = -1`, `FALSE = 0`. Compare with `!= 0` / `== 0`.
- Use `iif(cond, a, b)` (real ternary). Do not use Python truthiness on engine integers.
- 0-based lists. Preserve FB tile-array padding (`x * (y + 1) + 1`).
- Wall-clock `timer` for gameplay (`time.perf_counter()`), not frame `dt`.
- When Lua comments say “rewritten” / “FIXME”, read the FreeBASIC file.

## Current milestone

Lynn walks `forest_fall` (arrows/WASD, tile collision, camera follow). Same-map room strips warp instantly. `run.bat map` is tiles-only free-cam.
