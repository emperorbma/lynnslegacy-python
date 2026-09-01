"""XML <func> / <block_macro> → callable registry. Unknown names stay (return 0)."""

from __future__ import annotations

from collections.abc import Callable

from lynn.object.char import CharType

Func = Callable[[CharType], int]

BLOCK_MACROS: dict[str, tuple[str, ...]] = {
    "dead_block": (
        "__make_dead",
        "__active_anim_dead",
        "__dead_animate",
        "__cripple",
        "__active_anim_0",
        "__infinity",
    ),
    "dead_drop_block": (
        "__make_dead",
        "__active_anim_dead",
        "__dead_animate",
        "__cripple",
        "__drop",
        "__active_anim_0",
        "__infinity",
    ),
    "fire_block": (
        "__do_flyback",
        "__second_pause",
        "__return_idle",
    ),
    "ice_block": (
        "__second_pause",
        "__second_pause",
        "__return_idle",
    ),
}

FUNC_REGISTRY: dict[str, Func] = {}
MISSING_FUNCS: set[str] = set()


def __noop(this: CharType) -> int:
    return 0


def lookup_func(name: str) -> Func:
    func = FUNC_REGISTRY.get(name)
    if func is None:
        MISSING_FUNCS.add(name)
        return __noop
    return func


def register_func(name: str, func: Func) -> None:
    FUNC_REGISTRY[name] = func
