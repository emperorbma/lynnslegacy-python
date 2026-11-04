"""FB change_room fade FSM: invincible → fade → swap → fade up → vulnerable.

Port overlays (fade_black/white/red) stand in for FB Palette writes. Every
fade-in path must clear them; case 5 snaps leftovers as a safety net.
"""

from lynn import clock
from lynn.constants import LLFADE_GRAY, LLFADE_WHITE
from lynn.demos import MapDemo, set_up_room_enemies, try_hero_teleport
from lynn.events import bind_hero, bind_hero_only, reset_events
import lynn.events as events
from lynn.gfx.palette import load_pal
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.map.change_room import finish_change_room, init_change_room, tick_change_room
from lynn.map.loader import load_mapV
from lynn.object.seq_funcs import __set_gray_fade, __set_white_fade
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
    assert events.fade_black == 0
    assert events.fade_white == 0
    assert events.fade_red == 0


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


def _map_hop_demo(map_name: str) -> MapDemo:
    reset_events()
    path = resolve_map_path(map_name)
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
    demo.hero_room = 0
    set_up_room_enemies(demo, 0, load_images=False)
    bind_hero(demo.hero)
    bind_hero_only(demo.hero_only)
    return demo


def _assert_overlays_clear() -> None:
    assert events.fade_black == 0
    assert events.fade_white == 0
    assert events.fade_red == 0


def test_gray_fade_map_hop_clears_black_overlay():
    """island3 → forest_flashback stick pickup: set_gray_fade then change_map.

    Case 1 still fades out through fade_to_black. Case 3 uses fade_down_to_gray,
    which must lift the port's black overlay or the flashback stays covered.
    """
    demo = _map_hop_demo("island3")
    hero = demo.hero
    only = demo.hero_only
    only.fadeStyle = 0
    __set_gray_fade(hero)
    assert only.fadeStyle & LLFADE_GRAY
    tele = demo.game_map.room[0].teleport[0]
    assert "forest_flashback" in (tele.to_map or "").replace("\\", "/").lower()
    assert tele.to_room == 24
    hero.to_map = tele.to_map
    hero.to_entry = tele.to_room
    hero.switch_room = 0
    hero.fade_time = 0.01
    init_change_room(1)
    clock.timer = 1.0
    finish_change_room(demo)
    assert hero.switch_room == -1
    _assert_overlays_clear()
    assert only.fadeStyle == 0
    stem = (demo.game_map.filename or "").replace("\\", "/").lower()
    assert "forest_flashback" in stem
    assert demo.hero_room == demo.game_map.entry[24].room


def test_white_fade_map_hop_clears_overlays():
    """WHITE style: fade_to_white out, fade_down_to_color in — no leftover wash."""
    demo = _map_hop_demo("island3")
    hero = demo.hero
    only = demo.hero_only
    __set_white_fade(hero)
    assert only.fadeStyle & LLFADE_WHITE
    tele = demo.game_map.room[0].teleport[0]
    hero.to_map = tele.to_map
    hero.to_entry = tele.to_room
    hero.switch_room = 0
    hero.fade_time = 0.01
    init_change_room(1)
    clock.timer = 1.0
    finish_change_room(demo)
    assert hero.switch_room == -1
    _assert_overlays_clear()
    assert only.fadeStyle == 0


def test_fade_in_clears_stale_red_overlay():
    """Death leaves fade_red; a later room hop must not keep the red wash."""
    demo = _demo(1)
    hero = demo.hero
    events.fade_red = 255
    events.fade_black = 255
    south = demo.game_map.room[1].teleport[1]
    hero.coords_x = south.x
    hero.coords_y = south.y
    try_hero_teleport(demo, complete=True)
    _assert_overlays_clear()


def test_gray_fade_ramp_is_grayscale_not_full_color():
    """Mid __fade_down_to_gray must target avg gray, not restore_master color."""
    from lynn.gfx.palette import (
        LLPalette,
        reset_palette_ramps,
        step_fade_down_to_gray,
    )
    from lynn.object.seq_funcs import __fade_down_to_gray

    reset_events()
    reset_palette_ramps()
    pal = LLPalette()
    pal.master = [(0, 0, 0)] * 256
    pal.colors = [(0, 0, 0)] * 256
    pal.master[40] = (200, 40, 10)
    pal.colors[40] = (255, 255, 255)
    events.palette = pal
    events.fade_black = 255
    this = ctor_hero(load_images=False)
    this.fade_time = 0.01
    clock.timer = 1.0
    # First write is still white; after a few steps channels stay equal and drop.
    count = 0
    for _ in range(8):
        count, done = step_fade_down_to_gray(pal, count)
        assert done == 0
    r, g, b = pal.colors[40]
    assert r == g == b
    assert r < 255
    # Color ramp would pull toward master (200,40,10); gray stays equal.
    assert abs(r - g) == 0
    # Full fade-in clears overlays and locks B&W.
    reset_palette_ramps()
    this.fade_count = 0
    for _ in range(200):
        clock.timer += 0.05
        if __fade_down_to_gray(this):
            break
    else:
        raise AssertionError("fade_down_to_gray did not finish")
    _assert_overlays_clear()
    r, g, b = pal.colors[40]
    assert r == g == b
