"""Divius: flail-only metal, bomb pekkles, kam-bots, haywire guns, Divine."""

import random

import lynn.object  # noqa: F401
import lynn.object.move_ai  # noqa: F401

from lynn import clock
from lynn.constants import (
    DF_MAIN_CHAR,
    TRUE,
    u_charger,
    u_divine_bug,
    u_fbug,
    u_goldblock,
    u_pekkle_grey,
)
from lynn.macros import LLObject_CalculateFrame
from lynn.events import bind_hero, bind_hero_only, bind_room, reset_events
import lynn.events as events
from lynn.gfx.image import LLSystem_FaceType, LLSystem_FrameShell, LLSystem_ImageHeader
from lynn.gfx.menu import MainMenu, menu_bridge_select, scraps_menu_name
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.types import RoomType
from lynn.object.char import CharType
from lynn.object.combat import LLObject_DeriveHurt
from lynn.object.combat_funcs import __flashy
from lynn.object.dispatch import lookup_func
from lynn.object.move_ai import __chase
from lynn.object.projectile import __do_proj
from lynn.object.tick import tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import project_root

OBJ = project_root() / "data" / "object"


def _load(name: str) -> CharType:
    obj = CharType()
    obj.id = f"data/object/{name}"
    return LLSystem_ObjectFromXML(obj, load_images=False)


def _hero_at(x: int, y: int) -> None:
    reset_events()
    hero = ctor_hero()
    only = ctor_hero_only()
    hero.coords_x = x
    hero.coords_y = y
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero(hero)
    bind_hero_only(only)


def _strike(block: CharType, weapon: int, attack_state: int = 0) -> None:
    only = events.hero_only
    only.weapon = weapon
    only.powder = 0
    only.selected_item = 0
    events.hero.attacking = 1 if attack_state else 0
    events.hero.attack_state = attack_state
    block.hp = 1
    block.dmg_id = DF_MAIN_CHAR
    block.dead = 0
    LLObject_DeriveHurt(block)


def test_goldblock_breaks_only_for_the_flail():
    block = _load("goldblock.xml")
    assert block.unique_id == u_goldblock
    assert block.star_weak != 0
    assert block.mace_weak == 0
    _hero_at(0, 0)
    _strike(block, 0)
    assert block.hp == 1
    _strike(block, 1)
    assert block.hp == 1
    _strike(block, 1, attack_state=8)
    assert block.hp == 1
    _strike(block, 1, attack_state=9)
    assert block.hp == 1
    _strike(block, 2)
    assert block.hp == 0


def test_rope_becomes_the_flail_and_leaves_the_scraps_slot_empty():
    _hero_at(0, 0)
    only = events.hero_only
    only.has_weapon = 1
    only.weapon = 1
    only.hasItem[2] = TRUE
    events.now[1206] = TRUE
    gear = _load("gear.xml")
    gear.chap = 680
    assert lookup_func("__give_weapon")(gear) == 1
    assert only.has_weapon == 2
    assert only.weapon == 2
    menu = MainMenu()
    menu.menuNames = [""] * (menu_bridge_select + 1)
    menu.menuNames[menu_bridge_select] = "Some old scraps."
    assert scraps_menu_name(menu, only) == "Nothing left!"


def test_bomb_pekkle_and_kambot_explode_outward():
    _hero_at(0, 0)
    for name in ("pekkle_bomb.xml", "kambot.xml"):
        mob = _load(name)
        mob.coords_x = 100
        mob.coords_y = 80
        assert lookup_func("__make_dead")(mob) == 1
        assert mob.dead == TRUE
        assert mob.coords_x == 76
        assert mob.coords_y == 56
        assert mob.perimeter_x == 64
        assert mob.perimeter_y == 64
        assert mob.strength == 3


def test_dark_pekkle_explosion_plays_the_up_facing_strip():
    """explosion.spr frame 0 is blank. A sideways facing indexes past the sheet."""
    mob = _load("pekkle_bomb.xml")
    mob.direction = 2
    mob.proj_style = 4
    mob.fly_x = 3
    mob.strength = 1
    assert mob.animControl[mob.dead_anim].dir_frames == 5
    assert lookup_func("__make_dead")(mob) == 1
    assert mob.direction == 0
    assert mob.animating == 1
    assert mob.proj_style == 0
    assert mob.fly_x == 0
    assert mob.strength == 3
    assert lookup_func("__active_anim_dead")(mob) == 1
    assert mob.current_anim == mob.dead_anim
    for frame in range(1, 5):
        mob.frame = frame
        assert LLObject_CalculateFrame(mob) == frame
    bug = CharType()
    bug.unique_id = u_fbug
    bug.direction = 1
    bug.proj_style = 7
    bug.strength = 2
    assert lookup_func("__make_dead")(bug) == 1
    assert bug.direction == 0
    assert bug.proj_style == 7
    assert bug.strength == 0
    charger = CharType()
    charger.unique_id = u_charger
    charger.direction = 3
    assert lookup_func("__make_dead")(charger) == 1
    assert charger.direction == 3


def test_kambot_thrusts_only_when_it_reaches_lynn():
    _hero_at(64, 64)
    bot = _load("kambot.xml")
    assert bot.thrust != 0
    assert bot.diag_thrust != 0
    assert bot.thrust_state != 0
    bot.coords_x = 200
    bot.coords_y = 200
    assert __chase(bot) == 0
    assert bot.funcs.active_state != bot.thrust_state
    bot.coords_x = 64
    bot.coords_y = 64
    assert __chase(bot) == 0
    assert bot.funcs.active_state == bot.thrust_state


def test_haywire_shot_loops_back_to_the_align():
    bot = _load("haywire.xml")
    assert lookup_func("__return_jump_1") is not lookup_func("__noop")
    bot.funcs.active_state = bot.jump_state
    bot.funcs.current_func[bot.jump_state] = 5
    assert lookup_func("__return_jump_1")(bot) == 0
    assert bot.funcs.active_state == bot.jump_state
    assert bot.funcs.current_func[bot.jump_state] == 1


def test_red_pekkle_shot_is_an_eight_in_ten_roll():
    pekkle = _load("pekkle_red.xml")
    assert pekkle.projectile is not None
    rolls = iter([0.0, 0.15, 0.25])
    real = random.random
    random.random = lambda: next(rolls)
    try:
        assert lookup_func("__cond_trigger_projectile")(pekkle) == 1
        assert pekkle.projectile.active == 0
        assert lookup_func("__cond_trigger_projectile")(pekkle) == 1
        assert pekkle.projectile.active == 0
        assert lookup_func("__cond_trigger_projectile")(pekkle) == 1
        assert pekkle.projectile.active == pekkle.proj_style
    finally:
        random.random = real


def _statue_face() -> tuple[CharType, LLSystem_FaceType]:
    statue = _load("divine.xml")
    face = LLSystem_FaceType()
    frame = LLSystem_FrameShell(faces=1, face=[face])
    anim = LLSystem_ImageHeader(frame=[frame])
    statue.anim = [anim]
    return statue, face


def test_divine_sends_the_ball_down_lynns_side_and_locks_its_faces():
    _hero_at(336, 40)
    room = RoomType()
    room.x = 40
    statue, face = _statue_face()
    ball = _load("divine_ball.xml")
    ball.hp = 5
    others = [CharType() for _ in range(20)]
    others.append(statue)
    others.append(ball)
    bind_room(room, others)
    assert lookup_func("__divine_fireball")(statue) == 1
    assert ball.funcs.active_state == 1
    assert ball.walk_buffer == ball.walk_length
    assert ball.direction == 6
    assert face.invincible == -1
    events.hero.coords_x = 16
    assert lookup_func("__divine_fireball")(statue) == 1
    assert ball.direction == 7


def test_divine_ball_returns_home_and_unlocks_the_statue():
    _hero_at(0, 0)
    statue, face = _statue_face()
    face.invincible = -1
    ball = _load("divine_ball.xml")
    ball.coords_x = 40
    ball.coords_y = 80
    others = [CharType() for _ in range(20)]
    others.append(statue)
    others.append(ball)
    bind_room(RoomType(), others)
    assert lookup_func("__divine_ball_return")(ball) == 1
    assert (ball.coords_x, ball.coords_y) == (152, 24)
    ball.projectile.travelled = ball.projectile.length - 1
    ball.projectile.refreshTime = 0
    ball.projectile.active = ball.proj_style
    clock.timer = 0
    __do_proj(ball)
    assert ball.projectile.active == 0
    assert face.invincible == 0


def test_divine_death_wakes_the_bug_and_the_bug_drops_the_shells():
    _hero_at(0, 0)
    statue = _load("divine.xml")
    ball = _load("divine_ball.xml")
    ball.hp = 5
    bug = _load("divine_bug.xml")
    bug.invisible = 1
    shells = []
    for _ in range(20):
        shell = CharType()
        shell.hp = 3
        shells.append(shell)
    others = shells + [statue, ball, bug]
    bind_room(RoomType(), others)
    assert lookup_func("__make_dead")(statue) == 1
    assert ball.hp == 0
    assert bug.funcs.active_state == 1
    assert bug.invisible == 0
    for shell in shells:
        shell.hp = 3
    shells[6].hp = 9
    assert lookup_func("__make_dead")(bug) == 1
    for index, shell in enumerate(shells):
        if index == 6:
            assert shell.hp == 9
        else:
            assert shell.hp == 0


def test_divine_second_form_fights_as_soon_as_it_appears():
    """The statue wakes enemy 22 before happen 681 reloads the real bug.

    That shift hits the null placeholder. The reload must leave the bug in
    its walk state, or the room stays sealed on an idle body.
    """
    from lynn.demos import MapDemo, set_up_room_enemies
    from lynn.gfx.palette import load_pal
    from lynn.map.loader import load_mapV
    from lynn.paths import data_file, resolve_map_path

    _hero_at(160, 180)
    game_map = load_mapV(str(resolve_map_path("divius")), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    set_up_room_enemies(demo, 118, load_images=False)
    objs = demo.objects_by_room[118]
    room = game_map.room[118]
    bind_room(room, objs)
    statue = objs[20]
    bug = objs[22]
    assert bug.unique_id != u_divine_bug
    statue.hp = 0
    woke = False
    for i in range(2500):
        clock.timer = i / 200.0
        tick_objects(objs)
        if bug.unique_id == u_divine_bug and events.now[681] != 0:
            woke = True
            break
    assert woke
    assert bug.funcs.active_state == bug.reset_state
    assert bug.reset_state == 1
    assert bug.invisible == 0
    assert bug.hp == 30
    assert bug.funcs.func[bug.funcs.active_state][0].__name__ == "__randomize_path"


def test_divine_victory_chapter_card_transfers_to_logosta():
    from lynn.demos import MapDemo, consume_title_events, set_up_room_enemies
    from lynn.gfx.box import BoxControl
    from lynn.gfx.palette import load_pal
    from lynn.map.loader import load_mapV
    from lynn.object.tick import LLObject_CheckSpawn
    from lynn.paths import data_file, resolve_map_path
    from lynn.sequence import play_sequence

    _hero_at(160, 180)
    clock.timer = 0
    game_map = load_mapV(str(resolve_map_path("divius")), load_tileset=False)
    demo = MapDemo(
        palette=load_pal(data_file("palette", "ll.pal")),
        game_map=game_map,
        tile_surfs=[],
        load_images=0,
        load_tileset=0,
    )
    demo.objects_by_room = [[] for _ in game_map.room]
    demo.hero = events.hero
    demo.hero_only = events.hero_only
    demo.hero_room = 118
    demo.box = BoxControl()
    set_up_room_enemies(demo, 118, load_images=False)
    objs = demo.objects_by_room[118]
    bind_room(game_map.room[118], objs)

    statue, bug = objs[20], objs[22]
    statue.hp = 0
    for i in range(2500):
        clock.timer = i / 200.0
        tick_objects(objs)
        if bug.unique_id == u_divine_bug and events.now[681] != 0:
            break
    assert bug.unique_id == u_divine_bug

    bug.hp = 0
    for _ in range(1200):
        clock.timer += 0.05
        tick_objects(objs)
        if events.pending_seq is not None:
            demo.seq = events.pending_seq
            events.pending_seq = None
            break
    assert demo.seq is not None, "Divine victory sequence did not start"

    seen_maps = []
    saw_chapter_card = False
    for _ in range(8000):
        if demo.seq is not None:
            bind_room(
                demo.game_map.room[demo.hero_room],
                demo.objects_by_room[demo.hero_room],
            )
            if demo.box.activated != 0:
                demo.hero_only.action = TRUE
            clock.timer += 0.05
            demo.seq = play_sequence(demo.seq, demo.box, demo.hero_only)
            demo.hero_only.action = 0
            for obj in demo.objects_by_room[demo.hero_room]:
                LLObject_CheckSpawn(obj)

        if demo.game_map.filename.endswith("between.map"):
            card = next(
                (
                    obj
                    for obj in demo.objects_by_room[demo.hero_room]
                    if obj.id.replace("\\", "/").endswith("chapters.xml")
                ),
                None,
            )
            saw_chapter_card |= card is not None and card.current_anim == 1

        if demo.seq is None:
            old_map = demo.game_map.filename
            consume_title_events(demo)
            if demo.game_map.filename != old_map:
                seen_maps.append(
                    demo.game_map.filename.replace("\\", "/").rsplit("/", 1)[-1]
                )
            elif not demo.hero.to_map:
                break
    else:
        raise AssertionError(
            f"Divine portal sequence stalled on {demo.game_map.filename}, "
            f"command {demo.seq.current_command if demo.seq is not None else 'map change'}"
        )

    assert seen_maps == ["between.map", "l_entry.map"]
    assert saw_chapter_card
    assert demo.seq is None
    assert demo.hero.invisible == 0


def test_tick_leaves_actors_the_running_sequence_command_animates():
    from types import SimpleNamespace

    from lynn.object.tick import tick_objects

    seed = _load("seedbig.xml")
    seed.mod_lock = 1
    ent = SimpleNamespace(active_ent=0)
    seq = SimpleNamespace(
        current_command=0, commands=1, ent=[seed], Command=[SimpleNamespace(ent=[ent])]
    )
    calls = []
    seed.funcs.func[seed.funcs.active_state][0] = lambda this: calls.append(1) or 0
    reset_events()
    events.current_seq = seq
    tick_objects([seed])
    assert calls == []
    events.current_seq = None
    tick_objects([seed])
    assert calls == [1]


def test_divine_ending_hides_the_room_tiles():
    _hero_at(0, 0)
    lynn = _load("lynn.xml")
    assert lookup_func("__turn_off_tiles")(lynn) == 1
    assert events.tiles_disabled == TRUE
    assert lookup_func("__turn_on_tiles")(lynn) == 1
    assert events.tiles_disabled == 0


def test_grey_pekkle_keeps_its_hit_after_the_flash():
    _hero_at(0, 0)
    clock.timer = 0
    grey = _load("pekkle_grey.xml")
    assert grey.unique_id == u_pekkle_grey
    grey.flash_length = 1
    grey.hurt = 4
    grey.dmg_id = DF_MAIN_CHAR
    __flashy(grey)
    assert grey.dmg_id == 0
    assert grey.hurt == 4
    red = _load("pekkle_red.xml")
    red.flash_length = 1
    red.hurt = 4
    red.dmg_id = DF_MAIN_CHAR
    red.flash_timer = 0
    red.flash_count = 0
    __flashy(red)
    assert red.hurt == 0
    assert red.dmg_id == 0
