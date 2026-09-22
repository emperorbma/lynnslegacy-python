"""FB `Timer` — wall clock in seconds. Assign each frame from time.perf_counter()."""

timer = 0.0

# 60 Hz vs walk_speed 0.003 (swimsuit) is ~6 px/frame; fly_speed 0.004 is ~4.
MAX_TIMED_STEPS = 8
# Drop debt older than two 60 Hz frames so a pause/attack/seq does not dump 8 px.
MAX_CATCHUP_S = 1.0 / 30.0


def pop_due(hold: float, speed: float, cap: int | None = None) -> tuple[int, float]:
    """How many FB 1px intervals are due at `timer`, keeping leftover time.

    hold == 0 means due immediately (FB walk_hold = 0). Returns (steps, new_hold).
    Do not assign hold = timer after a move — that drops the remainder and
    caps motion at one pixel per display frame. If hold is more than
    MAX_CATCHUP_S behind (menu, sequence, enemy pause), resync instead of bursting.
    """
    if speed <= 0:
        speed = 0.009
    now = timer
    if hold == 0 or now - hold > MAX_CATCHUP_S:
        hold = now
    n = 0
    limit = MAX_TIMED_STEPS if cap is None else cap
    while now >= hold and n < limit:
        n += 1
        hold += speed
    return n, hold
