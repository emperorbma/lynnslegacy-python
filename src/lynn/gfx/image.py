"""FB engine--images.bas LLSystem_ImageLoad.

.spr is QBasic/FreeBASIC GET/PUT SCREEN 13:
  i32 x, y, arraysize, frames
  then per frame: u16 width*8, u16 height, u8[w*h], pad to arraysize*2 bytes.

Optional sidecar .col: per frame i32 faces, then faces * (x,y,w,h,strength,invincible,impassable).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

from lynn.gfx.palette import LLPalette


@dataclass
class LLSystem_FaceType:
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    strength: int = 0
    invincible: int = 0
    impassable: int = 0


@dataclass
class LLSystem_FrameShell:
    faces: int = 0
    face: list[LLSystem_FaceType] = field(default_factory=list)
    sound: int = 0
    vol: int = 0
    chan: int = 0
    uni_sound: int = 0
    pixels: bytes = b""
    width: int = 0
    height: int = 0


@dataclass
class LLSystem_ImageHeader:
    filename: str = ""
    x: int = 0
    y: int = 0
    x_off: int = 0
    y_off: int = 0
    arraysize: int = 0
    frames: int = 0
    frame: list[LLSystem_FrameShell] = field(default_factory=list)


def _kill_file_ext(path: str) -> str:
    # kfe(): strip last extension
    p = Path(path)
    if p.suffix:
        return str(p.with_suffix(""))
    return path


def LLSystem_ImageLoad(
    filename: str,
    oc: int | None = None,
    rc: int | None = None,
) -> LLSystem_ImageHeader:
    header = LLSystem_ImageHeader(filename=filename.replace("\\", "/"))
    path = Path(filename)
    if not path.is_file():
        return header

    data = path.read_bytes()
    if len(data) < 16:
        return header

    header.x, header.y, header.arraysize, header.frames = struct.unpack_from("<iiii", data, 0)
    offset = 16
    frame_stride = header.arraysize * 2

    for _ in range(header.frames):
        if offset + 4 > len(data):
            break
        width8, height = struct.unpack_from("<HH", data, offset)
        width = width8 // 8
        offset += 4
        nbytes = width * height
        raw = bytearray(data[offset : offset + nbytes])
        if oc is not None and rc is not None:
            for i, bt in enumerate(raw):
                if bt == oc:
                    raw[i] = rc
        offset += nbytes
        pad = frame_stride - (4 + nbytes)
        if pad > 0:
            offset += pad

        header.frame.append(
            LLSystem_FrameShell(
                pixels=bytes(raw),
                width=width,
                height=height,
            )
        )

    col_path = Path(_kill_file_ext(filename) + ".col")
    if col_path.is_file():
        _load_col(header, col_path.read_bytes())

    return header


def _load_col(header: LLSystem_ImageHeader, blob: bytes) -> None:
    offset = 0
    n = len(blob)
    for fi in range(header.frames):
        if offset + 4 > n:
            break
        (faces,) = struct.unpack_from("<i", blob, offset)
        offset += 4
        if fi >= len(header.frame):
            header.frame.append(LLSystem_FrameShell())
        shell = header.frame[fi]
        shell.faces = faces
        shell.face = []
        for _ in range(faces):
            if offset + 28 > n:
                break
            x, y, w, h, strength, invincible, impassable = struct.unpack_from("<iiiiiii", blob, offset)
            offset += 28
            shell.face.append(
                LLSystem_FaceType(
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    strength=strength,
                    invincible=invincible,
                    impassable=impassable,
                )
            )


def frame_surface(header: LLSystem_ImageHeader, frame_index: int, palette: LLPalette):
    """Build a 32-bit pygame surface for one frame. Index 0 is transparent.

    Paletted 8-bit surfaces plus convert() washed out to white on Windows;
    bake the LUT ourselves so SCREEN 13 indices become real RGB.
    """
    import pygame

    shell = header.frame[frame_index]
    w = header.x
    h = header.y
    pixels = shell.pixels
    lut = palette.pygame_palette()
    rgba = bytearray(w * h * 4)
    fw = min(shell.width, w)
    fh = min(shell.height, h)
    for y in range(fh):
        src_row = y * shell.width
        dst_row = y * w
        for x in range(fw):
            idx = pixels[src_row + x]
            if idx == 0:
                continue
            r, g, b = lut[idx]
            o = (dst_row + x) * 4
            rgba[o] = r
            rgba[o + 1] = g
            rgba[o + 2] = b
            rgba[o + 3] = 255
    surf = pygame.image.frombytes(bytes(rgba), (w, h), "RGBA")
    return surf.convert_alpha()


def frame_surfaces(header: LLSystem_ImageHeader, palette: LLPalette) -> list:
    return [frame_surface(header, i, palette) for i in range(header.frames)]
