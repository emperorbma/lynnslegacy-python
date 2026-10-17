"""FB gfx.bas load_pal and the palette writes in object--gfx_palette.bas.

.pal is 768 bytes, 256 colors x 3. The file order is B, G, R. FreeBASIC
stores Rgb(byte0>>2, byte1>>2, byte2>>2), a 6-bit DAC. This port draws
the 8-bit file bytes so pygame matches that brightness. Ramp math that
FreeBASIC writes as 0-255 stays in colors[]. A 6-bit Rgb() result is
shown as value<<2 so it sits on the same scale.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from lynn.paths import resolve_data_path


PALETTE_SIZE = 256
PALETTE_BYTES = PALETTE_SIZE * 3


def _clamp_chan(value: float) -> int:
    n = int(round(value))
    if n < 0:
        return 0
    if n > 255:
        return 255
    return n


@dataclass
class LLPalette:
    """master = loaded 8-bit RGB (FB display.pal). colors = what Palette last wrote."""

    master: list[tuple[int, int, int]] = field(default_factory=list)
    colors: list[tuple[int, int, int]] = field(default_factory=list)
    vga6: list[tuple[int, int, int]] = field(default_factory=list)
    raw: bytes = b""
    epoch: int = 0

    def touch(self) -> None:
        """Sprites are baked RGBA. Draw rebakes when this changes."""
        self.epoch += 1

    def ensure_colors(self) -> None:
        if len(self.colors) < PALETTE_SIZE:
            self.colors.extend([(0, 0, 0)] * (PALETTE_SIZE - len(self.colors)))
        elif len(self.colors) > PALETTE_SIZE:
            del self.colors[PALETTE_SIZE:]

    def reset_to_master(self) -> None:
        self.restore_master()

    def restore_master(self) -> None:
        """FB Palette Using display.pal. Dark stays a separate overlay."""
        if list(self.colors) == list(self.master):
            return
        self.colors = list(self.master)
        self.touch()

    def pygame_palette(self) -> list[tuple[int, int, int]]:
        cols = list(self.colors)
        if len(cols) < PALETTE_SIZE:
            cols.extend([(0, 0, 0)] * (PALETTE_SIZE - len(cols)))
        return cols[:PALETTE_SIZE]

    def color_off(self) -> None:
        """FB __color_off: Palette index, 0 for every entry."""
        self.colors = [(0, 0, 0)] * PALETTE_SIZE
        self.touch()

    def black_text_on(self) -> None:
        """FB __black_text_on: index 247 from display.pal, each channel << 2.

        display.pal is 6-bit. In this 8-bit buffer that is master with the
        low two bits cleared. It does not read the faded working color.
        """
        self.ensure_colors()
        if len(self.master) <= 247:
            return
        r, g, b = self.master[247]
        self.colors[247] = ((int(r) >> 2) << 2, (int(g) >> 2) << 2, (int(b) >> 2) << 2)
        self.touch()

    def red_tint(self) -> None:
        """FB __red_tint: subtract 64 from the 6-bit red and green of display.pal.

        Those channels are 0-63, so both clamp to 0. Blue is kept. The
        commented-out Shl 2 is not in the live function, so this is not a
        64-count darken of the 8-bit color.
        """
        self.ensure_colors()
        out: list[tuple[int, int, int]] = []
        for i in range(PALETTE_SIZE):
            src = self.master[i] if i < len(self.master) else (0, 0, 0)
            out.append((0, 0, (int(src[2]) >> 2) << 2))
        self.colors = out
        self.touch()

    def write_fade_up(self, fade_count: int, dark: int) -> None:
        """FB __fade_up_to_color: one slice from black toward display.pal.

        Int((fade_count * (5 - dark*0.63) / 5) * (channel6 / 64)).
        channel6 is the file byte >> 2. Shown as that 6-bit value << 2.
        """
        self.ensure_colors()
        scale = fade_count * (5.0 - (dark * 0.63)) / 5.0
        out: list[tuple[int, int, int]] = []
        for i in range(PALETTE_SIZE):
            src = self.master[i] if i < len(self.master) else (0, 0, 0)
            shown = []
            for ch in src:
                dac6 = math.floor(scale * ((int(ch) >> 2) / 64.0))
                if dac6 < 0:
                    dac6 = 0
                elif dac6 > 63:
                    dac6 = 63
                shown.append(dac6 << 2)
            out.append((shown[0], shown[1], shown[2]))
        self.colors = out
        self.touch()


class _ChanRamp:
    """FB static col_Get / col_Store / col_Inc for one palette function."""

    def __init__(self) -> None:
        self.ready = 0
        self.store: list[list[float]] = []
        self.inc: list[list[float]] = []

    def reset(self) -> None:
        self.ready = 0
        self.store = []
        self.inc = []

    def ensure(self, pal: LLPalette, divisor: float, gray: bool) -> None:
        if self.ready:
            return
        self.store = []
        self.inc = []
        master = pal.master
        for i in range(PALETTE_SIZE):
            rgb = master[i] if i < len(master) else (0, 0, 0)
            if gray:
                c6 = ((int(rgb[0]) >> 2) + (int(rgb[1]) >> 2) + (int(rgb[2]) >> 2)) // 3
                targets = (c6 << 2, c6 << 2, c6 << 2)
            else:
                targets = tuple((int(ch) >> 2) << 2 for ch in rgb)
            self.inc.append([(255 - t) / divisor for t in targets])
            self.store.append([255.0, 255.0, 255.0])
        self.ready = 1

    def write(self, pal: LLPalette) -> None:
        pal.ensure_colors()
        for i in range(PALETTE_SIZE):
            stored = self.store[i]
            step = self.inc[i]
            pal.colors[i] = (_clamp_chan(stored[0]), _clamp_chan(stored[1]), _clamp_chan(stored[2]))
            stored[0] -= step[0]
            stored[1] -= step[1]
            stored[2] -= step[2]
        pal.touch()


_flash_gray = _ChanRamp()
_flash_down = _ChanRamp()
_fade_down = _ChanRamp()


def reset_palette_ramps() -> None:
    _flash_gray.reset()
    _flash_down.reset()
    _fade_down.reset()


def make_black_and_white(pal: LLPalette | None) -> int:
    """FB __make_black_and_white: average the 6-bit DAC, write Rgb(c, c, c).

    Rgb() stores 0-63. Shown here as c<<2 so the lock matches the ramp,
    which already ended on that 8-bit gray.
    """
    if pal is None:
        return 1
    pal.ensure_colors()
    out: list[tuple[int, int, int]] = []
    for i in range(PALETTE_SIZE):
        r, g, b = pal.colors[i]
        c = ((int(r) >> 2) + (int(g) >> 2) + (int(b) >> 2)) // 3
        shown = c << 2
        out.append((shown, shown, shown))
    pal.colors = out
    pal.touch()
    return 1


def step_flash_down_gray(pal: LLPalette | None, fade_count: int) -> tuple[int, int]:
    """One __flash_down_gray call. Sixteen 0s, then the lock returns 1.

    The 17th call still writes the last ramp step, then __make_black_and_white.
    The check reads fade_count before the increment.
    """
    if pal is not None:
        _flash_gray.ensure(pal, 16, gray=True)
        _flash_gray.write(pal)
    if fade_count == 16:
        _flash_gray.reset()
        make_black_and_white(pal)
        return 0, 1
    return fade_count + 1, 0


def step_flash_down(pal: LLPalette | None, fade_count: int) -> tuple[int, int]:
    """FB __flash_down: sixteen steps from white back to display.pal."""
    if pal is not None:
        _flash_down.ensure(pal, 16, gray=False)
        _flash_down.write(pal)
    fade_count += 1
    if fade_count == 16:
        _flash_down.reset()
        if pal is not None:
            pal.restore_master()
        return 0, 1
    return fade_count, 0


def step_fade_down_to_color(pal: LLPalette | None, fade_count: int) -> tuple[int, int]:
    """FB __fade_down_to_color: 64 steps from white, then shift_pal."""
    if pal is not None:
        _fade_down.ensure(pal, 64, gray=False)
        _fade_down.write(pal)
    fade_count += 1
    if fade_count == 64:
        _fade_down.reset()
        if pal is not None:
            pal.restore_master()
        return 0, 1
    return fade_count, 0


def load_pal(filename: str | Path, bypass_errors: int = 0) -> LLPalette:
    # Function load_pal
    path = resolve_data_path(filename)
    pal = LLPalette()
    if path is None:
        if bypass_errors == 0:
            raise FileNotFoundError(filename)
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
