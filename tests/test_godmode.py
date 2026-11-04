"""Godmode console: Load/Save lists; Heal/Money/MaxHP use the FerUs line prompt."""

from lynn.events import reset_events
import lynn.events as events
from lynn.godmode import (
    GodEntry,
    GodMenu,
    ROOT_COMMANDS,
    apply_heal,
    apply_maxhp,
    apply_money,
    god_menu_back,
    god_menu_begin_prompt,
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
    reset_events()
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
    reset_events()


def test_save_list_is_four_slots_and_esc_returns_there():
    reset_events()
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
    reset_events()


def test_root_lists_heal_money_and_maxhp():
    assert ROOT_COMMANDS == ("Load", "Save", "Heal", "Money", "MaxHP")


def test_heal_money_maxhp_open_ferus_line_prompt():
    from lynn.console import feed_key

    reset_events()

    class Hero:
        hp = 3
        maxhp = 8
        money = 0
        dead = 0
        hurt = 0
        dmg_id = 0

    hero = Hero()
    menu = GodMenu()
    god_menu_open(menu)

    god_menu_move(menu, 2)  # Heal
    assert god_menu_confirm(menu, hero) is None
    assert events.console is not None
    assert events.console.prompt.startswith("Heal")
    assert events.console.text == ""
    feed_key(events.console, 13, "")
    assert hero.hp == 8
    assert events.console is None

    god_menu_move(menu, 1)  # Money
    assert god_menu_confirm(menu, hero) is None
    assert events.console.prompt.startswith("Gold")
    assert events.console.text == "10"
    feed_key(events.console, 13, "")
    assert hero.money == 10

    god_menu_move(menu, 1)  # MaxHP
    assert god_menu_confirm(menu, hero) is None
    assert events.console.prompt.startswith("MaxHP")
    assert events.console.text == "1"
    feed_key(events.console, 13, "")
    assert hero.maxhp == 9
    assert hero.hp == 9
    assert menu.open is True
    reset_events()


def test_prompt_esc_cancels_without_applying():
    from lynn.console import feed_key

    reset_events()

    class Hero:
        money = 5

    hero = Hero()
    menu = GodMenu()
    god_menu_open(menu)
    god_menu_begin_prompt(menu, "money", hero)
    assert events.console is not None
    feed_key(events.console, 27, "")
    assert hero.money == 5
    assert events.console is None
    assert menu.page == "root"
    assert menu.index == 3
    reset_events()


def test_money_prompt_accepts_typed_amount():
    from lynn.console import feed_key

    reset_events()

    class Hero:
        money = 0

    hero = Hero()
    menu = GodMenu()
    god_menu_open(menu)
    god_menu_begin_prompt(menu, "money", hero)
    con = events.console
    con.text = ""
    feed_key(con, 0, "2")
    feed_key(con, 0, "5")
    feed_key(con, 13, "")
    assert hero.money == 25
    reset_events()


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


def test_money_adds_amount_and_stops_at_the_hud_cap():
    class Hero:
        money = 12

    hero = Hero()
    apply_money(hero)
    assert hero.money == 22
    apply_money(hero, 5)
    assert hero.money == 27
    hero.money = 995
    apply_money(hero)
    assert hero.money == 999
    apply_money(None)


def test_money_clears_healthguy_refuse_sel_seq():
    from lynn.constants import u_healthguy
    from lynn.object.char import CharType

    reset_events()

    class Hero:
        money = 0

    hero = Hero()
    guy = CharType()
    guy.unique_id = u_healthguy
    guy.sel_seq = 2
    events.current_others = [guy]
    apply_money(hero)
    assert hero.money == 10
    assert guy.sel_seq == 0
    reset_events()


def test_heal_refills_or_adds_partial():
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
    hero.hp = 1
    apply_heal(hero, 3)
    assert hero.hp == 4


def test_maxhp_raises_cap_and_current():
    class Hero:
        hp = 6
        maxhp = 6
        dead = 0

    hero = Hero()
    apply_maxhp(hero, 2)
    assert hero.maxhp == 8
    assert hero.hp == 8


def test_caption_names_the_loaded_fixture():
    reset_events()
    events.debug_god = -1
    events.debug_fixture = "postgelidus"
    assert _play_caption() == "Lynn's Legacy [godmode postgelidus]"
    reset_events()
    assert _play_caption() == "Lynn's Legacy"
