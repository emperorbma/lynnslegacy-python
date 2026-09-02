"""Title map entry sequence, Begin/Continue/Quit, splash, jump_to_title."""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

import lynn.object  # noqa: F401
import lynn.object.move_ai  # noqa: F401
from lynn import clock
from lynn.constants import SCREEN_H, SCREEN_W, TRUE, u_menu
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.gfx.box import BoxControl
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.save import LLSystem_WriteSaveFile, sequence_LoadGame
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import START_MAP, chdir_project_root, data_file, project_root
from lynn.sequence import play_sequence


@pytest.fixture(scope="module")
def pygame_dummy():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((SCREEN_W, SCREEN_H))
    yield
    pygame.quit()


def _menu_obj() -> CharType:
    obj = CharType()
    obj.id = "data/object/menu.xml"
    LLSystem_ObjectFromXML(obj, load_images=False)
    return obj


def test_menu_xml_is_u_menu_and_has_title_funcs():
    obj = _menu_obj()
    assert obj.unique_id == u_menu
    assert lookup_func("__do_menu") is not lookup_func("__noop")
    assert lookup_func("__do_menu_continue") is not lookup_func("__noop")
    assert lookup_func("__end") is not lookup_func("__noop")
    assert obj.funcs.func[1][0] is lookup_func("__do_menu")
    assert obj.funcs.func[2][0] is lookup_func("__do_menu_continue")


def test_do_menu_begin_sets_return_trig():
    reset_events()
    hero = ctor_hero(load_images=False)
    bind_hero(hero)
    bind_hero_only(ctor_hero_only())
    menu = _menu_obj()
    menu.menu_sel = 0
    clock.timer = 1.0
    events.keys.enter = TRUE
    lookup_func("__do_menu")(menu)
    assert menu.menu_lock != 0
    events.keys.enter = 0
    lookup_func("__do_menu")(menu)
    assert menu.return_trig != 0
    assert hero.menu_sel == 0


def test_do_menu_continue_shifts_to_file_slots():
    reset_events()
    hero = ctor_hero(load_images=False)
    bind_hero(hero)
    bind_hero_only(ctor_hero_only())
    menu = _menu_obj()
    menu.menu_sel = 1
    clock.timer = 1.0
    events.keys.enter = TRUE
    lookup_func("__do_menu")(menu)
    events.keys.enter = 0
    lookup_func("__do_menu")(menu)
    assert menu.state_shift == 2
    assert hero.menu_sel == 2


def test_do_menu_quit_and_escape_request_quit():
    reset_events()
    hero = ctor_hero(load_images=False)
    bind_hero(hero)
    bind_hero_only(ctor_hero_only())
    menu = _menu_obj()
    menu.menu_sel = 2
    clock.timer = 1.0
    events.keys.enter = TRUE
    lookup_func("__do_menu")(menu)
    assert events.request_quit != 0
    reset_events()
    bind_hero(hero)
    events.keys.escape = TRUE
    lookup_func("__do_menu")(menu)
    assert events.request_quit != 0


def test_do_menu_continue_enter_on_occupied_slot_sets_isloading(tmp_path, monkeypatch):
    reset_events()
    chdir_project_root()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    events.map_filename = "forest_fall.map"
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    LLSystem_WriteSaveFile("ll_save1.sav", 2)
    menu = _menu_obj()
    menu.menu_sel = 0
    clock.timer = 1.0
    events.keys.enter_pulse = TRUE
    lookup_func("__do_menu_continue")(menu)
    assert only.isLoading != 0
    assert menu.save and menu.save[0] is not None
    assert menu.save[0].entry == 2


def test_play_sequence_isloading_sets_pending_load(tmp_path, monkeypatch):
    from lynn.map.types import CommandData, CommandType, SequenceType

    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    events.map_filename = "forest_fall.map"
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    LLSystem_WriteSaveFile("ll_save1.sav", 3)
    menu = _menu_obj()
    menu.menu_sel = 0
    clock.timer = 1.0
    events.keys.enter_pulse = TRUE
    lookup_func("__do_menu_continue")(menu)
    seq = SequenceType(ents=1, ent_code=[-1], commands=1)
    seq.ent = [menu]
    cmd = CommandType(ents=1, ent=[CommandData(active_ent=0, ent_state=2)])
    seq.Command = [cmd]
    box = BoxControl()
    result = play_sequence(seq, box, only)
    assert result is None
    assert events.pending_load is not None
    assert events.pending_load.entry == 3
    assert only.isLoading == 0


def test_sequence_load_game_copies_slot(tmp_path, monkeypatch):
    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    hero.hp = 6
    bind_hero(hero)
    bind_hero_only(only)
    events.map_filename = "forest_fall.map"
    events.now[9] = TRUE
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    LLSystem_WriteSaveFile("ll_save2.sav", 4)
    from lynn.object.save import LLSystem_ReadSaveFile

    data = LLSystem_ReadSaveFile(str(tmp_path / "ll_save2.sav"))
    assert data is not None
    data.hp = 12
    data.maxhp = 12
    data.gold = 40
    data.happen = [3]
    sequence_LoadGame(data)
    assert hero.hp == 12
    assert hero.money == 40
    assert hero.to_map == "forest_fall.map"
    assert hero.to_entry == 4
    assert events.now[3] != 0
    assert events.now[9] == 0
    assert hero.menu_sel == 0


def test_title_map_entry_starts_menu_seq(pygame_dummy):
    from lynn.demos import load_map_demo

    chdir_project_root()
    demo = load_map_demo(with_objects=True, map_path=START_MAP)
    assert demo.seq is not None
    assert demo.do_hud == 0
    assert events.do_hud == 0
    assert Path_name(demo.game_map.filename) == START_MAP
    menus = [o for o in demo.objects_by_room[0] if o.unique_id == u_menu]
    assert menus


def Path_name(name: str) -> str:
    from pathlib import Path

    return Path(str(name).replace("\\", "/")).name.lower()


def test_jump_to_title_resets_happen_and_starts_seq():
    from lynn.demos import MapDemo, jump_to_title, set_up_room_enemies
    from lynn.gfx.palette import load_pal
    from lynn.map.loader import load_mapV
    from lynn.paths import resolve_map_path

    reset_events()
    chdir_project_root()
    path = resolve_map_path("forest_fall")
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in game_map.room]
    set_up_room_enemies(demo, 0, load_images=False)
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    demo.hero_only.has_weapon = 0
    demo.hero_only.hasItem[0] = TRUE
    events.now[3] = TRUE
    bind_hero(demo.hero)
    bind_hero_only(demo.hero_only)
    jump_to_title(demo)
    assert all(v == 0 for v in events.now)
    assert Path_name(events.map_filename) == START_MAP
    assert demo.seq is not None
    assert demo.do_hud == 0
    assert demo.hero_only.has_weapon == -1
    assert demo.hero_only.hasItem[0] == 0
    assert demo.hero_only.hasCostume[0] != 0
    assert demo.hero.invisible != 0
    assert demo.hero_only.invisibleEntry == 0


def test_consume_pending_load_enters_saved_map(tmp_path, monkeypatch):
    from lynn.demos import MapDemo, consume_title_events, set_up_room_enemies
    from lynn.gfx.palette import load_pal
    from lynn.map.loader import load_mapV
    from lynn.object.save import LLSystem_ReadSaveFile
    from lynn.paths import resolve_map_path

    reset_events()
    chdir_project_root()
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    events.map_filename = "title.map"
    LLSystem_WriteSaveFile("ll_save1.sav", 13)
    save = LLSystem_ReadSaveFile(str(tmp_path / "ll_save1.sav"))
    assert save is not None
    save.map = "forest_fall.map"
    save.entry = 13
    path = resolve_map_path(START_MAP)
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
        hero=hero,
        hero_only=only,
    )
    demo.objects_by_room = [[] for _ in game_map.room]
    set_up_room_enemies(demo, 0, load_images=False)
    hero.invisible = 1
    only.invisibleEntry = TRUE
    events.pending_load = save
    assert consume_title_events(demo) is False
    assert Path_name(events.map_filename) == "forest_fall.map"
    assert demo.hero_room == 1
    assert demo.hero.menu_sel == 0
    assert demo.hero.invisible == 0
    assert only.invisibleEntry == 0
    assert events.pending_load is None


def test_change_map_from_title_tele_zero_is_forest_fall():
    from lynn.map.loader import load_mapV
    from lynn.object.seq_funcs import __change_map
    from lynn.paths import resolve_map_path

    reset_events()
    m = load_mapV(str(resolve_map_path(START_MAP)), load_tileset=False)
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    bind_room(m.room[0], [])
    actor = CharType()
    actor.chap = 0
    __change_map(actor)
    assert only.dropoutSequence != 0
    assert Path_name(hero.to_map) == "forest_fall.map"
    assert hero.to_entry == 0


def test_title_begin_reaches_forest_fall_change_map():
    from lynn.map.loader import load_mapV
    from lynn.object.xml_load import spawn_from_stub
    from lynn.paths import resolve_map_path
    from lynn.sequence import bind_sequence_ents

    reset_events()
    chdir_project_root()
    m = load_mapV(str(resolve_map_path(START_MAP)), load_tileset=False)
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    objs = [spawn_from_stub(s, load_images=False) for s in m.room[0].enemy]
    bind_hero(hero)
    bind_hero_only(only)
    bind_room(m.room[0], objs)
    seq = m.entry[0].seq[0]
    bind_sequence_ents(seq, hero, objs)
    box = BoxControl()
    menu = objs[0]
    began = False
    for i in range(4000):
        clock.timer = float(i)
        if seq is None:
            break
        if seq.current_command == 1 and not began:
            menu.menu_sel = 0
            events.keys.enter = TRUE
            play_sequence(seq, box, only)
            events.keys.enter = 0
            seq = play_sequence(seq, box, only)
            began = True
            continue
        seq = play_sequence(seq, box, only)
    assert began
    assert seq is None
    assert Path_name(hero.to_map) == "forest_fall.map"
    assert hero.to_entry == 0
    assert only.dropoutSequence == 0


def test_save_slot_preview_draws_status_and_items(pygame_dummy):
    from lynn.constants import SCREEN_H, SCREEN_W
    from lynn.gfx.hud import load_hud
    from lynn.gfx.palette import load_pal
    from lynn.object.save import SaveData, blit_save_menu

    chdir_project_root()
    hud = load_hud(load_pal("data/palette/ll.pal"))
    assert hud.sav_img and hud.sav_img[0]
    canvas = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
    canvas.fill((0, 0, 0))
    menu = CharType()
    menu.menu_sel = 0
    menu.save = [
        SaveData(hp=6, maxhp=6, gold=42, weapon=0, hasItem=[TRUE, 0, 0, 0, 0, 0]),
        None,
        None,
        None,
    ]
    blit_save_menu(canvas, menu, [], hud)
    assert canvas.get_at((32 + 10, 9))[:3] != (0, 0, 0)
    assert canvas.get_at((57 + 6, 26))[:3] != (0, 0, 0)
    assert canvas.get_at((49 + 8 + 4, 8 + 4))[:3] != (0, 0, 0)


def test_splash_image_is_320x200(pygame_dummy):
    from lynn.gfx.splash import load_splash_image

    chdir_project_root()
    splash = load_splash_image()
    assert splash.get_width() == SCREEN_W
    assert splash.get_height() == SCREEN_H
    colors = {
        splash.get_at((x, y))[:3]
        for y in range(0, SCREEN_H, 16)
        for x in range(0, SCREEN_W, 16)
    }
    assert len(colors) > 2
    assert (project_root() / "data" / "pictures" / "splash_screen.bmp").is_file()
