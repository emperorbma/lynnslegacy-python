import subprocess
import sys

import lynn.object  # noqa: F401

from lynn import clock
from lynn.constants import (
    DF_MAIN_CHAR,
    PROJECTILE_FIREBALL,
    TRUE,
    u_bardoor,
    u_coldrock,
    u_fkeydoor,
    u_gbutton,
    u_grult,
    u_gtorch,
    u_pushrock,
)
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.hero import ctor_hero_only, item_l_key, item_r_key
from lynn.object.char import CharType
from lynn.object.combat import LLObject_DeriveHurt, start_item_use
from lynn.object.dispatch import lookup_func
from lynn.object.tick import tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import project_root

OBJ = project_root() / "data" / "object"


def _load(name: str) -> CharType:
    obj = CharType()
    obj.id = f"data/object/{name}"
    return LLSystem_ObjectFromXML(obj, load_images=False)


def test_fresh_import_does_not_cycle_through_collision():
    """collision -> object.char used to re-enter boss.py while collision was loading."""
    code = (
        "from lynn.map.collision import check_bounds; "
        "import lynn.object; "
        "from lynn.hero import ctor_hero; "
        "from lynn.object.dispatch import lookup_func; "
        "assert lookup_func('__do_circle') is not lookup_func('__noop')"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(project_root()),
    )
    assert r.returncode == 0, r.stderr


def test_coldrock_and_powder_chest_load():
    rock = _load("coldrock.xml")
    assert rock.unique_id == u_coldrock
    assert rock.invincible != 0
    assert rock.fire_weak != 0
    assert rock.impassable != 0
    chest = _load("bluechestitem.xml")
    assert lookup_func("__give_item") is not lookup_func("__noop")
    assert chest.funcs.func[3][1] is lookup_func("__give_item")


def test_give_item_sets_hasItem():
    reset_events()
    only = ctor_hero_only()
    bind_hero_only(only)
    chest = _load("bluechestitem.xml")
    chest.chap = 0
    assert lookup_func("__give_item")(chest) == 1
    assert only.hasItem[0] == TRUE


def test_flare_powder_lights_unlit_torch():
    reset_events()
    only = ctor_hero_only()
    only.hasItem[0] = TRUE
    only.selected_item = 1
    only.powder = 1
    bind_hero_only(only)
    torch = _load("torch.xml")
    assert lookup_func("__color_up") is not lookup_func("__noop")
    assert lookup_func("__color_down") is not lookup_func("__noop")
    assert torch.torch != 0
    assert torch.fire_weak != 0
    torch.dmg_id = DF_MAIN_CHAR
    LLObject_DeriveHurt(torch)
    assert torch.funcs.active_state == torch.hit_state
    from lynn.object.tick import tick_object

    for i in range(8):
        clock.timer = i * 0.05
        tick_object(torch)
        if torch.current_anim == 1:
            break
    assert torch.current_anim == 1


def test_flare_powder_destroys_coldrock():
    reset_events()
    only = ctor_hero_only()
    only.hasItem[0] = TRUE
    only.selected_item = 1
    only.powder = 1
    bind_hero_only(only)
    rock = _load("coldrock.xml")
    rock.dmg_id = DF_MAIN_CHAR
    LLObject_DeriveHurt(rock)
    assert rock.hp == 0
    tick_objects([rock])
    assert rock.funcs.active_state == rock.death_state


def test_start_item_use_sets_flare_state():
    reset_events()
    from lynn.hero import ctor_hero

    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    only.hasItem[0] = TRUE
    only.selected_item = 1
    bind_hero_only(only)
    start_item_use(hero)
    assert only.attacking == TRUE
    assert hero.attack_state == 8
    assert only.powder == 1


def test_item_cycle_skips_empty_slots():
    only = ctor_hero_only()
    only.hasItem[0] = TRUE
    only.hasItem[2] = TRUE
    only.selected_item = 1
    item_r_key(only)
    assert only.selected_item == 3
    item_l_key(only)
    assert only.selected_item == 1


def test_grult_loads_as_boss():
    boss = _load("grult.xml")
    assert boss.unique_id == u_grult
    assert boss.isBoss != 0
    assert boss.hp == 15
    assert boss.proj_style == PROJECTILE_FIREBALL
    assert boss.radius == 60
    assert lookup_func("__do_circle") is not lookup_func("__noop")
    assert lookup_func("__grult_fireball") is not lookup_func("__noop")
    assert boss.funcs.func[0][0] is lookup_func("__do_circle")
    torch = _load("gtorch.xml")
    assert torch.unique_id == u_gtorch
    assert lookup_func("__big_color_up") is not lookup_func("__noop")
    assert lookup_func("__return_jump") is not lookup_func("__noop")


def test_do_circle_orbits_origin():
    boss = _load("grult.xml")
    boss.x_origin = 100
    boss.y_origin = 100
    boss.coords_x = 100
    boss.coords_y = 100
    boss.degree = 0
    clock.timer = 1.0
    lookup_func("__do_circle")(boss)
    assert boss.coords_x == 100
    assert boss.coords_y == 40


def test_grult_stuns_when_dark_not_4():
    reset_events()
    events.dark = 1
    boss = _load("grult.xml")
    boss.funcs.active_state = 0
    boss.x_origin = 100
    boss.y_origin = 100
    boss.coords_x = 100
    boss.coords_y = 100
    tick_objects([boss])
    assert boss.funcs.active_state == boss.stun_state
    assert boss.coords_x == 100
    assert boss.coords_y == 100


def test_grult_fireball_hitting_gtorch_stuns_boss():
    from lynn.object.boss import LLObject_CheckGTorchLit

    reset_events()
    events.dark = 4
    boss = _load("grult.xml")
    boss.unique_id = u_grult
    boss.coords_x = 100
    boss.coords_y = 100
    boss.x_origin = 100
    boss.y_origin = 100
    boss.funcs.active_state = 0
    lookup_func("__grult_fireball")(boss)
    torch = _load("gtorch.xml")
    torch.coords_x = int(boss.projectile.coords[0][0])
    torch.coords_y = int(boss.projectile.coords[0][1])
    torch.perimeter_x = 16
    torch.perimeter_y = 16
    objs = [boss, torch]
    bind_room(None, objs)
    LLObject_CheckGTorchLit(boss, objs)
    assert events.dark == 1
    assert torch.funcs.active_state == torch.hit_state
    tick_objects(objs)
    assert boss.funcs.active_state == boss.stun_state
    assert (boss.coords_x, boss.coords_y) == (100, 100)


def test_grult_thwack_does_not_slide():
    from lynn.object.combat_funcs import __do_flyback

    reset_events()
    events.dark = 1
    boss = _load("grult.xml")
    boss.coords_x = 100
    boss.coords_y = 80
    boss.fly_x = 1
    boss.fly_y = 1
    boss.hurt = 1
    tick_objects([boss])
    assert boss.funcs.active_state == boss.stun_state
    boss.funcs.active_state = boss.hit_state
    boss.funcs.current_func[boss.hit_state] = 0
    __do_flyback(boss)
    assert boss.coords_x == 100
    assert boss.coords_y == 80
    boss.hurt = 1
    boss.fly_length = 1
    boss.fly_count = 0
    boss.funcs.current_func[boss.hit_state] = 0
    tick_objects([boss])
    tick_objects([boss])
    assert boss.funcs.active_state == boss.stun_state
    assert boss.coords_x == 100
    assert boss.coords_y == 80


def test_gtorch_sets_room_dark():
    reset_events()
    events.dark = 4
    torch = _load("gtorch.xml")
    lookup_func("__big_color_up")(torch)
    assert events.dark == 1
    lookup_func("__big_color_down")(torch)
    assert events.dark == 4


def test_grult_explode_skips_stun_jumps_to_reach_seq():
    from lynn.object.gfx_animation import __explode

    boss = _load("grult.xml")
    assert boss.isBoss != 0
    assert __explode(boss) == 3


def test_grult_death_queues_room_sequence():
    reset_events()
    boss = _load("grult.xml")
    boss.seq = []  # filled below from map
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.gfx.palette import load_pal
    from lynn.hero import ctor_hero, ctor_hero_only
    from lynn.map.loader import load_mapV
    from lynn.paths import data_file, resolve_map_path
    from lynn.object.tick import tick_object

    path = resolve_map_path("moenia")
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    set_up_room_enemies(demo, 22, load_images=False)
    bind_hero(demo.hero)
    bind_hero_only(demo.hero_only)
    objs = demo.objects_by_room[22]
    events.current_others = objs
    grult = next(o for o in objs if o.unique_id == u_grult)
    grult.funcs.active_state = grult.death_state
    grult.funcs.current_func[grult.death_state] = 1
    for i in range(40):
        clock.timer = i * 0.05
        tick_object(grult)
        if events.pending_seq is not None:
            break
    assert events.pending_seq is not None
    assert events.pending_seq.commands == 15


def test_grult_fireball_spawns_at_mouth():
    reset_events()
    hero = CharType()
    hero.coords_x = 200
    hero.coords_y = 200
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero(hero)
    boss = _load("grult.xml")
    boss.coords_x = 100
    boss.coords_y = 100
    lookup_func("__grult_fireball")(boss)
    assert boss.grult_proj_trig != 0
    assert boss.projectile is not None
    assert boss.projectile.coords[0] == [152, 136]
    clock.timer = 1.0
    lookup_func("__do_grult_proj")(boss)
    assert boss.projectile.coords[0] != [152, 136]
    assert boss.fly_x == 0
    assert boss.fly_y == 0


def _open_room(w: int = 20, h: int = 20):
    from lynn.map.types import RoomType

    room = RoomType()
    room.x = w
    room.y = h
    room.layout = [[0] * (w * h) for _ in range(3)]
    return room


def test_pushrock_loads_pushable():
    rock = _load("pushrock.xml")
    assert rock.unique_id == u_pushrock
    assert rock.pushable != 0
    assert rock.impassable != 0
    assert lookup_func("__off_happen") is not lookup_func("__noop")


def test_push_rock_slides_when_lynn_faces_it():
    from lynn.object.move_ai import __push

    reset_events()
    room = _open_room()
    hero = CharType()
    hero.coords_x = 160
    hero.coords_y = 160
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    hero.direction = 1
    rock = _load("pushrock.xml")
    rock.coords_x = 176
    rock.coords_y = 160
    rock.num = 0
    bind_hero(hero)
    bind_room(room, [rock])
    events.keys.right = TRUE
    clock.timer = 1.0
    __push(rock)
    assert rock.coords_x == 177
    assert hero.is_pushing == 2


def test_gbutton_presses_when_rock_overlaps():
    reset_events()
    room = _open_room()
    rock = _load("pushrock.xml")
    rock.coords_x = 80
    rock.coords_y = 80
    button = _load("gbutton.xml")
    button.coords_x = 80
    button.coords_y = 80
    button.chap = 10
    button.num = 1
    objs = [rock, button]
    bind_room(room, objs)
    tick_objects(objs)
    tick_objects(objs)
    assert button.unique_id == u_gbutton
    assert button.funcs.active_state == 1
    assert events.now[10] != 0


def test_chest_loot_funcs_are_implemented():
    chest = _load("chest.xml")
    assert lookup_func("__give_key") is not lookup_func("__noop")
    assert lookup_func("__give_gold_amount") is not lookup_func("__noop")
    assert lookup_func("__play_dead_sound") is not lookup_func("__noop")
    assert lookup_func("__check_key") is not lookup_func("__noop")
    assert chest.funcs.func[1][1] is lookup_func("__give_key")
    assert chest.funcs.func[1][3] is lookup_func("__play_dead_sound")
    assert chest.funcs.func[2][1] is lookup_func("__give_gold_amount")


def test_drop_b_key_is_implemented():
    reset_events()
    only = ctor_hero_only()
    only.b_key = 1
    bind_hero_only(only)
    assert lookup_func("__drop_b_key") is not lookup_func("__noop")
    assert lookup_func("__drop_b_key")(CharType()) == 1
    assert only.b_key == 0


def test_seed_change_map_returns_to_forest_town():
    from lynn.demos import MapDemo, consume_title_events, set_up_room_enemies
    from lynn.gfx.palette import load_pal
    from lynn.hero import ctor_hero, ctor_hero_only
    from lynn.map.loader import load_mapV
    from lynn.paths import data_file, resolve_map_path

    reset_events()
    path = resolve_map_path("moenia")
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    demo.hero_room = 22
    set_up_room_enemies(demo, 22, load_images=False)
    bind_hero(demo.hero)
    bind_hero_only(demo.hero_only)
    bind_room(game_map.room[22], demo.objects_by_room[22])
    demo.hero.chap = 1
    assert lookup_func("__change_map")(demo.hero) == 1
    assert "forest_fall" in (demo.hero.to_map or "").replace("\\", "/").lower()
    demo.seq = None
    consume_title_events(demo)
    assert "forest_fall" in (events.map_filename or "").replace("\\", "/").lower()
    assert events.fade_white == 0
    assert events.fade_black == 0
    assert demo.seq is not None


def test_give_key_and_gold_amount():
    reset_events()
    hero = CharType()
    hero.key = 0
    hero.money = 0
    bind_hero(hero)
    assert lookup_func("__give_key")(CharType()) == 1
    assert hero.key == 1
    pile = CharType()
    pile.chap = 30
    assert lookup_func("__give_gold_amount")(pile) == 1
    assert hero.money == 30


def test_check_key_consumes_or_aborts():
    reset_events()
    hero = CharType()
    hero.key = 0
    bind_hero(hero)
    door = _load("keydoor.xml")
    assert lookup_func("__check_key")(door) == 1
    assert door.return_trig != 0
    assert hero.key == 0
    door.return_trig = 0
    hero.key = 2
    assert lookup_func("__check_key")(door) == 1
    assert hero.key == 1
    assert door.return_trig == 0


def test_moenia_r1_red_chest_gives_key_without_stalling():
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.gfx.box import BoxControl
    from lynn.gfx.palette import load_pal
    from lynn.hero import DIR_UP, ctor_hero, ctor_hero_only
    from lynn.map.loader import load_mapV
    from lynn.paths import data_file, resolve_map_path
    from lynn.sequence import play_sequence, try_action_sequence

    reset_events()
    path = resolve_map_path("moenia")
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    demo.hero.key = 0
    demo.hero.perimeter_x = 16
    demo.hero.perimeter_y = 16
    demo.hero_room = 1
    demo.box = BoxControl()
    set_up_room_enemies(demo, 1, load_images=False)
    bind_hero(demo.hero)
    bind_hero_only(demo.hero_only)
    objs = demo.objects_by_room[1]
    chest = next(o for o in objs if o.id.replace("\\", "/").endswith("chest.xml"))
    demo.hero.direction = DIR_UP
    demo.hero.coords_x = chest.coords_x
    demo.hero.coords_y = chest.coords_y + 16
    demo.hero_only.action = TRUE
    seq = try_action_sequence(demo.hero, demo.hero_only, objs)
    demo.hero_only.action = 0
    assert seq is not None
    for i in range(200):
        clock.timer = i * 0.05
        if demo.box.activated != 0:
            demo.hero_only.action = TRUE
        seq = play_sequence(seq, demo.box, demo.hero_only)
        demo.hero_only.action = 0
        if seq is None:
            break
    else:
        raise AssertionError("Moenia r1 red chest sequence stalled")
    assert demo.hero.key == 1
    assert events.now[150] != 0
    tick_objects(objs)
    assert chest.invisible == 0
    assert chest.current_anim == 1


def test_blit_keeps_opened_chest_visible():
    import pygame
    from lynn.gfx.blit import blit_object

    pygame.display.set_mode((32, 32))
    canvas = pygame.Surface((32, 32))
    canvas.fill((0, 0, 0))
    tile = pygame.Surface((16, 16))
    tile.fill((200, 40, 40))
    chest = CharType()
    chest.coords_x = 0
    chest.coords_y = 0
    chest.current_anim = 1
    chest.spawn_kill_trig = TRUE
    chest.total_dead = TRUE
    chest.invisible = 0
    blit_object(canvas, chest, 0, 0, [tile, tile])
    assert canvas.get_at((8, 8))[0] > 100
    chest.invisible = TRUE
    canvas.fill((0, 0, 0))
    blit_object(canvas, chest, 0, 0, [tile, tile])
    assert canvas.get_at((8, 8))[0] == 0


def test_if_all_dead_waits_for_mobs_then_opens():
    from lynn.events import bind_room
    from lynn.object.tick import tick_object

    reset_events()
    door = _load("bardoor.xml")
    door.unique_id = u_bardoor
    door.chap = 175
    bat = CharType()
    bat.dead = 0
    bat.unique_id = 0
    bind_room(None, [door, bat])
    assert lookup_func("__if_all_dead") is not lookup_func("__noop")
    assert lookup_func("__if_all_dead")(door) == -1
    bat.dead = TRUE
    assert lookup_func("__if_all_dead")(door) == 1
    door.chap = 0
    assert lookup_func("__if_all_dead")(door) == 0


def test_moenia_r0_fkeydoor_vanishes_after_blue_key():
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.gfx.box import BoxControl
    from lynn.gfx.palette import load_pal
    from lynn.hero import ctor_hero, ctor_hero_only
    from lynn.map.loader import load_mapV
    from lynn.object.tick import LLObject_CheckSpawn, tick_objects
    from lynn.paths import data_file, resolve_map_path
    from lynn.sequence import play_sequence, try_touch_sequence

    reset_events()
    path = resolve_map_path("moenia")
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    demo.hero_only.b_key = 1
    demo.hero.perimeter_x = 16
    demo.hero.perimeter_y = 16
    demo.hero_room = 0
    demo.box = BoxControl()
    set_up_room_enemies(demo, 0, load_images=False)
    bind_hero(demo.hero)
    bind_hero_only(demo.hero_only)
    objs = demo.objects_by_room[0]
    door = next(o for o in objs if o.unique_id == u_fkeydoor)
    assert door.impassable != 0
    demo.hero.coords_x = door.coords_x
    demo.hero.coords_y = door.coords_y + 16
    seq = try_touch_sequence(demo.hero, objs)
    assert seq is not None
    for i in range(40):
        clock.timer = i * 0.05
        seq = play_sequence(seq, demo.box, demo.hero_only)
        for obj in objs:
            LLObject_CheckSpawn(obj)
        if seq is None:
            break
    else:
        raise AssertionError("fkeydoor sequence stalled")
    tick_objects(objs)
    assert events.now[104] != 0
    assert door.spawn_kill_trig != 0
    assert door.invisible != 0
    assert door.impassable == 0


def test_moenia_r0_bardoor_opens_when_room_is_clear():
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.events import bind_room
    from lynn.gfx.palette import load_pal
    from lynn.hero import ctor_hero, ctor_hero_only
    from lynn.map.loader import load_mapV
    from lynn.object.tick import tick_objects
    from lynn.paths import data_file, resolve_map_path

    reset_events()
    path = resolve_map_path("moenia")
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    set_up_room_enemies(demo, 0, load_images=False)
    objs = demo.objects_by_room[0]
    bind_hero(demo.hero)
    bind_hero_only(demo.hero_only)
    bind_room(game_map.room[0], objs)
    door = next(o for o in objs if o.unique_id == u_bardoor and o.chap == 175)
    for o in objs:
        if o.unique_id not in (u_bardoor, u_fkeydoor) and o is not door:
            o.dead = TRUE
    for i in range(20):
        clock.timer = i * 0.05
        tick_objects(objs)
        if door.invisible != 0 or door.dead != 0:
            break
    assert door.dead != 0 or door.invisible != 0
    assert events.now[175] != 0
