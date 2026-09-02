"""Same-map enemy respawn (change_room type 0) and house map teles (type 1)."""

from lynn.constants import TRUE
from lynn.demos import (
    MapDemo,
    del_room_enemies,
    enter_map,
    set_up_room_enemies,
    try_hero_teleport,
)
from lynn.events import now, reset_events
from lynn.gfx.palette import load_pal
from lynn.hero import ctor_hero
from lynn.map.collision import check_teleports
from lynn.map.loader import load_mapV
from lynn.object.tick import tick_objects
from lynn.paths import data_file, resolve_map_path


def _stand_on_tele(hero, tele) -> None:
    hero.coords_x = tele.x
    hero.coords_y = tele.y
    if tele.w == 0:
        hero.coords_x = tele.x - (hero.perimeter_x >> 1)
    else:
        hero.coords_x = tele.x
    if tele.h == 0:
        hero.coords_y = tele.y - (hero.perimeter_y >> 1)
    else:
        hero.coords_y = tele.y - hero.perimeter_y + 1


def _bare_demo(map_stem: str = "forest_fall") -> MapDemo:
    reset_events()
    path = resolve_map_path(map_stem)
    game_map = load_mapV(str(path), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in game_map.room]
    hero = ctor_hero(load_images=False)
    demo.hero_room = 0
    demo.hero = hero
    return demo


def _roamers(objs):
    return [o for o in objs if o.id.replace("\\", "/").endswith("roamer.xml")]


def _sapling(objs):
    for o in objs:
        if o.id.replace("\\", "/").endswith("sapling.xml"):
            return o
    return None


def test_forest_fall_town_door_is_inhouse_entry():
    m = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False)
    door = m.room[4].teleport[3]
    assert door.to_map.replace("\\", "/").endswith("inhouse.map")
    assert door.to_room == 0
    hut = m.room[2].teleport[3]
    assert hut.to_map.replace("\\", "/").endswith("inhouse.map")
    assert hut.to_room == 7


def test_roamers_respawn_after_leaving_the_room():
    demo = _bare_demo()
    set_up_room_enemies(demo, 1, load_images=False)
    roamers = _roamers(demo.objects_by_room[1])
    assert roamers
    origins = [(o.coords_x, o.coords_y) for o in roamers]
    for o in roamers:
        o.dead = TRUE
        o.hp = 0
    hero = demo.hero
    demo.hero_room = 1
    south = demo.game_map.room[1].teleport[1]
    assert south.to_map == ""
    assert south.to_room == 2
    _stand_on_tele(hero, south)
    assert check_teleports(hero, demo.game_map.room[1].teleport) == 1
    try_hero_teleport(demo)
    assert demo.hero_room == 2
    assert demo.objects_by_room[1] == []
    north = demo.game_map.room[2].teleport[0]
    assert north.to_room == 1
    _stand_on_tele(hero, north)
    try_hero_teleport(demo)
    assert demo.hero_room == 1
    again = _roamers(demo.objects_by_room[1])
    assert len(again) == len(origins)
    assert [(o.coords_x, o.coords_y) for o in again] == origins
    assert all(o.dead == 0 for o in again)
    assert all(o.hp > 0 for o in again)


def test_sapling_stays_gone_when_room_respawns():
    demo = _bare_demo()
    now[3] = TRUE
    set_up_room_enemies(demo, 1, load_images=False)
    sapling = _sapling(demo.objects_by_room[1])
    assert sapling is not None
    assert sapling.spawn_kill_trig != 0
    assert sapling.dead != 0


def test_sapling_comes_back_if_happen_3_is_clear():
    demo = _bare_demo()
    set_up_room_enemies(demo, 1, load_images=False)
    sapling = _sapling(demo.objects_by_room[1])
    assert sapling is not None
    assert sapling.spawn_kill_trig == 0
    assert sapling.dead == 0


def test_enter_house_from_town_door():
    demo = _bare_demo()
    hero = demo.hero
    demo.hero_room = 4
    door = demo.game_map.room[4].teleport[3]
    _stand_on_tele(hero, door)
    assert check_teleports(hero, demo.game_map.room[4].teleport) == 3
    try_hero_teleport(demo)
    assert "inhouse" in demo.game_map.filename.replace("\\", "/").lower()
    house = load_mapV(str(resolve_map_path("inhouse")), load_tileset=False)
    entry = house.entry[0]
    assert demo.hero_room == entry.room
    assert (hero.coords_x, hero.coords_y) == (entry.x, entry.y)
    assert hero.direction == entry.direction
    assert hero.to_map == ""


def test_leave_house_returns_to_town():
    demo = _bare_demo()
    enter_map(demo, "inhouse.map", 0, load_images=False, load_tileset=False)
    hero = demo.hero
    door = demo.game_map.room[demo.hero_room].teleport[0]
    assert "forest_fall" in door.to_map.replace("\\", "/").lower()
    _stand_on_tele(hero, door)
    try_hero_teleport(demo)
    assert "forest_fall" in demo.game_map.filename.replace("\\", "/").lower()
    entry = load_mapV(str(resolve_map_path("forest_fall")), load_tileset=False).entry[door.to_room]
    assert demo.hero_room == entry.room
    assert (hero.coords_x, hero.coords_y) == (entry.x, entry.y)


def test_enter_map_keeps_hero_hp():
    demo = _bare_demo()
    demo.hero.hp = 4
    demo.hero.maxhp = 8
    demo.hero.money = 12
    enter_map(demo, "inhouse.map", 7, load_images=False, load_tileset=False)
    assert demo.hero.hp == 4
    assert demo.hero.maxhp == 8
    assert demo.hero.money == 12
    house = load_mapV(str(resolve_map_path("inhouse")), load_tileset=False)
    entry = house.entry[7]
    assert demo.hero_room == entry.room
    assert (demo.hero.coords_x, demo.hero.coords_y) == (entry.x, entry.y)


def test_del_then_setup_replaces_dead_objects():
    demo = _bare_demo()
    set_up_room_enemies(demo, 1, load_images=False)
    first = demo.objects_by_room[1][0]
    first.dead = TRUE
    del_room_enemies(demo, 1)
    assert demo.objects_by_room[1] == []
    set_up_room_enemies(demo, 1, load_images=False)
    assert demo.objects_by_room[1][0] is not first
    assert demo.objects_by_room[1][0].dead == 0


def _town_obj(objs, name: str):
    name = name.lower()
    for obj in objs:
        if obj.id.replace("\\", "/").lower().endswith(name):
            return obj
    return None


def test_town_npcs_park_offscreen_until_grult():
    demo = _bare_demo()
    set_up_room_enemies(demo, 4, load_images=False)
    tick_objects(demo.objects_by_room[4])
    npc = _town_obj(demo.objects_by_room[4], "npc1.xml")
    assert npc is not None
    assert (npc.coords_x, npc.coords_y) == (800, 800)
    portal = _town_obj(demo.objects_by_room[4], "portalw.xml")
    richard = _town_obj(demo.objects_by_room[4], "richard.xml")
    assert portal is not None and richard is not None
    assert (portal.coords_x, portal.coords_y) == (368, 600)
    assert (richard.coords_x, richard.coords_y) == (376, 640)


def test_town_npcs_walk_after_grult_happen():
    demo = _bare_demo()
    now[199] = TRUE
    set_up_room_enemies(demo, 4, load_images=False)
    tick_objects(demo.objects_by_room[4])
    npc = _town_obj(demo.objects_by_room[4], "npc1.xml")
    assert npc is not None
    assert (npc.coords_x, npc.coords_y) == (320, 1000)


def test_wait_spawn_holds_until_happen():
    demo = _bare_demo("moenia")
    set_up_room_enemies(demo, 22, load_images=False)
    gold = _town_obj(demo.objects_by_room[22], "gold.xml")
    assert gold is not None
    assert gold.unique_id == 0
    now[199] = TRUE
    tick_objects(demo.objects_by_room[22])
    gold = _town_obj(demo.objects_by_room[22], "gold.xml")
    assert gold.unique_id == 19
    assert gold.spawn_wait_trig != 0
