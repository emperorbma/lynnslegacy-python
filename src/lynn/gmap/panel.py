"""FB-style clickable property panel for gmap.

Mirrors box_handling.bas: labeled rows you click to edit (setup_bounds /
click_bounds), plus a mode strip like set_gmap_controls().
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pygame

from lynn.gmap import ops

DIR_NAMES = ("up", "right", "down", "left")
ENTRY_DIR_NAMES = (
    "up",
    "right",
    "down",
    "left",
    "upleft",
    "upright",
    "downright",
    "downleft",
)

# Mode strip order ≈ FB control column.
MODE_STRIP: tuple[tuple[str, str], ...] = (
    ("paint", "Paint"),
    ("flood", "Flood"),
    ("walk", "Walk"),
    ("ice", "Ice"),
    ("enemy", "Enemy"),
    ("entry", "Entry"),
    ("tele", "Tele"),
    ("seq", "Seq"),
    ("macro", "Macro"),
)

ActionFn = Callable[[], None]


@dataclass
class PanelRow:
    label: str
    action: ActionFn | None = None
    muted: bool = False


@dataclass
class PanelLayout:
    rows: list[PanelRow]
    row_rects: list[pygame.Rect]
    mode_rects: list[tuple[str, pygame.Rect]]
    panel_rect: pygame.Rect
    scroll: int = 0


def _stem(path: str) -> str:
    return Path(str(path).replace("\\", "/")).stem or path


def _regular_box_rows(st: Any, actions: dict[str, ActionFn]) -> list[PanelRow]:
    """FB regular_box — room props + view toggles (shown in paint, or after mode box)."""
    room = st.room
    return [
        PanelRow(f"├ Song: {room.song}", actions.get("room_song")),
        PanelRow(f"├ Darkness: {room.dark}", actions.get("room_dark")),
        PanelRow(f"├ Changes song: {room.song_changes}", actions.get("room_song_changes")),
        PanelRow(f"├ Changes to: {room.changes_to}", actions.get("room_changes_to")),
        PanelRow(
            f"├ Parallax: {'yes' if room.parallax else 'no'}"
            + (f" ({_stem(room.para_filename)})" if room.para_filename else ""),
            actions.get("room_parallax"),
        ),
        PanelRow(f"├ Layer: {st.layer}  (click cycle)", actions.get("layer_cycle")),
        PanelRow(
            f"├ Zoom: {st.zoom}x  Grid:{int(st.show_grid)} "
            f"Walk:{int(st.show_walk)} Solo:{int(st.solo)}",
            actions.get("toggle_zoom"),
        ),
        PanelRow("│  Toggle tile grid", actions.get("toggle_grid")),
        PanelRow("│  Toggle walk grid", actions.get("toggle_walk")),
        PanelRow("│  Toggle layer solo", actions.get("toggle_solo")),
    ]


def build_rows(st: Any, actions: dict[str, ActionFn]) -> list[PanelRow]:
    """Build the FB box contents for the current mode.

    Like FB current_box, mode-specific fields come first so they fit without scrolling.
    regular_box room fields follow (always reachable via scroll / paint mode).
    """
    room = st.room
    rows: list[PanelRow] = [
        PanelRow(f"Map: {st.map_path.name}{' *' if st.dirty else ''}", muted=True),
        PanelRow(
            f"Room [{st.room_i}/{max(0, st.game_map.rooms - 1)}]  {room.x}x{room.y}",
            actions.get("jump_room"),
        ),
        PanelRow(f"Layer {st.layer}  Zoom {st.zoom}x  Brush {st.brush}", muted=True),
        PanelRow("", muted=True),
    ]

    mode = st.mode
    if mode == "paint":
        rows.extend(_regular_box_rows(st, actions))
        rows.extend(
            [
                PanelRow("", muted=True),
                PanelRow("Paint layer with brush", muted=True),
                PanelRow("├ Eyedrop (Alt / RMB)", muted=True),
                PanelRow("├ Layer fill", actions.get("layer_fill")),
                PanelRow("├ Load tileset", actions.get("load_tileset")),
                PanelRow("├ Redimension room", actions.get("redim")),
            ]
        )
    elif mode == "flood":
        rows.append(PanelRow(f"Flood fill brush={st.brush} — click map", muted=True))
    elif mode == "walk":
        rows.extend(
            [
                PanelRow(f"Walkables on layer {st.layer}", muted=True),
                PanelRow("├ Click 8×8 quad to toggle", muted=True),
                PanelRow("├ Mid-click line start/end", muted=True),
                PanelRow(
                    f"├ Line start: {st.walk_line_start or '—'}",
                    muted=True,
                ),
            ]
        )
    elif mode == "ice":
        rows.extend(
            [
                PanelRow("Ice on layer 0", muted=True),
                PanelRow("├ Click tile to toggle", muted=True),
                PanelRow("├ Clear all ice", actions.get("ice_clear")),
                PanelRow("├ Fill all ice", actions.get("ice_fill")),
            ]
        )
    elif mode == "enemy":
        rows.append(
            PanelRow(
                f"Enemy #{st.enemy_sel}/{max(0, room.enemies - 1)}",
                actions.get("enemy_cycle"),
            )
        )
        if 0 <= st.enemy_sel < len(room.enemy):
            e = room.enemy[st.enemy_sel]
            dname = DIR_NAMES[e.direction & 3] if e.direction < 4 else str(e.direction)
            rows.extend(
                [
                    PanelRow(f"├ Name: {_stem(e.id)}", actions.get("enemy_id")),
                    PanelRow(f"├ x: {e.x_origin}  y: {e.y_origin}", muted=True),
                    PanelRow(f"├ Direction: {dname}", actions.get("enemy_dir")),
                    PanelRow(f"├ chap: {e.chap}", actions.get("enemy_chap")),
                    PanelRow(f"├ spawn_h: {e.spawn_h}", actions.get("enemy_spawn_h")),
                    PanelRow(f"├ is_h_set: {e.is_h_set}", actions.get("enemy_is_h_set")),
                    PanelRow(f"├ spawn_d: {e.spawn_d}", actions.get("enemy_spawn_d")),
                    PanelRow(f"├ is_d_set: {e.is_d_set}", actions.get("enemy_is_d_set")),
                    PanelRow(
                        f"├ Conditional: {'yes' if e.spawn_cond else 'no'}",
                        actions.get("enemy_spawn_cond"),
                    ),
                ]
            )
            if e.spawn_cond and e.spawn_info is not None:
                info = e.spawn_info
                rows.extend(
                    [
                        PanelRow(f"│  # of waits: {info.wait_n}", actions.get("spawn_wait_n")),
                        PanelRow(f"│  # of kills: {info.kill_n}", actions.get("spawn_kill_n")),
                        PanelRow(f"│  # of actives: {info.active_n}", actions.get("spawn_active_n")),
                        PanelRow("│  Edit wait pair…", actions.get("spawn_edit_wait")),
                        PanelRow("│  Edit kill pair…", actions.get("spawn_edit_kill")),
                        PanelRow("│  Edit active pair…", actions.get("spawn_edit_active")),
                    ]
                )
            rows.extend(
                [
                    PanelRow("├ Add enemy…", actions.get("enemy_add")),
                    PanelRow("├ Delete enemy", actions.get("enemy_del")),
                ]
            )
        else:
            rows.append(PanelRow("├ Add enemy…", actions.get("enemy_add")))
    elif mode == "entry":
        rows.append(
            PanelRow(
                f"Entry #{st.entry_sel}/{max(0, st.game_map.entries - 1)}",
                actions.get("entry_cycle"),
            )
        )
        if 0 <= st.entry_sel < len(st.game_map.entry):
            en = st.game_map.entry[st.entry_sel]
            dname = (
                ENTRY_DIR_NAMES[en.direction]
                if 0 <= en.direction < len(ENTRY_DIR_NAMES)
                else str(en.direction)
            )
            rows.extend(
                [
                    PanelRow(f"├ x: {en.x}  y: {en.y}", muted=True),
                    PanelRow(f"├ To Room: {en.room}", actions.get("entry_room")),
                    PanelRow(f"├ Character will face: {dname}", actions.get("entry_dir")),
                    PanelRow(f"├ seq_here: {en.seq_here}", muted=True),
                    PanelRow("├ Add entry", actions.get("entry_add")),
                    PanelRow("├ Delete entry", actions.get("entry_del")),
                ]
            )
        else:
            rows.append(PanelRow("├ Add entry", actions.get("entry_add")))
    elif mode == "tele":
        rows.append(
            PanelRow(
                f"Tele #{st.tele_sel}/{max(0, room.teleports - 1)}  phase {st.tele_phase}",
                actions.get("tele_cycle"),
            )
        )
        if 0 <= st.tele_sel < len(room.teleport):
            tp = room.teleport[st.tele_sel]
            rows.extend(
                [
                    PanelRow("[Start]", muted=True),
                    PanelRow(f"├ x: {tp.x}", actions.get("tele_x")),
                    PanelRow(f"├ y: {tp.y}", actions.get("tele_y")),
                    PanelRow(f"├ w: {tp.w}", actions.get("tele_w")),
                    PanelRow(f"├ h: {tp.h}", actions.get("tele_h")),
                    PanelRow("[Destination]", muted=True),
                    PanelRow(f"├ dx: {tp.dx}", actions.get("tele_dx")),
                    PanelRow(f"├ dy: {tp.dy}", actions.get("tele_dy")),
                    PanelRow(f"├ dd: {tp.dd}", actions.get("tele_dd")),
                    PanelRow(
                        f"├ Room: {tp.to_room}" if not tp.to_map else f"├ Entry: {tp.to_room}",
                        actions.get("tele_to_room"),
                    ),
                    PanelRow(f"├ Map: {tp.to_map or '—'}", actions.get("tele_to_map")),
                    PanelRow(f"├ Song: {tp.to_song}", actions.get("tele_song")),
                    PanelRow("├ Add teleport", actions.get("tele_add")),
                    PanelRow("├ Delete teleport", actions.get("tele_del")),
                    PanelRow("├ Begin dest place…", actions.get("tele_dest_phase")),
                ]
            )
        else:
            rows.append(PanelRow("├ Add teleport", actions.get("tele_add")))
    elif mode == "seq":
        owner = ops.seq_list_for(
            st.game_map, room, st.seq_src, st.enemy_sel, st.entry_sel
        )
        rows.extend(
            [
                PanelRow(f"Sequence source: {st.seq_src}", actions.get("seq_src")),
                PanelRow(
                    f"Sequence #{st.seq_sel}/{max(0, owner.seq_here - 1)}",
                    actions.get("seq_cycle"),
                ),
                PanelRow("├ Add sequence", actions.get("seq_add")),
                PanelRow("├ Delete sequence", actions.get("seq_del")),
            ]
        )
        if owner.seq:
            seq = owner.seq[min(st.seq_sel, len(owner.seq) - 1)]
            rows.append(PanelRow(f"├ Entities: {seq.ents}", actions.get("seq_ents")))
            if seq.ent_code:
                i = min(st.seq_ent_sel, len(seq.ent_code) - 1)
                rows.append(
                    PanelRow(
                        f"│  ent_code[{i}]: {seq.ent_code[i]}",
                        actions.get("seq_ent_code"),
                    )
                )
            rows.append(
                PanelRow(
                    f"├ Commands: {seq.commands}  sel={st.seq_cmd_sel}",
                    actions.get("seq_cmd_cycle"),
                )
            )
            rows.append(PanelRow("│  Add command", actions.get("seq_cmd_add")))
            rows.append(PanelRow("│  Delete command", actions.get("seq_cmd_del")))
            if seq.Command:
                cmd = seq.Command[min(st.seq_cmd_sel, len(seq.Command) - 1)]
                rows.append(
                    PanelRow(
                        f"├ Blocks: {cmd.ents}  sel={st.seq_block_sel}",
                        actions.get("seq_block_cycle"),
                    )
                )
                rows.append(PanelRow("│  Add block", actions.get("seq_block_add")))
                rows.append(PanelRow("│  Delete block", actions.get("seq_block_del")))
                if cmd.ent:
                    block = cmd.ent[min(st.seq_block_sel, len(cmd.ent) - 1)]
                    rows.append(PanelRow("[Command block]", muted=True))
                    for field in ops.COMMAND_DATA_FIELDS:
                        cur = getattr(block, field)
                        preview = repr(cur) if isinstance(cur, str) else str(cur)
                        if len(preview) > 28:
                            preview = preview[:25] + "..."
                        rows.append(
                            PanelRow(
                                f"├ {field}: {preview}",
                                actions.get(f"block:{field}"),
                            )
                        )
    elif mode == "macro":
        rows.extend(
            [
                PanelRow(f"Macros: {len(st.macros)}  sel={st.macro_sel}", actions.get("macro_cycle")),
                PanelRow("├ Add macro (brush fill)", actions.get("macro_add")),
                PanelRow("├ Delete macro", actions.get("macro_del")),
                PanelRow("├ Clear macro", actions.get("macro_clear")),
                PanelRow("├ Wall macro (layer 1 border)", actions.get("macro_wall")),
                PanelRow("├ Capture 6×6 (Ctrl+click map)", muted=True),
                PanelRow("├ Stamp (click map)", muted=True),
            ]
        )

    # Room props reachable from non-paint modes via scroll (FB still has regular_box).
    if mode != "paint":
        rows.append(PanelRow("", muted=True))
        rows.append(PanelRow("[Room props]", muted=True))
        rows.extend(_regular_box_rows(st, actions))

    rows.extend(
        [
            PanelRow("", muted=True),
            PanelRow("├ Save map", actions.get("save")),
            PanelRow("├ Load map…", actions.get("load")),
            PanelRow("├ Add room", actions.get("room_add")),
            PanelRow("├ Delete room", actions.get("room_del")),
        ]
    )
    return rows


def draw_panel(
    canvas: pygame.Surface,
    font: pygame.font.Font,
    panel_rect: pygame.Rect,
    st: Any,
    rows: list[PanelRow],
    scroll: int = 0,
    hover: tuple[int, int] | None = None,
) -> PanelLayout:
    pygame.draw.rect(canvas, (22, 22, 30), panel_rect)
    pygame.draw.rect(canvas, (90, 90, 120), panel_rect, 1)

    mode_rects: list[tuple[str, pygame.Rect]] = []
    x = panel_rect.x + 4
    y = panel_rect.y + 4
    for key, label in MODE_STRIP:
        surf = font.render(label, True, (20, 20, 24) if st.mode == key else (210, 210, 220))
        pad = 4
        r = pygame.Rect(x, y, surf.get_width() + pad * 2, surf.get_height() + 2)
        if r.right > panel_rect.right - 4:
            x = panel_rect.x + 4
            y += r.height + 2
            r.topleft = (x, y)
        bg = (220, 200, 90) if st.mode == key else (40, 40, 55)
        if hover and r.collidepoint(hover):
            bg = (255, 230, 120) if st.mode == key else (60, 60, 80)
        pygame.draw.rect(canvas, bg, r, border_radius=2)
        canvas.blit(surf, (r.x + pad, r.y + 1))
        mode_rects.append((key, r))
        x = r.right + 4

    y = max(y + 22, panel_rect.y + 40)
    row_h = font.get_height() + 2
    visible = max(1, (panel_rect.bottom - y - 4) // row_h)
    scroll = max(0, min(scroll, max(0, len(rows) - visible)))
    row_rects: list[pygame.Rect] = [pygame.Rect(0, 0, 0, 0) for _ in rows]

    for i, row in enumerate(rows[scroll : scroll + visible]):
        idx = scroll + i
        ry = y + i * row_h
        rect = pygame.Rect(panel_rect.x + 4, ry, panel_rect.width - 8, row_h)
        row_rects[idx] = rect
        if row.action and hover and rect.collidepoint(hover):
            pygame.draw.rect(canvas, (45, 45, 65), rect)
        color = (140, 140, 155) if row.muted or row.action is None else (230, 230, 240)
        if row.label:
            canvas.blit(font.render(row.label, True, color), (rect.x + 2, rect.y))

    if scroll > 0 or scroll + visible < len(rows):
        hint = font.render(
            f"[{scroll + 1}-{min(len(rows), scroll + visible)}/{len(rows)}] wheel/Ctrl+Pg",
            True,
            (150, 150, 170),
        )
        canvas.blit(hint, (panel_rect.x + 6, panel_rect.bottom - hint.get_height() - 2))

    return PanelLayout(
        rows=rows,
        row_rects=row_rects,
        mode_rects=mode_rects,
        panel_rect=panel_rect,
        scroll=scroll,
    )


def hit_panel(layout: PanelLayout, mx: int, my: int) -> str | int | None:
    """Return mode key str, row index int, or None."""
    for key, rect in layout.mode_rects:
        if rect.collidepoint(mx, my):
            return key
    for i, rect in enumerate(layout.row_rects):
        if rect.width > 0 and rect.collidepoint(mx, my):
            row = layout.rows[i]
            if row.action is not None:
                return i
    return None
