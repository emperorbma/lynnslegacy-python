import json
from pathlib import Path

import pytest

import lynn.object  # noqa: F401
from lynn import clock
from lynn.constants import TRUE, u_savepoint
from lynn.events import bind_hero, bind_hero_only, reset_events
import lynn.events as events
from lynn.hero import ctor_hero, ctor_hero_only, place_hero
from lynn.object.char import CharType
from lynn.object.control import in_proximity
from lynn.object.dispatch import lookup_func
from lynn.object.save import (
    LLSystem_ReadSaveFile,
    LLSystem_WriteSaveFile,
    apply_save_happen,
    apply_save_hero,
    example_short_name,
    resolve_save_spec,
)
from lynn.object.xml_load import LLSystem_ObjectFromXML

FIXTURES = Path(__file__).resolve().parent / "fixtures"
EXPECT_PATH = FIXTURES / "expect.json"


def _example_save_paths() -> list[Path]:
    return sorted(FIXTURES.glob("test_example_*.sav"))


def _example_save_expect() -> dict:
    if not EXPECT_PATH.is_file():
        return {}
    return json.loads(EXPECT_PATH.read_text(encoding="utf-8"))


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


def test_do_menu_save_writes_slot(tmp_path, monkeypatch):
    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    import lynn.events as events

    events.map_filename = "forest_fall.map"
    events.keys.enter_pulse = TRUE
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    sp = CharType()
    sp.id = "data/object/savepoint.xml"
    LLSystem_ObjectFromXML(sp, load_images=False)
    sp.chap = 1
    sp.menu_sel = 0
    clock.timer = 1.0
    lookup_func("__do_menu_save")(sp)
    path = tmp_path / "ll_save1.sav"
    assert path.is_file()
    data = LLSystem_ReadSaveFile("ll_save1.sav")
    assert data is not None
    assert data.entry == 1


@pytest.mark.parametrize(
    "path",
    _example_save_paths() or [None],
    ids=lambda p: p.name if p else "none",
)
def test_example_save_loads(path: Path | None):
    if path is None:
        pytest.skip("no local example saves in tests/fixtures")
    data = LLSystem_ReadSaveFile(str(path))
    assert data is not None
    assert data.map
    assert data.maxhp >= data.hp >= 0


@pytest.mark.parametrize(
    "name,expect",
    sorted(_example_save_expect().items()) or [("none", {})],
)
def test_example_save_state(name: str, expect: dict):
    if name == "none":
        pytest.skip("no local tests/fixtures/expect.json")
    path = FIXTURES / name
    if not path.is_file():
        pytest.skip(f"local fixture {name} not present")
    data = LLSystem_ReadSaveFile(str(path))
    assert data is not None
    if "hp" in expect:
        assert data.hp == expect["hp"]
    if "maxhp" in expect:
        assert data.maxhp == expect["maxhp"]
    if "gold" in expect:
        assert data.gold == expect["gold"]
    if "weapon" in expect:
        assert data.weapon == expect["weapon"]
    if "hasItem" in expect:
        assert data.hasItem == expect["hasItem"]
    if "hasCostume" in expect:
        assert data.hasCostume[: len(expect["hasCostume"])] == expect["hasCostume"]
    if "isWearing" in expect:
        assert data.isWearing == expect["isWearing"]
    if "b_key" in expect:
        assert (data.b_key != 0) == (expect["b_key"] != 0)
    if "map" in expect:
        assert data.map.replace("\\", "/").endswith(expect["map"])
    if "entry" in expect:
        assert data.entry == expect["entry"]
    for chap in expect.get("happen_has", ()):
        assert chap in data.happen
    if "rooms" in expect:
        assert data.rooms == expect["rooms"]


def test_resolve_save_spec_example_name():
    assert example_short_name("forest") == "forest"
    assert example_short_name("test_example_limbo3.sav") == "limbo3"
    try:
        path = resolve_save_spec("forest")
    except FileNotFoundError:
        pytest.skip("local example save forest not present")
    assert path.name == "test_example_forest.sav"
    assert path.is_file()
    limbo = resolve_save_spec("limbo3")
    assert limbo.name == "test_example_limbo3.sav"


@pytest.mark.parametrize(
    "path",
    _example_save_paths() or [None],
    ids=lambda p: p.name if p else "none",
)
def test_apply_example_save_restores_state(path: Path | None):
    from lynn.map.loader import load_mapV
    from lynn.paths import resolve_map_path

    if path is None:
        pytest.skip("no local example saves in tests/fixtures")
    data = LLSystem_ReadSaveFile(str(path))
    assert data is not None
    reset_events()
    apply_save_happen(data)
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    apply_save_hero(hero, only, data)
    m = load_mapV(str(resolve_map_path(data.map)), load_tileset=False)
    room = place_hero(hero, m, data.entry)
    assert hero.hp == data.hp
    assert hero.maxhp == data.maxhp
    assert hero.money == data.gold
    assert only.has_weapon == data.weapon
    assert only.weapon == data.weapon
    assert only.hasItem == data.hasItem
    for chap in data.happen:
        assert events.now[chap] != 0
    assert room == m.entry[data.entry].room
    assert (hero.coords_x, hero.coords_y) == (m.entry[data.entry].x, m.entry[data.entry].y)
