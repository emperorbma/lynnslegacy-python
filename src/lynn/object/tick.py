"""Minimal act_enemies inner step: run one XML func and wrap the block."""

from __future__ import annotations

from lynn.object.char import CharType


def tick_object(this: CharType) -> None:
    f = this.funcs
    if f.states == 0 or not f.func:
        return
    state = f.active_state
    if state < 0 or state >= len(f.func):
        return
    count = f.func_count[state] if state < len(f.func_count) else 0
    if count == 0:
        return
    if f.current_func[state] == count:
        f.current_func[state] = 0
    idx = f.current_func[state]
    block = f.func[state]
    if idx < 0 or idx >= len(block):
        return
    result = block[idx](this)
    f.current_func[state] = f.current_func[state] + result


def tick_objects(objs: list[CharType]) -> None:
    for obj in objs:
        tick_object(obj)
