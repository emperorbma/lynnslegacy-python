"""AI / declare-list gaps: squirrel destroy, vguard pause, FB registrations."""

from __future__ import annotations

import re
from pathlib import Path

import lynn.object  # noqa: F401
import lynn.object.move_ai  # noqa: F401

from lynn import clock
from lynn.constants import u_angerfireball, u_cell
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
from lynn.hero import ctor_hero, ctor_hero_only
import lynn.object.boss as boss
from lynn.object.char import CharType
from lynn.object.dispatch import FUNC_REGISTRY, MISSING_FUNCS, lookup_func, __noop
from lynn.object.move_ai import __lunge, __lunge_return, __move_down
from lynn.object.tick import tick_object
from lynn.object.xml_load import LLSystem_CopyNewObject, LLSystem_ObjectFromXML


def _obj(path: str) -> CharType:
    obj = CharType()
    obj.id = path
    return LLSystem_ObjectFromXML(obj, load_images=False)


def _bind(objs: list[CharType]) -> CharType:
    reset_events()
    hero = ctor_hero(load_images=False)
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero(hero)
    bind_hero_only(ctor_hero_only())
    bind_room(None, objs)
    return hero


def test_shipped_xml_funcs_all_resolve():
    """No object XML <func> should fall through to __noop."""
    MISSING_FUNCS.clear()
    missing: list[str] = []
    for path in sorted(Path("data/object").glob("*.xml")):
        text = path.read_text(encoding="latin-1", errors="replace")
        for match in re.finditer(r"<func>\s*([^<]+?)\s*</func>", text):
            name = match.group(1).strip()
            if not name:
                continue
            key = name if name.startswith("__") else f"__{name}"
            if lookup_func(key) is __noop and key != "__noop":
                missing.append(f"{path.name}:{key}")
    assert missing == [], "XML funcs still unresolved:\n" + "\n".join(missing)


def test_implemented_fb_declares_are_registered():
    """FB declares that have .bas bodies (or port AI) must be in the registry.

    Declares with no FB body (__near, __far, __active_anim, __anger_fireball,
    __reset_enemy, __steel_slide) and title-only __handle_menu stay out.
    """
    import lynn.object.move_ai  # noqa: F401

    expected = {
        "__anger_fireball_lock",
        "__calc_slide",
        "__destroy",
        "__give_weapon2",
        "__go_grip",
        "__lunge",
        "__lunge_return",
        "__momentum_move",
        "__move_down",
        "__move_left",
        "__move_right",
        "__random_pause",
        "__stop_grip",
    }
    absent = sorted(name for name in expected if name not in FUNC_REGISTRY)
    assert absent == []


def test_squirrel_destroy_despawns_after_home():
    """Forest squirrel NPC: home → destroy → return_trig must finish."""
    squirrel = _obj("data/object/squirrel.xml")
    assert lookup_func("__destroy") is not __noop
    assert squirrel.funcs.func[5][1] is lookup_func("__destroy")
    squirrel.coords_x = 10
    squirrel.coords_y = 20
    squirrel.dest_x = 10
    squirrel.dest_y = 20
    squirrel.funcs.active_state = 5
    squirrel.funcs.current_func[5] = 0
    _bind([squirrel])
    clock.timer = 1.0
    # home completes immediately at dest.
    tick_object(squirrel)
    assert squirrel.funcs.current_func[5] == 1
    tick_object(squirrel)
    assert squirrel.dead != 0
    assert squirrel.invisible != 0
    assert squirrel.total_dead != 0
    assert squirrel.funcs.current_func[5] == 2
    tick_object(squirrel)
    assert squirrel.return_trig == 1
    assert squirrel.funcs.current_func[5] == 3


def test_vguard_random_pause_advances_into_patrol():
    """Nerme/Limbo vguard: random_pause must not softlock the patrol block."""
    import random

    vguard = _obj("data/object/vguard.xml")
    assert lookup_func("__random_pause") is not __noop
    assert vguard.funcs.func[0][0] is lookup_func("__random_pause")
    assert vguard.funcs.func[0][1] is lookup_func("__randomize_path")
    _bind([vguard])
    clock.timer = 0.0
    random.seed(1)
    assert tick_object(vguard) is None
    assert vguard.funcs.current_func[0] == 0
    assert vguard.pause != 0
    clock.timer = vguard.pause
    tick_object(vguard)
    assert vguard.pause == 0
    assert vguard.funcs.current_func[0] == 1


def test_give_weapon2_matches_give_weapon():
    reset_events()
    only = ctor_hero_only()
    only.has_weapon = 1
    only.weapon = 1
    bind_hero_only(only)
    o = CharType()
    assert lookup_func("__give_weapon2")(o) == 1
    assert only.has_weapon == 2
    assert only.weapon == 2


def test_lunge_and_return_reach_origin():
    reset_events()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 80
    hero.coords_y = 80
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero(hero)
    enemy = CharType()
    enemy.coords_x = 40
    enemy.coords_y = 40
    enemy.x_origin = 40
    enemy.y_origin = 40
    enemy.perimeter_x = 16
    enemy.perimeter_y = 16
    enemy.walk_length = 2
    enemy.mad_walk_speed = 0.01
    enemy.walk_speed = 0.01
    clock.timer = 0.0
    assert __lunge(enemy) == 0
    clock.timer = enemy.walk_hold
    enemy.walk_hold = 0
    assert __lunge(enemy) == 1
    enemy.coords_x = 50
    enemy.coords_y = 55
    clock.timer = 10.0
    enemy.walk_hold = 0
    # Without a room, lunge_return cannot step — force arrival.
    enemy.coords_x = enemy.x_origin
    enemy.coords_y = enemy.y_origin
    assert __lunge_return(enemy) == 1
    assert enemy.mad == 0


def test_move_down_steps_without_room():
    reset_events()
    o = CharType()
    o.coords_x = 5
    o.coords_y = 5
    o.walk_speed = 0.01
    clock.timer = 1.0
    assert __move_down(o) == 1
    assert o.direction == 2
    assert o.coords_y == 6


def test_anger_fireball_lock_staggers_copy():
    boss._anger_fireball_lock_h = 0.0
    reset_events()
    degrees = []
    for _ in range(8):
        ball = CharType()
        ball.id = "data/object/angerfireball.xml"
        LLSystem_CopyNewObject(ball, load_images=False)
        assert ball.unique_id == u_angerfireball
        degrees.append(ball.degree)
    assert degrees == [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
    assert boss._anger_fireball_lock_h == 0.0


def test_cell_copy_picks_diagonal_direction():
    reset_events()
    seen = set()
    for seed in range(20):
        import random

        random.seed(seed)
        cell = CharType()
        cell.id = "data/object/cell.xml"
        LLSystem_CopyNewObject(cell, load_images=False)
        assert cell.unique_id == u_cell
        assert 4 <= cell.direction <= 7
        seen.add(cell.direction)
    assert len(seen) >= 2
