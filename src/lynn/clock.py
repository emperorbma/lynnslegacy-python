"""FB `Timer` — seconds. The play loop steps it at the original engine rate."""

timer = 0.0

# 60 Hz vs walk_speed 0.003 (swimsuit) is ~6 px/frame; fly_speed 0.004 is ~4.
MAX_TIMED_STEPS = 8
# Drop debt older than two 60 Hz frames so a pause/attack/seq does not dump 8 px.
MAX_CATCHUP_S = 1.0 / 30.0

# FB ll.bas draws every pass and Sleeps 1 only when handle_fps says the
# loop is above ~200 fps (fps_hold = frames * 64, sampled every 1/64s).
# A two-phase hold (step, then clear on the next pass) therefore waits
# about one 5 ms pass on top of its delay. One 60 Hz call makes that
# extra pass 16 ms, which is why a 0.004 s sword step crawls.
LOGIC_HZ = 200
LOGIC_DT = 1.0 / LOGIC_HZ
MAX_LOGIC_STEPS = 8

_last_real: float | None = None
_sim = 0.0
_accum = 0.0


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


def reset_logic_clock() -> None:
    """Test hook. The play loop does not call this."""
    global _last_real, _sim, _accum
    _last_real = None
    _sim = 0.0
    _accum = 0.0


def hold_logic(now: float) -> None:
    """Forget banked time while the map sim is not running (the minimap)."""
    global _last_real, _sim, _accum
    _last_real = now
    _sim = now
    _accum = 0.0


def take_logic_steps(now: float) -> int:
    """How many 1/200 s engine passes fit since the previous real timestamp.

    The first call is one pass. A gap longer than a quarter second, or a
    backwards clock, does not replay the pause. More than MAX_LOGIC_STEPS
    passes in one display frame are dropped so a hitch cannot fast-forward.
    """
    global _last_real, _sim, _accum
    if _last_real is None:
        _last_real = now
        _sim = now
        _accum = 0.0
        return 1
    dt = now - _last_real
    _last_real = now
    if dt <= 0.0 or dt > 0.25:
        _accum = 0.0
        return 1 if dt > 0.25 else 0
    _accum += dt
    n = 0
    while _accum + 1e-9 >= LOGIC_DT and n < MAX_LOGIC_STEPS:
        _accum -= LOGIC_DT
        n += 1
    if n >= MAX_LOGIC_STEPS:
        _accum = 0.0
    return n


def advance_logic_timer() -> float:
    """Publish the next engine timestamp. Call once per take_logic_steps pass."""
    global _sim, timer
    timer = _sim
    _sim += LOGIC_DT
    return timer
