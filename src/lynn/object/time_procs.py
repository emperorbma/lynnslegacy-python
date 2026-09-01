"""FB object_time.bas — __return_idle so idle_animate can loop."""

from __future__ import annotations

from lynn.object.char import CharType
from lynn.object.dispatch import register_func


def __return_idle(this: CharType) -> int:
    this.funcs.current_func[this.funcs.active_state] = 0
    this.funcs.active_state = 0
    this.funcs.current_func[this.funcs.active_state] = 0
    return 0


register_func("__return_idle", __return_idle)
