"""Godmode console: Load and Save open a scrolling file list. Heal stays on it."""

from lynn.events import reset_events
import lynn.events as events
from lynn.godmode import (
    GodEntry,
    GodMenu,
    apply_heal,
    apply_money,
    god_menu_back,
    god_menu_confirm,
    god_menu_move,
    god_menu_open,
    resume_entry,
    visible_rows,
    write_god_slot,
)
from lynn.main import _play_caption
from lynn.object.save import SaveData, write_save_data


def _fixture(tmp_path, name, **kwargs):
    write_save_data(tmp_path / f"test_example_{name}.sav", SaveData(**kwargs), "zlib")


def test_console_opens_load_then_esc_returns(tmp_path, monkeypatch):
    monkeypatch.setattr("lynn.object.save.example_save_dir", lambda: tmp_path)
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    _fixture(tmp_path, "forest", map="forest_fall.map", entry=21, hp=6, gold=1)
    _fixture(tmp_path, "postgelidus", map="forest_fall.map", entry=21, hp=8, gold=179)
    write_save_data(tmp_path / "ll_save1.sav", SaveData(map="gelidus.map", entry=3, hp=8), "zlib")
    before = (tmp_path / "test_example_postgelidus.sav").read_bytes()
    menu = GodMenu()
    god_menu_open(menu)
    assert menu.page == "root"
    assert god_menu_confirm(menu) is None
    assert menu.page == "load"
    assert [row.label for row in menu.entries] == ["slot 1", "forest", "postgelidus"]
    assert menu.entries[0].save.map == "gelidus.map"
    god_menu_back(menu)
    assert menu.page == "root"
    assert menu.index == 0
    assert menu.open is True
    assert (tmp_path / "test_example_postgelidus.sav").read_bytes() == before


def test_save_list_is_four_slots_and_esc_returns_there():
    menu = GodMenu()
    god_menu_open(menu)
    god_menu_move(menu, 1)
    assert god_menu_confirm(menu) is None
    assert menu.page == "save"
    assert [row.label for row in menu.entries] == ["slot 1", "slot 2", "slot 3", "slot 4"]
    assert all(row.kind == "save" for row in menu.entries)
    god_menu_back(menu)
    assert menu.page == "root"
    assert menu.index == 1
    god_menu_back(menu)
    assert menu.open is False


def test_heal_and_money_stay_on_the_console():
    menu = GodMenu()
    god_menu_open(menu)
    god_menu_move(menu, 2)
    picked = god_menu_confirm(menu)
    assert picked is not None
    assert picked.kind == "heal"
    assert menu.page == "root"
    god_menu_move(menu, 1)
    picked = god_menu_confirm(menu)
    assert picked.kind == "money"
    assert menu.page == "root"
    assert menu.open is True


def test_visible_rows_follow_a_long_load_list():
    menu = GodMenu()
    menu.page = "load"
    menu.entries = [GodEntry("load", f"s{i}") for i in range(6)]
    menu.index = 0
    start, shown = visible_rows(menu)
    assert start == 0
    assert len(shown) == 4
    menu.index = 5
    start, shown = visible_rows(menu)
    assert shown[-1].label == "s5"
    assert start <= menu.index < start + 4


def test_resume_entry_picks_the_closest_in_the_room():
    class Entry:
        def __init__(self, room, x, y):
            self.room, self.x, self.y = room, x, y

    class Map:
        entry = [Entry(0, 0, 0), Entry(2, 100, 100), Entry(2, 12, 8)]

    class Hero:
        coords_x, coords_y = 14, 10

    assert resume_entry(Map(), Hero(), 2) == 2
    assert resume_entry(None, Hero(), 2) == 0


def test_write_god_slot_stores_the_live_hero(tmp_path, monkeypatch):
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    reset_events()
    events.map_filename = "forest_fall.map"
    events.hero = type("H", (), {"hp": 8, "maxhp": 8, "money": 179, "key": 0})()
    events.hero_only = type(
        "O",
        (),
        {
            "hasItem": [-1, -1, 0, 0, 0, 0],
            "hasCostume": [-1, 0, 0, 0, 0, 0, 0, 0, 0],
            "has_weapon": 0,
            "has_bar": 0,
            "isWearing": 0,
            "b_key": 0,
        },
    )()
    events.now[297] = -1
    data = write_god_slot(2, 21)
    assert data is not None
    assert data.map == "forest_fall.map"
    assert data.entry == 21
    assert data.hp == 8
    assert data.gold == 179
    assert 297 in data.happen
    assert (tmp_path / "ll_save2.sav").is_file()
    reset_events()


def test_money_adds_ten_and_stops_at_the_hud_cap():
    class Hero:
        money = 12

    hero = Hero()
    apply_money(hero)
    assert hero.money == 22
    hero.money = 995
    apply_money(hero)
    assert hero.money == 999
    apply_money(None)


def test_heal_refills_and_clears_death():
    class Hero:
        hp = 1
        maxhp = 8
        dead = 1
        hurt = 3
        dmg_id = 4

    hero = Hero()
    apply_heal(hero)
    assert hero.hp == 8
    assert hero.dead == 0
    assert hero.hurt == 0
    assert hero.dmg_id == 0


def test_caption_names_the_loaded_fixture():
    reset_events()
    events.debug_god = -1
    events.debug_fixture = "postgelidus"
    assert _play_caption() == "Lynn's Legacy [godmode postgelidus]"
    reset_events()
    assert _play_caption() == "Lynn's Legacy"
