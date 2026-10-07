"""Arx: torch colors, shapeless heal and hurt, the bridge menu, Sterach's sword, chargers."""

import lynn.object  # noqa: F401
import lynn.object.move_ai  # noqa: F401

from lynn import audio, clock
from lynn.audio import sound_explosion, sound_switch
from lynn.constants import (
    TRUE,
    u_bshape,
    u_charger,
    u_eguard,
    u_gshape,
    u_ltorch,
    u_sterach,
    u_swordie,
)
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.gfx.menu import (
    MainMenu,
    bridge_menu_icons,
    menu_MAX,
    menu_blank,
    menu_blank_select,
    menu_bridge,
    menu_bridge2,
    menu_bridge2_select,
    menu_bridge3,
    menu_bridge3_select,
    menu_bridge_select,
    scraps_menu_name,
)
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.types import RoomType
from lynn.map.loader import load_mapV
from lynn.object.boss import (
    __sterach_call,
    __sword_angle,
    __sword_fly,
    __sword_glow,
    __sword_jump,
    __sword_return,
)
from lynn.object.char import CharType
from lynn.object.combat import LLObject_ObjectDamage
from lynn.object.dispatch import lookup_func
from lynn.object.move_ai import __charger_charge
from lynn.object.seq_funcs import __cool_down, __make_dead
from lynn.object.tick import LLObject_TorchModify, tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML, spawn_from_stub
from lynn.paths import resolve_map_path


def _obj(path: str) -> CharType:
    obj = CharType()
    obj.id = path
    return LLSystem_ObjectFromXML(obj, load_images=False)


def _open_room() -> RoomType:
    room = RoomType()
    room.x = 40
    room.y = 40
    n = room.x * room.y
    room.layout = [[0] * n, [0] * n, [0] * n]
    return room


def _solid_room() -> RoomType:
    room = RoomType()
    room.x = 40
    room.y = 40
    room.layout = [[], [], []]
    return room


def _bind(room: RoomType, objs: list[CharType], hero: CharType | None = None) -> CharType:
    reset_events()
    if hero is None:
        hero = ctor_hero(load_images=False)
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.invincible = 0
    hero.dmg_id = 0
    hero.hurt = 0
    bind_hero(hero)
    bind_hero_only(ctor_hero_only())
    bind_room(room, objs)
    clock.timer = 5.0
    return hero


def _menu(has_scraps: int = 1) -> tuple[MainMenu, object]:
    reset_events()
    menu = MainMenu()
    menu.menuNames = [""] * menu_MAX
    menu.menuNames[menu_bridge_select] = "Some old scraps."
    only = ctor_hero_only()
    only.hasItem[2] = has_scraps
    return menu, only


def test_sword_and_sterach_procs_are_registered():
    sword = _obj("data/object/swordie.xml")
    boss = _obj("data/object/sterach.xml")
    assert sword.unique_id == u_swordie
    assert boss.unique_id == u_sterach
    assert sword.fly_length == 75
    assert abs(sword.fly_speed - 0.004) < 1e-6
    assert [fn.__name__ for fn in sword.funcs.func[1]] == [
        "__sword_glow",
        "__q_second_pause",
        "__sword_glow",
        "__sword_fly",
        "__second_pause",
        "__sterach_call",
        "__sword_return",
        "__infinity",
    ]
    idle = [fn.__name__ for fn in boss.funcs.func[0]]
    assert "__sword_jump" in idle
    assert idle[-1] == "__infinity"
    death = [fn.__name__ for fn in boss.funcs.func[boss.death_state]]
    assert death[0] == "__make_dead"
    assert "__play_seq" in death
    for name in (
        "__sword_angle",
        "__sword_fly",
        "__sword_return",
        "__sword_glow",
        "__sword_jump",
        "__sterach_call",
    ):
        assert lookup_func(name).__name__ == name


def test_sword_angle_faces_the_four_cardinals():
    sword = _obj("data/object/swordie.xml")
    sword.coords_x = 80
    sword.coords_y = 80
    hero = _bind(_open_room(), [sword])
    # Mids: sword (96, 96), hero (x+8, y+8). Bias is +5.625 degrees, 16 frames.
    cases = (
        (160, 88, 4),  # right
        (8, 88, 12),  # left
        (88, 160, 8),  # down
        (88, 0, 0),  # up
    )
    for hx, hy, frame in cases:
        hero.coords_x = hx
        hero.coords_y = hy
        assert __sword_angle(sword) == 1
        assert sword.frame == frame


def _sword_travel(step: float, count: int) -> int:
    sword = _obj("data/object/swordie.xml")
    sword.coords_x = 80
    sword.coords_y = 80
    hero = _bind(_open_room(), [sword])
    hero.coords_x = 400
    hero.coords_y = 88
    clock.timer = 0.0
    sword.fly_timer = 0
    sword.fly_count = 0
    start = sword.coords_x
    for i in range(count):
        clock.timer = (i + 1) * step
        if __sword_fly(sword) == 1:
            break
    return int(sword.coords_x) - start


def test_sword_fly_at_engine_rate_is_faster_than_one_step_per_display_frame():
    """fly_speed 0.004 clears on the next engine pass. 60 Hz makes that pass 16 ms."""
    slow = _sword_travel(1.0 / 60.0, 30)
    fast = _sword_travel(clock.LOGIC_DT, int(0.5 / clock.LOGIC_DT))
    assert slow < 45
    assert fast > 80
    assert fast > slow * 2


def test_sword_fly_steps_toward_lynn_and_ends_on_a_wall():
    sword = _obj("data/object/swordie.xml")
    sword.coords_x = 80
    sword.coords_y = 80
    sword.direction = 0
    room = _open_room()
    hero = _bind(room, [sword])
    hero.coords_x = 160
    hero.coords_y = 88
    assert __sword_fly(sword) == 0
    assert sword.coords_x == 82
    assert sword.coords_y == 80
    assert sword.direction == 0
    assert sword.fly_count == 1
    assert abs(sword.fly_x + 1.0) < 1e-6
    assert sword.fly_y == 0
    held = sword.coords_x
    assert __sword_fly(sword) == 0
    assert sword.coords_x == held
    # The wait clears on this call. The next one, with fly_timer back at 0, steps.
    clock.timer = sword.fly_timer
    assert __sword_fly(sword) == 0
    assert sword.coords_x == held
    assert sword.fly_timer == 0
    assert __sword_fly(sword) == 0
    assert sword.coords_x == held + 2

    blocked = _obj("data/object/swordie.xml")
    blocked.coords_x = 80
    blocked.coords_y = 80
    _bind(_solid_room(), [blocked], hero)
    hero.coords_x = 160
    hero.coords_y = 88
    assert __sword_fly(blocked) == 1
    assert blocked.coords_x == 80
    assert blocked.fly_count == 0
    assert blocked.fly_timer == 0


def test_sword_returns_to_sterach_and_a_wall_does_not_finish_it():
    sword = _obj("data/object/swordie.xml")
    boss = _obj("data/object/sterach.xml")
    sword.coords_x = 80
    sword.coords_y = 80
    boss.coords_x = 88
    boss.coords_y = 88
    sword.funcs.active_state = 1
    _bind(_open_room(), [sword, boss])
    assert __sword_return(sword) == 0
    assert boss.funcs.active_state == 1
    assert sword.funcs.active_state == 1
    assert __sword_return(sword) == 0
    assert sword.funcs.active_state == 0

    thrown = _obj("data/object/swordie.xml")
    thrown.coords_x = 80
    thrown.coords_y = 80
    other = _obj("data/object/sterach.xml")
    other.coords_x = 200
    other.coords_y = 80
    _bind(_solid_room(), [thrown, other])
    assert __sword_return(thrown) == 0
    assert thrown.coords_x == 80
    assert thrown.fly_count == 0
    assert other.funcs.active_state == 0


def test_glow_jump_and_sterach_call_use_room_indices():
    sword = _obj("data/object/swordie.xml")
    boss = _obj("data/object/sterach.xml")
    sword.current_anim = 0
    boss.current_anim = 1
    boss.frame = 4
    _bind(_open_room(), [sword, boss])
    assert __sword_glow(sword) == 1
    assert sword.current_anim == 1
    assert __sword_glow(sword) == 1
    assert sword.current_anim == 0
    assert __sword_jump(boss) == 1
    assert sword.funcs.active_state == 1
    assert boss.funcs.active_state == 0
    assert __sterach_call(sword) == 1
    assert boss.current_anim == 3
    assert boss.frame == 0


def test_sterach_death_kills_the_sword():
    sword = _obj("data/object/swordie.xml")
    boss = _obj("data/object/sterach.xml")
    sword.hp = 1
    _bind(_open_room(), [sword, boss])
    assert __make_dead(boss) == 1
    assert boss.dead != 0
    assert sword.hp == 0
    assert boss.funcs.active_state == 0
    events.now[1203] = TRUE
    assert __make_dead(boss) == 1
    assert boss.funcs.active_state == 5
    assert sword.hp == 0


def test_torch_takes_the_first_living_ghost_or_guard():
    torch = _obj("data/object/ltorch.xml")
    assert torch.unique_id == u_ltorch
    assert torch.vision_field == 32
    green = _obj("data/object/gshape.xml")
    red = _obj("data/object/bshape.xml")
    guard = CharType()
    guard.unique_id = u_eguard
    guard.perimeter_x = 16
    guard.perimeter_y = 16
    for obj in (torch, green, red, guard):
        obj.coords_x = 0
        obj.coords_y = 0

    LLObject_TorchModify(torch, [green])
    assert torch.current_anim == 2
    LLObject_TorchModify(torch, [red])
    assert torch.current_anim == 1
    LLObject_TorchModify(torch, [guard, red])
    assert torch.current_anim == 3
    LLObject_TorchModify(torch, [green, guard])
    assert torch.current_anim == 2

    green.dead = TRUE
    LLObject_TorchModify(torch, [green, red])
    assert torch.current_anim == 1
    red.coords_x = 32
    LLObject_TorchModify(torch, [red])
    assert torch.current_anim == 0
    red.coords_x = 31
    red.coords_y = 0
    LLObject_TorchModify(torch, [red])
    assert torch.current_anim == 1
    red.coords_x = 0
    red.coords_y = 32
    LLObject_TorchModify(torch, [red])
    assert torch.current_anim == 0

    torch.current_anim = 2
    room = _open_room()
    green.dead = 0
    green.coords_x = 0
    green.coords_y = 0
    _bind(room, [torch, green])
    tick_objects([torch, green])
    assert torch.current_anim == 2


def test_green_ghost_heals_and_both_colors_are_spent():
    room = _open_room()
    green = _obj("data/object/gshape.xml")
    assert green.unique_id == u_gshape
    assert green.strength == -3
    green.coords_x = 40
    green.coords_y = 40
    hero = _bind(room, [green])
    hero.coords_x = 40
    hero.coords_y = 40
    hero.hp = 10
    LLObject_ObjectDamage([green], hero)
    assert hero.hp == 13
    assert hero.hurt == 0
    assert hero.dmg_id == 0
    assert green.dead != 0
    assert green.invisible != 0
    assert green.strength == 0
    assert green.impassable == 0
    LLObject_ObjectDamage([green], hero)
    assert hero.hp == 13

    red = _obj("data/object/bshape.xml")
    assert red.unique_id == u_bshape
    assert red.strength == 1
    red.coords_x = 40
    red.coords_y = 40
    hero = _bind(room, [red])
    hero.coords_x = 40
    hero.coords_y = 40
    hero.hp = 6
    LLObject_ObjectDamage([red], hero)
    assert hero.hp == 5
    assert hero.hurt == 1
    assert hero.dmg_id != 0
    assert red.dead != 0
    assert red.invisible != 0
    assert red.strength == 0


def test_bridge_menu_follows_the_weapon_then_the_two_spans():
    menu, only = _menu()
    assert bridge_menu_icons(only) == (menu_bridge, menu_bridge_select)
    assert scraps_menu_name(menu, only) == "Some old scraps."

    events.now[470] = TRUE
    assert bridge_menu_icons(only) == (menu_bridge2, menu_bridge2_select)
    assert scraps_menu_name(menu, only) == "Some old scraps."

    events.now[1206] = TRUE
    assert bridge_menu_icons(only) == (menu_bridge3, menu_bridge3_select)
    assert scraps_menu_name(menu, only) == "A sturdy rope."

    only.has_weapon = 2
    assert bridge_menu_icons(only) == (menu_blank, menu_blank_select)
    assert scraps_menu_name(menu, only) == "Nothing left!"

    only.hasItem[2] = 0
    assert scraps_menu_name(menu, only) == ""


def _pump_charge(charger: CharType) -> int:
    if charger.walk_hold and clock.timer < charger.walk_hold:
        clock.timer = charger.walk_hold
    return __charger_charge(charger)


def test_charger_dashes_to_the_wall_then_retreats():
    charger = _obj("data/object/charger.xml")
    assert charger.jump_state == 2
    assert charger.funcs.func[2][0] is __charger_charge
    assert charger.funcs.func[2][2] is __cool_down
    assert lookup_func("__charger_charge") is __charger_charge
    assert lookup_func("__cool_down") is __cool_down
    assert charger.perimeter_x == 96
    assert charger.unstoppable_by_object != 0

    charger.direction = 1
    charger.coords_x = 16
    charger.coords_y = 200
    room = _open_room()
    _bind(room, [charger])
    clock.timer = 0.0
    charger.walk_hold = 0
    limit_x = (room.x << 4) - charger.perimeter_x
    audio.last_play = None
    boom = None
    result = 0
    for _ in range(4000):
        result = _pump_charge(charger)
        if boom is None and audio.last_play == (sound_explosion, 40):
            boom = charger.coords_x
        if result == 1:
            break
    assert result == 1
    assert boom == limit_x
    assert charger.coords_x == 0
    assert charger.direction == 1
    assert charger.internalState == 0
    assert charger.current_anim == 0
    assert charger.sway == 0
    assert audio.last_play == (sound_switch, 40)
    assert abs(charger.walk_speed - 0.013) < 1e-9

    charger.mad = 1
    assert __cool_down(charger) == 1
    assert charger.mad == 0


def test_arx_chargers_leave_their_halls_when_lynn_is_near():
    """Rooms 44 and 52. The dash is the only func those objects were missing."""
    game_map = load_mapV(str(resolve_map_path("arx")), load_tileset=False)
    for room_i, axis, sign in ((44, "coords_x", 1), (52, "coords_x", -1)):
        room = game_map.room[room_i]
        stub = room.enemy[0]
        assert stub.id.replace("\\", "/").endswith("charger.xml")
        charger = spawn_from_stub(stub, load_images=False)
        hero = _bind(room, [charger])
        hero.coords_x = charger.coords_x
        hero.coords_y = charger.coords_y
        start = getattr(charger, axis)
        for i in range(1, 31):
            clock.timer = 5.0 + i * clock.LOGIC_DT
            tick_objects([charger])
        moved = getattr(charger, axis) - start
        assert moved * sign > 8
        assert charger.funcs.active_state == charger.jump_state
        assert charger.current_anim == 1


def test_charger_rush_covers_more_ground_than_the_return():
    """0.005s out, 0.013s back. One pixel per 1/200s pass, then the hold clears."""
    charger = _obj("data/object/charger.xml")
    charger.direction = 1
    charger.coords_x = 200
    charger.coords_y = 200
    _bind(_open_room(), [charger])
    clock.timer = 0.0
    charger.walk_hold = 0
    start = charger.coords_x
    half = int(0.5 / clock.LOGIC_DT)
    for i in range(1, half + 1):
        clock.timer = i * clock.LOGIC_DT
        __charger_charge(charger)
    outbound = charger.coords_x - start
    charger.internalState = 3
    charger.direction = 3
    charger.walk_speed = 0.013
    charger.walk_hold = 0
    back = charger.coords_x
    for i in range(half + 1, half * 2 + 1):
        clock.timer = i * clock.LOGIC_DT
        __charger_charge(charger)
    retreat = back - charger.coords_x
    assert outbound > 40
    assert retreat > 15
    assert outbound > retreat * 1.5


def test_charger_keeps_dashing_after_lynn_leaves():
    charger = _obj("data/object/charger.xml")
    assert charger.unique_id == u_charger
    charger.direction = 1
    charger.coords_x = 16
    charger.coords_y = 200
    hero = _bind(_open_room(), [charger])
    hero.coords_x = 16
    hero.coords_y = 200
    clock.timer = 0.0
    tick_objects([charger])
    assert charger.mad != 0
    assert charger.funcs.active_state == charger.jump_state
    started = charger.coords_x
    hero.coords_x = 2000
    hero.coords_y = 2000
    for i in range(40):
        clock.timer = 0.01 * (i + 1)
        tick_objects([charger])
    assert charger.funcs.active_state == charger.jump_state
    assert charger.coords_x >= started + 20
    assert charger.internalState == 0
