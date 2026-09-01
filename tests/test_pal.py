from pathlib import Path

import pytest

from lynn.gfx.palette import PALETTE_BYTES, PALETTE_SIZE, load_pal

PAL_PATH = Path(__file__).resolve().parents[1] / "data" / "palette" / "ll.pal"


pytestmark = pytest.mark.skipif(not PAL_PATH.is_file(), reason="data/palette/ll.pal missing")


def test_load_pal_has_256_colors():
    pal = load_pal(PAL_PATH)
    assert len(pal.raw) == PALETTE_BYTES
    assert len(pal.master) == PALETTE_SIZE
    assert len(pal.colors) == PALETTE_SIZE
    assert len(pal.vga6) == PALETTE_SIZE


def test_load_pal_bgr_bytes_in_range():
    pal = load_pal(PAL_PATH)
    for r, g, b in pal.master:
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255
    for r, g, b in pal.vga6:
        assert 0 <= r <= 63
        assert 0 <= g <= 63
        assert 0 <= b <= 63


def test_load_pal_index_zero_is_dark():
    pal = load_pal(PAL_PATH)
    r, g, b = pal.master[0]
    assert r + g + b < 32
