# Lynn's Legacy (Python)

Faithful gameplay port of *Lynn's Legacy* from FreeBASIC to Python / pygame-ce.

Original project: [https://sourceforge.net/projects/lynn/](https://sourceforge.net/projects/lynn/)

This is not a rewrite and not a map-editor port. Function names, field names, and binary layouts follow the original engine.

## License

Public domain ([Unlicense](http://unlicense.org/)), same as the original FreeBASIC game and the LÖVE port. See `LICENSE`.

Machine-local source-tree paths and credentials are not stored in this repository.

## Setup

Windows:

```text
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Unix:

```text
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Runtime data lives in `data/` (uncompressed maps, sprites, objects, sounds, music).

## Run

Double-click `run.bat` (Windows) or `./run.sh` (Unix), or from the project root:

```text
run.bat / ./run.sh                      splash, then title (Begin / Continue / Quit)
run.bat / ./run.sh objects forest_fall  skip title, walk the overworld
run.bat / ./run.sh map                  forest_fall tiles only
run.bat / ./run.sh map valley           another map (stem, file, or path)
run.bat / ./run.sh objects inhouse      interior map
run.bat / ./run.sh palette              256-color ramp + lynn24.spr
run.bat / ./run.sh test                 pytest (same as python -m lynn test; silent audio)
run.bat / ./run.sh test --map valley    demo/map tests against that map
run.bat / ./run.sh config               key setup (writes data/controls.xml and ll.ini)
run.bat / ./run.sh audio                live sound check (title.it); Esc quits
run.bat / ./run.sh --save forest        debug: local example tests/fixtures/test_example_forest.sav
run.bat / ./run.sh --save 1             debug: live slot ll_save1.sav (skips splash/title)
python -m lynn [objects|map|palette|audio|config|test] [map] [--save spec]
```

Keys:

- Movement — `data/controls.xml` (shipped default: WASD). `run.bat config` / `./run.sh config` to rebind
- Arrow keys — pause menu and title Begin/Continue/Quit
- Space — action (talk, pickup, advance text); rebound in config
- Enter — confirm pause slot or Yes/No
- Left / Right — Yes/No
- Ctrl — swing current weapon; rebound in config
- Esc — pause (`objects`); quit (`map` / `palette` / `config` saves)
- `[` `]` or PageUp / PageDown — previous / next room
- F11 / Alt+Enter — toggle fullscreen
- F12 — cycle integer scale (fit, then 1x–6x)

Window close quits. Default boot is the splash card, then `data/map/title.map` (Begin / Continue / Quit). Continue reads `ll_save1.sav`–`ll_save4.sav` next to `run.bat` / `run.sh`. Pause → Title returns to that menu. `data/map/forest_fall.map` is chapter 1 overworld (`run.bat objects forest_fall` / `./run.sh objects forest_fall`). `island3` is a later island state (`run.bat objects island3` / `./run.sh objects island3`).

## Porting conventions

- Keep FreeBASIC names (`enemy_main`, `__walk`, `x_origin`).
- `TRUE = -1`, `FALSE = 0`. Compare with `!= 0` / `== 0`.
- Use `iif(cond, a, b)` (real ternary). Do not use Python truthiness on engine integers.
- 0-based lists. Preserve FB tile-array padding (`x * (y + 1) + 1`).
- Wall-clock `timer` for gameplay (`time.perf_counter()`), not frame `dt`.
- When Lua comments say “rewritten” / “FIXME”, read the FreeBASIC file.

## Current milestone

Chapter 1 overworld is playable: walk, tile and entity collision, camera, HUD, pause, sapling pickup and swing, contact damage, roamers and copters, signs and NPC talk (including shops), save points, loot, same-map room warps, and map-change doors (houses). Leaving a room respawns its enemies; happen flags keep unique pickups gone.

Room `.it` music plays through pygame-ce `mixer.music` (no extra library). Title boot starts `title.it`; map changes start the dest room song.

Not started: room-change fade.
