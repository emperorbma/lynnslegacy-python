# Lynn's Legacy (Python)

Faithful gameplay port of *Lynn's Legacy* from FreeBASIC to Python / pygame-ce.

Original project: [https://sourceforge.net/projects/lynn/](https://sourceforge.net/projects/lynn/)

This is not a rewrite and not a map-editor port. Function names, field names, and binary layouts follow the original engine.

## License

Public domain ([Unlicense](http://unlicense.org/)), same as the original FreeBASIC game and the LÖVE port. See `LICENSE`.

Machine-local source-tree paths and credentials are not stored in this repository.

## Setup

```text
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Runtime data lives in `data/` (uncompressed maps, sprites, objects, sounds, music).

## Run

Double-click `run.bat`, or from the project root:

```text
run.bat                      walk Lynn (default: forest_fall)
run.bat map                  forest_fall tiles only
run.bat map valley           another map (stem, file, or path)
run.bat objects inhouse      interior map
run.bat palette              256-color ramp + lynn24.spr
run.bat test                 pytest (same as python -m lynn test)
run.bat test --map valley    demo/map tests against that map
.\.venv\Scripts\python.exe -m lynn [objects|map|palette|test] [map]
```

Keys:

- Arrow keys / WASD — walk Lynn (`objects`) or pan camera (`map`)
- Space — action (talk, pickup, advance text)
- Enter — confirm pause slot or Yes/No
- Left / Right — Yes/No
- Ctrl — swing current weapon
- Esc — pause (`objects`); quit (`map` / `palette`)
- `[` `]` or PageUp / PageDown — previous / next room
- F11 / Alt+Enter — toggle fullscreen
- F12 — cycle integer scale (fit, then 1x–6x)

Window close quits. Default map is `data/map/forest_fall.map` (chapter 1 overworld). `title.map` is the boot/menu sequence, not the overworld. `island3` is a later island state (`run.bat objects island3`).

## Porting conventions

- Keep FreeBASIC names (`enemy_main`, `__walk`, `x_origin`).
- `TRUE = -1`, `FALSE = 0`. Compare with `!= 0` / `== 0`.
- Use `iif(cond, a, b)` (real ternary). Do not use Python truthiness on engine integers.
- 0-based lists. Preserve FB tile-array padding (`x * (y + 1) + 1`).
- Wall-clock `timer` for gameplay (`time.perf_counter()`), not frame `dt`.
- When Lua comments say “rewritten” / “FIXME”, read the FreeBASIC file.

## Current milestone

Chapter 1 overworld is playable: walk, tile and entity collision, camera, HUD, pause, sapling pickup and swing, contact damage, roamers and copters, signs and NPC talk (including shops), save points, loot, same-map room warps, and map-change doors (houses). Leaving a room respawns its enemies; happen flags keep unique pickups gone.

Not started: `.it` music, title sequence, load from save, room-change fade.
