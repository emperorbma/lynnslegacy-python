import lynn.object  # noqa: F401
from lynn import clock
from lynn.constants import TRUE, u_savepoint
from lynn.events import bind_hero, bind_hero_only, reset_events
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.object.char import CharType
from lynn.object.control import in_proximity
from lynn.object.dispatch import lookup_func
from lynn.object.save import LLSystem_ReadSaveFile, LLSystem_WriteSaveFile, save_path
from lynn.object.xml_load import LLSystem_ObjectFromXML


def test_savepoint_xml_froggy_and_funcs():
    obj = CharType()
    obj.id = "data/object/savepoint.xml"
    LLSystem_ObjectFromXML(obj, load_images=False)
    assert obj.unique_id == u_savepoint
    assert obj.froggy == 1
    assert obj.vision_field == 32
    assert obj.jump_state == 1
    assert obj.reset_state == 2
    assert obj.invincible == -1
    assert lookup_func("__do_menu_save") is not lookup_func("__noop")
    assert lookup_func("__poll_action") is not lookup_func("__noop")
    assert obj.funcs.func[1][4] is lookup_func("__do_menu_save")


def test_in_proximity_jumps_to_jump_state():
    reset_events()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 100
    hero.coords_y = 100
    bind_hero(hero)
    sp = CharType()
    sp.id = "data/object/savepoint.xml"
    LLSystem_ObjectFromXML(sp, load_images=False)
    sp.coords_x = 110
    sp.coords_y = 110
    assert in_proximity(sp) == sp.jump_state
    assert sp.mad == 1


def test_write_and_read_json_save(tmp_path, monkeypatch):
    reset_events()
    hero = ctor_hero(load_images=False)
    hero.hp = 4
    hero.maxhp = 6
    hero.money = 12
    only = ctor_hero_only()
    only.has_weapon = 0
    bind_hero(hero)
    bind_hero_only(only)
    import lynn.events as events

    events.map_filename = "forest_fall.map"
    events.now[3] = TRUE
    path = tmp_path / "ll_save1.sav"
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    LLSystem_WriteSaveFile("ll_save1.sav", 2)
    data = LLSystem_ReadSaveFile(str(path))
    assert data is not None
    assert data.hp == 4
    assert data.gold == 12
    assert data.weapon == 0
    assert data.entry == 2
    assert data.map == "forest_fall.map"
    assert 3 in data.happen


def test_do_menu_save_writes_slot():
    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    import lynn.events as events

    events.map_filename = "forest_fall.map"
    events.keys.enter_pulse = TRUE
    sp = CharType()
    sp.id = "data/object/savepoint.xml"
    LLSystem_ObjectFromXML(sp, load_images=False)
    sp.chap = 1
    sp.menu_sel = 0
    clock.timer = 1.0
    lookup_func("__do_menu_save")(sp)
    path = save_path(0)
    try:
        assert path.is_file()
        data = LLSystem_ReadSaveFile("ll_save1.sav")
        assert data is not None
        assert data.entry == 1
    finally:
        if path.is_file():
            path.unlink()
