import lynn.object  # noqa: F401
from lynn import clock
from lynn.events import bind_hero, bind_room, reset_events
from lynn.hero import ctor_hero
from lynn.map.collision import move_object
from lynn.map.loader import load_mapV
from lynn.map.types import RoomType
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.move_ai import __chase, __copter_path
from lynn.object.tick import tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import resolve_map_path


def test_gcopter_xml_binds_copter_path():
    obj = CharType()
    obj.id = "data/object/gcopter.xml"
    LLSystem_ObjectFromXML(obj, load_images=False)
    assert obj.hp == 2
    assert obj.strength == 2
    assert obj.uni_directional == 1
    assert obj.walk_length == 80
    assert lookup_func("__copter_path") is __copter_path
    assert obj.funcs.func[0][7] is __copter_path


def test_copter_path_picks_8_dir():
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    room = m.room[2]
    o = CharType()
    o.walk_length = 80
    o.perimeter_x = 32
    o.perimeter_y = 24
    o.coords_x = 200
    o.coords_y = 200
    o.unstoppable_by_tile = -1
    o.unstoppable_by_screen = -1
    bind_room(room, [o])
    assert __copter_path(o) == 1
    assert 0 <= o.direction <= 7
    assert o.walk_buffer == 80


def _rcopter() -> CharType:
    obj = CharType()
    obj.id = "data/object/rcopter.xml"
    return LLSystem_ObjectFromXML(obj, load_images=False)


def test_red_copter_keeps_aggro_after_lynn_steps_outside():
    """The leash starts on the acquire pass. A later step outside still chases."""
    reset_events()
    saved = clock.timer
    clock.timer = 10.0
    try:
        hero = ctor_hero(load_images=False)
        hero.coords_x = 100
        hero.coords_y = 100
        hero.perimeter_x = 16
        hero.perimeter_y = 16
        bind_hero(hero)
        cop = _rcopter()
        cop.coords_x = 100
        cop.coords_y = 100
        assert cop.froggy == 1
        assert cop.lose_time == 4
        assert cop.vision_field == 48
        bind_room(RoomType(), [cop])
        tick_objects([cop])
        assert cop.mad == 1
        assert cop.funcs.active_state == cop.jump_state
        assert cop.reset_delay == clock.timer + cop.lose_time
        # One axis leaves the 48px box. The other stays inside the far box.
        hero.coords_x = 168
        for i in range(4):
            clock.timer = 10.0 + (i + 1) * 0.05
            tick_objects([cop])
            assert cop.mad == 1
            assert cop.funcs.active_state == cop.jump_state
    finally:
        clock.timer = saved


def test_red_copter_returns_to_the_chase_after_a_hit():
    """A hit clears mad. Lynn still in the vision box should not make it land."""
    import lynn.object.move_ai  # noqa: F401 — bind __chase before the XML load

    from lynn.constants import DF_MAIN_CHAR
    from lynn.object.combat import LLObject_DamageCalc

    reset_events()
    saved = clock.timer
    clock.timer = 10.0
    try:
        hero = ctor_hero(load_images=False)
        hero.coords_x = 100
        hero.coords_y = 100
        hero.perimeter_x = 16
        hero.perimeter_y = 16
        bind_hero(hero)
        cop = _rcopter()
        cop.coords_x = 120
        cop.coords_y = 100
        bind_room(RoomType(), [cop])
        for _ in range(8):
            clock.timer += 0.005
            tick_objects([cop])
        assert cop.mad == 1
        assert cop.funcs.active_state == cop.jump_state
        assert cop.funcs.current_func[cop.jump_state] >= 2
        cop.dmg_id = DF_MAIN_CHAR
        LLObject_DamageCalc(cop)
        assert cop.funcs.active_state == cop.hit_state
        for _ in range(40):
            clock.timer += 0.005
            tick_objects([cop])
            if cop.funcs.active_state == cop.jump_state and cop.mad == 1:
                break
        assert cop.funcs.active_state == cop.jump_state
        assert cop.mad == 1
        assert cop.funcs.current_func[cop.jump_state] >= 2
    finally:
        clock.timer = saved


def test_red_copter_lands_when_a_hit_knocks_lynn_out_of_vision():
    reset_events()
    saved = clock.timer
    clock.timer = 10.0
    try:
        hero = ctor_hero(load_images=False)
        hero.coords_x = 100
        hero.coords_y = 100
        hero.perimeter_x = 16
        hero.perimeter_y = 16
        bind_hero(hero)
        cop = _rcopter()
        cop.coords_x = 100
        cop.coords_y = 100
        bind_room(RoomType(), [cop])
        tick_objects([cop])
        from lynn.constants import DF_MAIN_CHAR
        from lynn.object.combat import LLObject_DamageCalc

        cop.dmg_id = DF_MAIN_CHAR
        LLObject_DamageCalc(cop)
        hero.coords_x = 400
        hero.coords_y = 400
        landed = False
        for _ in range(40):
            clock.timer += 0.005
            tick_objects([cop])
            if cop.funcs.active_state == cop.reset_state:
                landed = True
                break
        assert landed
        assert cop.mad == 0
    finally:
        clock.timer = saved


def test_chase_keeps_sidestepping_after_a_blocked_step(monkeypatch):
    """FB swaying skips the direct vector until that direction can move."""
    reset_events()
    saved = clock.timer
    clock.timer = 0.0
    tried: list[int] = []

    def _blocked_right(this, room, only_looking=0, moment=1, others=None, **_kw):
        tried.append(int(this.direction))
        if this.direction in (1, 5, 6):
            return 0
        if this.direction == 2:
            this.coords_y += 1
            return 1
        if this.direction == 3:
            this.coords_x -= 1
            return 1
        if this.direction == 0:
            this.coords_y -= 1
            return 1
        return 0

    monkeypatch.setattr("lynn.object.move_ai.move_object", _blocked_right)
    try:
        hero = ctor_hero(load_images=False)
        hero.coords_x = 200
        hero.coords_y = 100
        hero.perimeter_x = 16
        hero.perimeter_y = 16
        bind_hero(hero)
        cop = CharType()
        cop.coords_x = 100
        cop.coords_y = 100
        cop.perimeter_x = 32
        cop.perimeter_y = 16
        cop.mad_walk_speed = 0.019
        cop.uni_directional = 1
        cop.degree = 90
        cop.sway = 1
        bind_room(RoomType(), [cop])
        assert __chase(cop) == 0
        assert tried == [1, 2, 1]
        assert cop.swaying == -1
        assert cop.coords_y == 101
        tried.clear()
        cop.walk_hold = 0
        assert __chase(cop) == 0
        assert tried[0] != 1
        assert cop.coords_y > 101
    finally:
        clock.timer = saved


def test_move_object_diagonal_up_right():
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    room = m.room[2]
    o = CharType()
    o.perimeter_x = 16
    o.perimeter_y = 16
    o.coords_x = 200
    o.coords_y = 200
    o.direction = 5
    o.unstoppable_by_tile = -1
    x0, y0 = o.coords_x, o.coords_y
    result = move_object(o, room, only_looking=0, moment=1)
    assert result != 0
    assert o.coords_x == x0 + 1
    assert o.coords_y == y0 - 1
