"""Tests for gmap FB-style property panel rows and wall macro."""

from types import SimpleNamespace
from pathlib import Path

from lynn.gmap import ops
from lynn.gmap.actions import make_actions
from lynn.gmap.panel import MODE_STRIP, build_rows, hit_panel, PanelLayout, PanelRow
from lynn.map.types import RoomType
import pygame


def _room(w=8, h=6, fill=1) -> RoomType:
    room = RoomType(x=w, y=h)
    n = ops.layer_len(w, h)
    room.layout = [[fill] * n for _ in range(3)]
    room.room_elem = w * (h + 1) + 1
    return room


def _state(mode="paint"):
    room = _room()
    game_map = SimpleNamespace(
        rooms=1,
        room=[room],
        entries=0,
        entry=[],
        tileset_filename="data/pictures/tiles/forest.spr",
    )
    return SimpleNamespace(
        game_map=game_map,
        map_path=Path("data/map/test.map"),
        room_i=0,
        room=room,
        layer=0,
        zoom=1,
        brush=3,
        dirty=False,
        mode=mode,
        show_grid=True,
        show_walk=False,
        solo=False,
        enemy_sel=0,
        entry_sel=0,
        tele_sel=0,
        tele_phase=0,
        seq_src="room",
        seq_sel=0,
        seq_ent_sel=0,
        seq_cmd_sel=0,
        seq_block_sel=0,
        walk_line_start=None,
        macros=[],
        macro_sel=0,
        macro_walk_edit=False,
        panel_scroll=0,
    )


def test_mode_strip_covers_all_editor_modes():
    keys = [k for k, _ in MODE_STRIP]
    assert keys == [
        "paint",
        "flood",
        "walk",
        "ice",
        "enemy",
        "entry",
        "tele",
        "seq",
        "macro",
    ]


def test_build_rows_regular_box_fields_clickable():
    st = _state("paint")
    nop = lambda: None
    actions = {
        "jump_room": nop,
        "room_song": nop,
        "room_dark": nop,
        "room_song_changes": nop,
        "room_changes_to": nop,
        "room_parallax": nop,
        "layer_cycle": nop,
        "toggle_zoom": nop,
        "toggle_grid": nop,
        "toggle_walk": nop,
        "toggle_solo": nop,
        "layer_fill": nop,
        "load_tileset": nop,
        "redim": nop,
        "save": nop,
        "load": nop,
        "room_add": nop,
        "room_del": nop,
    }
    rows = build_rows(st, actions)
    labels = [r.label for r in rows]
    assert any(l.startswith("├ Song:") for l in labels)
    assert any(l.startswith("├ Darkness:") for l in labels)
    assert any("Layer fill" in l for l in labels)
    assert any(r.action is actions["room_song"] for r in rows)
    assert any(r.action is actions["layer_fill"] for r in rows)


def test_build_rows_enemy_and_seq_modes():
    st = _state("enemy")
    rows = build_rows(st, {})
    assert any("Enemy #" in r.label for r in rows)
    # Mode box precedes room props so it fits without scrolling.
    labels = [r.label for r in rows]
    assert labels.index(next(l for l in labels if "Enemy #" in l)) < labels.index(
        next(l for l in labels if l.startswith("├ Song:"))
    )
    st.mode = "seq"
    rows = build_rows(st, {})
    assert any("Sequence source" in r.label for r in rows)


def test_macro_mode_shows_clear_and_wall_near_top():
    st = _state("macro")
    rows = build_rows(st, {"macro_clear": lambda: None, "macro_wall": lambda: None})
    labels = [r.label for r in rows]
    assert any("Clear macro" in l for l in labels)
    assert any("Wall macro" in l for l in labels)
    # First ~12 rows should include macro actions (visible without scroll).
    top = "\n".join(labels[:12])
    assert "Clear macro" in top
    assert "Wall macro" in top


def test_make_actions_registers_panel_keys():
    st = _state()
    ctx = {
        "st": st,
        "flash": lambda _m: None,
        "save": lambda: None,
        "save_as": lambda: None,
        "load": lambda: None,
        "new_map": lambda: None,
        "pick_object": lambda: None,
        "pick_tileset": lambda: None,
        "pick_parallax": lambda: None,
        "redim": lambda: None,
    }
    actions = make_actions(ctx)
    for key in (
        "jump_room",
        "room_song",
        "layer_fill",
        "enemy_cycle",
        "entry_add",
        "tele_add",
        "seq_add",
        "macro_clear",
        "macro_wall",
        "macro_walk_toggle",
        "toggle_zoom",
        "parallax_toggle",
        "save",
        "save_as",
        "load",
        "new_map",
    ):
        assert key in actions
        assert callable(actions[key])
    for field in ops.COMMAND_DATA_FIELDS:
        assert f"block:{field}" in actions


def test_hit_panel_mode_and_row():
    pygame.init()
    rows = [
        PanelRow("muted", muted=True),
        PanelRow("edit me", action=lambda: None),
    ]
    layout = PanelLayout(
        rows=rows,
        row_rects=[
            pygame.Rect(0, 0, 0, 0),
            pygame.Rect(10, 40, 100, 14),
        ],
        mode_rects=[("paint", pygame.Rect(10, 10, 40, 14))],
        panel_rect=pygame.Rect(0, 0, 200, 200),
        scroll=0,
    )
    assert hit_panel(layout, 15, 12) == "paint"
    assert hit_panel(layout, 20, 45) == 1
    assert hit_panel(layout, 5, 5) is None
    pygame.quit()


def test_wall_macro_sets_border_on_layer_1():
    room = _room(6, 6, fill=0)
    cells = list(range(36))
    ops.wall_macro(room, cells)
    # Top-left corner from cells[0]
    assert room.layout[1][0] & 0xFF == cells[0]
    # Bottom-right from cells[28]
    assert room.layout[1][(room.y - 1) * room.x + (room.x - 1)] & 0xFF == cells[28]
    # Walk bits on inner top edge (y=1)
    assert room.layout[1][1 * room.x + 2] & (ops.LOWER_LEFT | ops.LOWER_RIGHT)


def test_clear_macro_zeros_cells():
    cells = [7] * 36
    ops.clear_macro(cells)
    assert cells == [0] * 36
