# Lynn's Legacy (Python)

Faithful gameplay port of *Lynn's Legacy* from FreeBASIC to Python / pygame-ce.

Original project: [https://sourceforge.net/projects/lynn/](https://sourceforge.net/projects/lynn/)

LÖVE port: [https://github.com/gradualgames/lynnslegacy](https://github.com/gradualgames/lynnslegacy)

This is not a rewrite and not a map-editor port. Function names, field names, and binary layouts follow the original engine.

## License

Public domain ([Unlicense](http://unlicense.org/)), same as the original FreeBASIC game and the [LÖVE port](https://github.com/gradualgames/lynnslegacy). See `LICENSE`.

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

Same names as the original Windows build: double-click `ll.bat` / `./ll.sh` for the game (`ll.exe`), or `Configure LL.bat` / `./Configure LL.sh` for key setup (`Configure LL.exe`). Those call `run.bat` / `run.sh`.

Or run `run.bat` / `./run.sh` from the project root:

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
run.bat / ./run.sh credits              ending roll, then exit; Esc quits
run.bat / ./run.sh --save forest        debug: local example tests/fixtures/test_example_forest.sav
run.bat / ./run.sh --save 1             debug: live slot ll_save1.sav (skips splash/title)
python -m lynn [objects|map|palette|audio|config|credits|test] [map] [--save spec]
```

Keys:

- Movement — `data/controls.xml` (shipped default: arrow keys). `Configure LL.bat` / `./Configure LL.sh` (or `run.bat config`) to rebind
- Arrow keys — pause menu and title Begin/Continue/Quit
- Space — action (talk, pickup, advance text); rebound in config
- Enter — confirm pause slot or Yes/No
- Left / Right — Yes/No
- Ctrl — swing current weapon; rebound in config
- Esc — pause (`objects`); quit (`map` / `palette` / `config` saves / `credits`)
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

The game is playable from the title screen to the end credits. The critical path is covered by automated tests (`tests/test_critical_path.py` and `tests/test_critical_path_ending.py`): start, island, Arx, desert, Divius, the Logosta dungeon (Ferus and the dimension core), the dry world, Limbo and the seed fight, the ending cutscene, then the credit roll. As in the original, the game quits after the credits.

Implemented: walking, collisions, camera, HUD, pause menu and items (including Adrenaline Booster and Healing Symbol), weapons and outfits, shops, signs and NPC talk, save points, loot, room warps and map-change doors, enemies and bosses, scripted sequences and cutscenes, text boxes (with FreeBASIC options for no background, colour, position, auto-dismiss and Yes/No), music and sound, and the credit roll.

Fidelity: all 219 FreeBASIC object functions are registered. Known stub bodies still referenced by shipped XML: `__change_room`, `__outfit_branch`, `__black_text_on`, `__flash_down_gray`. Not started: room-change fade. Ongoing work is auditing behaviour against the FreeBASIC source; no content beyond the original is being added.

Port-only additions (not in the original): godmode (`--godmode`; F8 toggles no damage, F9 opens cheat commands), the pytest suite, and the debug tools (`--save`, `[` `]` room stepping).

Room `.it` music plays through pygame-ce `mixer.music` (no extra library). Title boot starts `title.it`; map changes start the dest room song.
