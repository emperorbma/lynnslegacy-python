import struct
from pathlib import Path

import pytest

from lynn.gfx.image import LLSystem_ImageLoad

SPR_PATH = Path(__file__).resolve().parents[1] / "data" / "pictures" / "char" / "lynn24.spr"
COL_PATH = SPR_PATH.with_suffix(".col")


pytestmark = pytest.mark.skipif(not SPR_PATH.is_file(), reason="data/pictures/char/lynn24.spr missing")


def test_lynn24_header():
    img = LLSystem_ImageLoad(str(SPR_PATH))
    assert img.x == 16
    assert img.y == 24
    assert img.frames == 32
    assert img.arraysize == 194
    assert len(img.frame) == img.frames
    # 16-byte header + frames * arraysize shorts
    x, y, arraysize, frames = struct.unpack("<iiii", SPR_PATH.read_bytes()[:16])
    assert SPR_PATH.stat().st_size == 16 + frames * arraysize * 2
    assert (x, y, arraysize, frames) == (img.x, img.y, img.arraysize, img.frames)


def test_lynn24_frame_pixels_match_get_size():
    img = LLSystem_ImageLoad(str(SPR_PATH))
    for frame in img.frame:
        assert frame.width > 0
        assert frame.height > 0
        assert len(frame.pixels) == frame.width * frame.height


def test_lynn24_index_zero_present():
    img = LLSystem_ImageLoad(str(SPR_PATH))
    assert 0 in img.frame[0].pixels


def test_lynn24_has_no_col_sidecar():
    # Original walk sprite has no .col; hitboxes come from lynn.xml perimeter.
    assert not COL_PATH.is_file()
    img = LLSystem_ImageLoad(str(SPR_PATH))
    assert all(shell.faces == 0 for shell in img.frame)
