"""Nerme green save points and the roamers a vine guard spawns."""

import lynn.object  # noqa: F401
from lynn import clock
from lynn.constants import TRUE, u_savepoint
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.types import RoomType
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.tick import tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML


def _load(name: str) -> CharType:
    obj = CharType()
    obj.id = f"data/object/{name}"
    return LLSystem_ObjectFromXML(obj, load_images=False)


def test_hsavepoint_heals_then_opens_the_save_menu(monkeypatch):
    """heal_lynn sits in front of the file menu. A noop there never saves."""
    monkeypatch.setattr("lynn.object.save.LLSystem_ReadSaveFile", lambda name: None)
    reset_events()
    saved = clock.timer
    clock.timer = 0.0
    try:
        hero = ctor_hero(load_images=False)
        hero.hp = 1
        hero.maxhp = 6
        hero.coords_x = 100
        hero.coords_y = 100
        only = ctor_hero_only()
        only.action = 1
        bind_hero(hero)
        bind_hero_only(only)
        sp = _load("hsavepoint.xml")
        sp.coords_x = 100
        sp.coords_y = 100
        assert sp.unique_id == u_savepoint
        assert sp.jump_state == 1
        assert lookup_func("__heal_lynn") is not lookup_func("__noop")
        jump = sp.funcs.func[sp.jump_state]
        assert jump[3] is lookup_func("__heal_lynn")
        assert jump[4] is lookup_func("__poll_action")
        assert jump[5] is lookup_func("__do_menu_save")
        opened = False
        for _ in range(16):
            tick_objects([sp])
            if hero.hp == hero.maxhp and hero.menu_sel == 2:
                opened = True
                break
        assert hero.hp == hero.maxhp
        assert opened
        assert hero.menu_sel == 2
        import lynn.events as events

        assert events.box_entity is sp
        assert events.do_hud == 0
    finally:
        clock.timer = saved


def test_vine_guard_roamer_is_removed_before_it_can_drop(monkeypatch):
    """FB maintain_temps releases a temp on the cripple call, before __drop."""
    monkeypatch.setattr("random.random", lambda: 0.0)
    reset_events()
    saved = clock.timer
    clock.timer = 0.0
    try:
        room = RoomType()
        guard = _load("vguard.xml")
        guard.coords_x = 80
        guard.coords_y = 80
        others = [guard]
        bind_room(room, others)
        assert lookup_func("__make_enemy")(guard) == 1
        roamer = others[1]
        assert roamer.is_temp == TRUE
        assert roamer.d_health == 50
        assert "roamer" in roamer.id.replace("\\", "/").lower()
        roamer.hp = 0
        room_list = [roamer]
        for _ in range(12):
            clock.timer += 0.05
            tick_objects(room_list)
            if not room_list:
                break
        assert room_list == []
        assert roamer.dropped == 0
        assert roamer.total_dead != 0
        assert roamer.funcs.current_func[roamer.death_state] == 3
    finally:
        clock.timer = saved


def test_placed_roamer_still_drops(monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.0)
    reset_events()
    saved = clock.timer
    clock.timer = 0.0
    try:
        roamer = _load("roamer.xml")
        assert roamer.is_temp == 0
        assert roamer.d_health == 50
        roamer.hp = 0
        room_list = [roamer]
        for _ in range(24):
            clock.timer += 0.05
            tick_objects(room_list)
        assert room_list == [roamer]
        assert roamer.dropped == 1
        assert roamer.total_dead != 0
    finally:
        clock.timer = saved
