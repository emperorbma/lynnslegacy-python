"""FB gfx.bas load_pal + Lua loadPalette.

.pal is 768 bytes, 256 colors x 3. Lua/Unity treat the file as BGR.
FB then >>2 for VGA 6-bit Palette Using. We keep 8-bit RGB for pygame
and a 6-bit copy for later fade math.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


PALETTE_SIZE = 256
PALETTE_BYTES = PALETTE_SIZE * 3


@dataclass
class LLPalette:
    """master = pristine 8-bit RGB; colors = working 8-bit RGB; vga6 = 0-63 RGB."""

    master: list[tuple[int, int, int]] = field(default_factory=list)
    colors: list[tuple[int, int, int]] = field(default_factory=list)
    vga6: list[tuple[int, int, int]] = field(default_factory=list)
    raw: bytes = b""

    def reset_to_master(self) -> None:
        self.colors = list(self.master)

    def pygame_palette(self) -> list[tuple[int, int, int]]:
        cols = list(self.colors)
        if len(cols) < PALETTE_SIZE:
            cols.extend([(0, 0, 0)] * (PALETTE_SIZE - len(cols)))
        return cols[:PALETTE_SIZE]


def load_pal(filename: str | Path, bypass_errors: int = 0) -> LLPalette:
    # Function load_pal
    path = Path(filename)
    pal = LLPalette()
    if not path.is_file():
        if bypass_errors == 0:
            raise FileNotFoundError(path)
        return pal

    raw = path.read_bytes()
    if len(raw) < PALETTE_BYTES:
        if bypass_errors == 0:
            raise ValueError(f"palette is empty or truncated: {path} ({len(raw)} bytes)")
        return pal

    pal.raw = raw[:PALETTE_BYTES]
    master: list[tuple[int, int, int]] = []
    vga6: list[tuple[int, int, int]] = []
    for i in range(PALETTE_SIZE):
        off = i * 3
        # Lua: local b,g,r = readByte, readByte, readByte
        b = pal.raw[off]
        g = pal.raw[off + 1]
        r = pal.raw[off + 2]
        master.append((r, g, b))
        vga6.append((r >> 2, g >> 2, b >> 2))

    pal.master = master
    pal.colors = list(master)
    pal.vga6 = vga6
    return pal
