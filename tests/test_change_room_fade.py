"""FB change_room fade FSM: invincible → fade → swap → fade up → vulnerable."""

from lynn import clock
from lynn.constants import LLFADE_WHITE
from lynn.demos import MapDemo, set_up_room_enemies, try_hero_teleport
from lynn.events import reset_events
import lynn.events as events
from lynn.gfx.palette import load_pal
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.change_room import finish_change_room, tick_change_room
from lynn.map.loader import load_mapV
from lynn.paths import data_file, resolve_map_path


def _demo(room_i: int = 1) -> MapDemo:
    reset_events()
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
    demo.hero = ctor_hero(load_images=False)
    demo.hero_only = ctor_hero_only()
    demo.hero_room = room_i
    set_up_room_enemies(demo, room_i, load_images=False)
    return demo


def test_same_map_tele_fades_before_swap():
    demo = _demo(1)
    hero = demo.hero
    south = demo.game_map.room[1].teleport[1]
    hero.coords_x = south.x
    hero.coords_y = south.y
    clock.timer = 1.0
    try_hero_teleport(demo)
    assert hero.switch_room == 1
    assert hero.invincible != 0
    assert demo.hero_room == 1
    # One fade step darkens; room has not swapped yet.
    clock.timer += 0.01
    tick_change_room(demo)
    assert demo.hero_room == 1
    assert events.fade_black > 0 or hero.fade_out != 0
    finish_change_room(demo)
    assert hero.switch_room == -1
    assert hero.invincible == 0
    assert demo.hero_room == 2
    assert events.fade_black == 0


def test_white_fade_style_is_consumed():
    demo = _demo(1)
    hero = demo.hero
    only = demo.hero_only
    only.fadeStyle = LLFADE_WHITE
    south = demo.game_map.room[1].teleport[1]
    hero.coords_x = south.x
    hero.coords_y = south.y
    try_hero_teleport(demo, complete=True)
    assert only.fadeStyle == 0
    assert demo.hero_room == 2


def test_room_seq_starts_after_fade():
    """forest_fall room 2 carries a room.seq that FB promotes in case 5."""
    demo = _demo(1)
    hero = demo.hero
    south = demo.game_map.room[1].teleport[1]
    assert south.to_room == 2
    assert demo.game_map.room[2].seq
    hero.coords_x = south.x
    hero.coords_y = south.y
    try_hero_teleport(demo, complete=True)
    assert demo.hero_room == 2
    assert demo.seq is not None


def test_map_change_preserves_title_unconscious_anim():
    """Title Begin sets active_anim_1 before change_map; FB enter_map keeps it.

    Resetting to walk anim 0 flashed standing Lynn for a frame after the
    forest_fall fade-up, before the entry seq re-applied anim 1.
    """
    from lynn.map.enter_map import enter_map

    demo = _demo(0)
    hero = demo.hero
    hero.current_anim = 1
    hero.frame = 3
    hero.to_map = "forest_fall.map"
    hero.to_entry = 0
    hero.switch_room = -2
    enter_map(
        demo,
        "forest_fall.map",
        0,
        load_images=False,
        load_tileset=False,
        from_change_room=True,
    )
    assert hero.current_anim == 1
    assert hero.frame == 3


def test_map_hop_enter_map_keeps_hud_on():
    """FB enter_map does not clear do_hud; Arx entry 0 has no seq to restore it."""
    from lynn.constants import TRUE
    from lynn.map.enter_map import enter_map

    demo = _demo(0)
    events.do_hud = TRUE
    demo.do_hud = TRUE
    enter_map(
        demo,
        "arx.map",
        0,
        load_images=False,
        load_tileset=False,
        from_change_room=True,
    )
    assert events.do_hud != 0
    assert demo.do_hud != 0
    assert demo.seq is None
