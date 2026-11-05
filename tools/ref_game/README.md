# Reference game (Lynn's Legacy 1.1)

Use the SourceForge **Linux Full** build for side-by-side gameplay and asset comparison against this port.

## Fetch

```bash
tools/ref_game/fetch.sh
```

Downloads `ll-linux.7z` and FMOD 3.75 into `ref/cache/`, extracts to `ref/ll-1.1-linux/` (gitignored).

## Play (desktop)

```bash
tools/ref_game/run.sh
```

Runtime needs:

- 32-bit (`i386`) libs: `libc6`, `libX11`, `libXext`, `libXpm`, `libXrandr`, `libXrender`, `libncurses5`
- A real `DISPLAY` (desktop or Xephyr). Headless Xvfb currently segfaults in this binary after `title.map` load (null deref at `+0x58`).
- `/dev/dsp` for FMOD 3.75 audio (`osspd` + Pulse is typical)

The binary expects the **ZLIB-wrapped** maps that ship in the archive. Pointing it at this repo’s uncompressed `data/map` makes it abort (`crashlog.txt`: `Byte 0 = 18`).

## Asset / map compare

```bash
python tools/ref_game/compare_assets.py
```

Checks palette / textbox / font against the distributed files, and decompresses each ref `*.map` to compare the raw payload with this tree’s uncompressed maps.

## Notes

- `ll.pal`, `textbox.spr`, and `llfont.spr` match this tree (white ink on gold textbox).
- Windows 1.1 (`ll.exe` + `bass.dll`) is the same content pack; Wine hits the same null deref under Xvfb here.
