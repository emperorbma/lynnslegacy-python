"""Gelidus boss: Dyssius slide, eye beam, and the open eye."""

import random
from pathlib import Path

import lynn.object  # noqa: F401
from lynn import clock
from lynn.constants import DF_MAIN_CHAR, TRUE, u_dyssius, u_lynn, u_steelstrider
from lynn.events import bind_hero, bind_room, reset_events
import lynn.events as events
from lynn.map.collision import check_against
from lynn.map.loader import load_mapV
from lynn.map.types import RoomType
from lynn.object.boss import tick_dyssius
from lynn.object.char import CharType
from lynn.object.combat import LLObject_DamageCalc
from lynn.object.dispatch import lookup_func
from lynn.object.projectile import LLObject_ClearProjectiles, LLObject_ProjectileDamage, enemy_proj_drawable
from lynn.object.tick import tick_object, tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML, spawn_from_stub
from lynn.paths import resolve_map_path


def _boss(load_images: bool = False) -> CharType:
    boss = CharType()
    boss.id = "data/object/dyssius.xml"
    return LLSystem_ObjectFromXML(boss, load_images=load_images)


def _room(fill: int = 0) -> RoomType:
    room = RoomType()
    room.x = 30
    room.y = 30
    n = 30 * 31 + 2
    room.layout = [[fill] * n, [0] * n, [0] * n]
    return room


def _place(boss: CharType, room: RoomType) -> None:
    boss.coords_x = 80
    boss.coords_y = 80
    boss.perimeter_x = 16
    boss.perimeter_y = 16
    boss.walk_hold = 0
    boss._dyssius_slide_hold = 0
    reset_events()
    bind_hero(None)
    bind_room(room, [boss])
    clock.timer = 10.0


def test_dyssius_procs_are_registered():
    boss = _boss()
    for name in (
        "__dyssius_patience",
        "__dyssius_slide",
        "__dyssius_after_slide",
        "__dyssius_idle_gate",
        "__do_dyssius_proj",
        "__dyssius_flyback",
        "__dyssius_eye_explode",
        "__dyssius_full_explode",
    ):
        assert lookup_func(name) is not lookup_func("__noop")
        assert lookup_func(name).__name__ == name
    assert boss.unique_id == u_dyssius
    assert boss.isBoss != 0
    assert boss.hp == 15
    assert boss.funcs.func[0][0] is lookup_func("__dyssius_patience")
    assert boss.funcs.func[0][2] is lookup_func("__dyssius_slide")
    assert boss.funcs.func[boss.hit_state][0] is lookup_func("__dyssius_flyback")
    assert boss.funcs.func[boss.death_state][1] is lookup_func("__dyssius_eye_explode")
    assert boss.proj_style != 0
    assert boss.projectile is not None
    assert boss.projectile.length == 30
    assert boss.projectile.strength == 3


def test_patience_arms_sway_and_jump_starts_the_slide():
    boss = _boss()
    room = _room()
    _place(boss, room)
    boss.unstoppable_by_tile = 1
    boss.unstoppable_by_screen = 1
    tick_objects([boss])
    assert boss.sway == clock.timer + 4.5
    assert boss.funcs.current_func[0] == 1
    tick_objects([boss])
    assert boss.funcs.current_func[0] == 1
    clock.timer = boss.sway
    tick_objects([boss])
    assert boss.funcs.current_func[0] == 1
    clock.timer = boss.sway + 0.01
    tick_objects([boss])
    assert boss.funcs.active_state == 0
    assert boss.funcs.current_func[0] == 2
    assert boss.frame == 1
    assert boss.sway == 0


def test_slide_creeps_then_finishes_and_a_wall_ends_it():
    boss = _boss()
    room = _room()
    _place(boss, room)
    boss.unstoppable_by_tile = 1
    boss.unstoppable_by_screen = 1
    start = (boss.coords_x, boss.coords_y)
    assert lookup_func("__dyssius_slide")(boss) == 0
    assert (boss.coords_x, boss.coords_y) != start
    assert boss.frame == 1
    finished = 0
    for i in range(1, 100):
        boss.walk_hold = 0
        result = lookup_func("__dyssius_slide")(boss)
        if result == 1:
            finished = i + 1
            break
    assert finished == 100
    assert boss._dyssius_slide_hold == 0

    walled = _boss()
    _place(walled, _room(fill=0xFFFF))
    walled.walk_speed = 0.03
    assert lookup_func("__dyssius_slide")(walled) == 1


def test_off_ice_grip_clears_momentum_and_ice_keeps_it():
    boss = _boss()
    room = _room()
    _place(boss, room)
    boss.unstoppable_by_tile = 1
    boss.unstoppable_by_screen = 1
    lookup_func("__dyssius_slide")(boss)
    assert any(v > 0 for v in boss.momentum)
    tick_dyssius(boss)
    assert all(v == 0 for v in boss.momentum)
    assert lookup_func("__dyssius_after_slide")(boss) == 1
    assert boss.frame == 0

    icy = _boss()
    ice_room = _room()
    _place(icy, ice_room)
    icy.unstoppable_by_tile = 1
    icy.unstoppable_by_screen = 1
    # Center of (80, 80, 16, 16) is tile (5, 5) on a 30-wide room.
    ice_room.layout[0][5 * 30 + 5] = 1 << 8
    lookup_func("__dyssius_slide")(icy)
    before = list(icy.momentum)
    assert any(v > 0 for v in before)
    tick_dyssius(icy)
    assert any(v > 0 for v in icy.momentum)


def test_beam_drops_from_the_eye_and_hurts_lynn():
    boss = _boss()
    _place(boss, _room())
    boss.coords_x = 0
    boss.coords_y = 0
    boss.perimeter_x = 16
    boss.perimeter_y = 16
    assert lookup_func("__do_dyssius_proj")(boss) == 0
    assert boss.projectile.coords[0] == [120, 105]
    assert boss.projectile.coords[1] == [120, 121]
    assert boss.projectile.travelled == 1
    boss.projectile.refreshTime = 0
    lookup_func("__do_dyssius_proj")(boss)
    boss.projectile.refreshTime = 0
    lookup_func("__do_dyssius_proj")(boss)
    assert boss.projectile.coords[0][1] == 105 + 32

    hero = CharType()
    hero.unique_id = u_lynn
    hero.hp = 10
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.coords_x = 120
    hero.coords_y = 140
    bind_room(events.current_room, [boss])
    LLObject_ProjectileDamage([boss], hero)
    assert hero.hp == 7
    assert hero.hurt == 3
    assert boss.projectile.active == 0
    assert enemy_proj_drawable(boss) is True
    LLObject_ClearProjectiles(boss)
    assert enemy_proj_drawable(boss) is False


def test_flyback_returns_to_idle():
    boss = _boss()
    _place(boss, _room())
    boss.funcs.active_state = boss.hit_state
    boss.funcs.current_func[boss.hit_state] = 0
    boss.projectile.coords[0] = [5, 6]
    clock.timer = 0.0
    boss.fly_timer = 0
    boss.fly_count = 0
    steps = 0
    while boss.funcs.active_state != 0 and steps < 120:
        clock.timer += 1.0 / 60.0
        tick_object(boss)
        steps += 1
    assert boss.funcs.active_state == 0
    assert boss.funcs.current_func[0] == 0
    assert boss.fly_count == 0
    assert boss.projectile.coords[0] == [0, 0]
    assert steps < 80


def test_eye_is_the_only_vulnerable_face():
    from lynn.gfx.image import LLSystem_ImageLoad

    boss = _boss()
    _place(boss, _room())
    # Load the real .col without the XML image cache. Caching explosion.spr
    # makes Grult's boss explode animate instead of skipping ahead.
    boss.anim[0] = LLSystem_ImageLoad(r"data/pictures/char/boss2.spr")
    shell = boss.anim[0].frame[0]
    assert shell.faces >= 8
    assert shell.face[7].invincible == 0
    assert shell.face[4].invincible != 0
    boss.hp = 15
    boss.fly_count = 9
    boss.shifty_state = 4
    boss.slide_hold = 3
    boss.frame_check = 0
    boss.dmg_id = DF_MAIN_CHAR
    boss.dmg_specific = 4
    LLObject_DamageCalc(boss)
    assert boss.hp == 15

    boss.frame_check = 0
    boss.dmg_id = DF_MAIN_CHAR
    boss.dmg_specific = 7
    LLObject_DamageCalc(boss)
    assert boss.hp == 14
    assert boss.funcs.active_state == boss.hit_state
    assert boss.fly_count == 0
    assert boss.shifty_state == 0
    assert boss.slide_hold == 0


def test_slide_stops_on_lynn_and_idle_gate_can_restart():
    boss = CharType()
    lynn = CharType()
    lynn.unique_id = u_lynn
    lynn.num = -1
    lynn.coords_x = 100
    lynn.coords_y = 84
    lynn.perimeter_x = 16
    lynn.perimeter_y = 16
    boss.unique_id = u_dyssius
    boss.coords_x = 100
    boss.coords_y = 100
    boss.perimeter_x = 16
    boss.perimeter_y = 16
    boss.direction = 0
    boss.impassable = 0
    lynn.impassable = 0
    assert check_against(boss, lynn, 0) == 1
    assert check_against(lynn, boss, 2) == 0

    boss = _boss()
    saw_fire = False
    saw_idle = False
    for seed in range(50):
        random.seed(seed)
        boss.funcs.active_state = 0
        boss.funcs.current_func[0] = 4
        result = lookup_func("__dyssius_idle_gate")(boss)
        if result == 1:
            saw_fire = True
        else:
            saw_idle = True
            assert boss.funcs.active_state == 0
            assert boss.funcs.current_func[0] == 0
    assert saw_fire and saw_idle


def test_steelstrider_slide_uses_speed_four():
    boss = _boss()
    _place(boss, _room())
    boss.unique_id = u_steelstrider
    boss.unstoppable_by_tile = 1
    boss.unstoppable_by_screen = 1
    for i in range(8):
        boss.momentum[i] = 0
    lookup_func("__dyssius_slide")(boss)
    assert max(boss.momentum) == 4


def test_gelidus_r29_spawns_dyssius_with_happen_297():
    reset_events()
    game_map = load_mapV(str(resolve_map_path("gelidus")), load_tileset=False)
    stub = next(
        e
        for e in game_map.room[29].enemy
        if Path(str(e.id).replace("\\", "/")).name.lower() == "dyssius.xml"
    )
    boss = spawn_from_stub(stub, load_images=False)
    assert boss.chap == 297
    assert (boss.coords_x, boss.coords_y) == (376, 520)
    assert boss.seq_here != 0
    lookup_func("__dyssius_eye_explode")(boss)
    assert boss.explosions == 5
    assert (boss.expl_x_off, boss.expl_y_off) == (117, 98)
    lookup_func("__dyssius_full_explode")(boss)
    assert boss.explosions == 30
    boss.chap = 297
    events.now[297] = 0
    assert lookup_func("__set_happen")(boss) == 1
    assert events.now[297] == TRUE
