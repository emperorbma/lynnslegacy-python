"""In-memory binary cursor matching FB vfile / Lua moonblob reads.

H-strings are u16 length + raw bytes (no NUL). Paths use backslashes on disk.
"""

from __future__ import annotations

import struct


class VFile:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def remaining(self) -> int:
        return len(self.data) - self.pos

    def _need(self, n: int) -> None:
        if self.pos + n > len(self.data):
            raise EOFError(f"vfile: need {n} bytes at {self.pos}, file is {len(self.data)}")

    def i32(self) -> int:
        self._need(4)
        (v,) = struct.unpack_from("<i", self.data, self.pos)
        self.pos += 4
        return v

    def u16(self) -> int:
        self._need(2)
        (v,) = struct.unpack_from("<H", self.data, self.pos)
        self.pos += 2
        return v

    def s16(self) -> int:
        self._need(2)
        (v,) = struct.unpack_from("<h", self.data, self.pos)
        self.pos += 2
        return v

    def u8(self) -> int:
        self._need(1)
        v = self.data[self.pos]
        self.pos += 1
        return v

    def f64(self) -> float:
        self._need(8)
        (v,) = struct.unpack_from("<d", self.data, self.pos)
        self.pos += 8
        return v

    def raw(self, n: int) -> bytes:
        self._need(n)
        chunk = self.data[self.pos : self.pos + n]
        self.pos += n
        return chunk

    def hstring(self) -> str:
        # VFile_Get_HString / Lua readString
        n = self.u16()
        text = self.raw(n).decode("latin-1")
        return text.replace("\\", "/")
