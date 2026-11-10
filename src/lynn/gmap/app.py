"""gmap editor — Screen 19–sized workspace (800×600) like FB gmap.bas.

Covers rooms, layers, paint/flood/fill, teleports, sequences, macros,
enemy edit, room redimension, load/save.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pygame

from lynn.gfx.blit import blit_room_tiles
from lynn.gfx.image import LLSystem_ImageLoad, frame_surfaces
from lynn.gfx.palette import load_pal
from lynn.gmap import ops
from lynn.gmap.prompt import pick_list, prompt_int, prompt_text
from lynn.map.loader import load_mapV
from lynn.map.saver import save_mapV
from lynn.map.types import MapType, RoomType
from lynn.paths import (
    DEFAULT_MAP,
    chdir_project_root,
    data_root,
    resolve_map_path,
)

GMAP_W = 800
GMAP_H = 600
VIEW_W = 512
VIEW_H = 384
TILE_PANEL = (520, 8, 272, 272)
DIR_NAMES = ("up", "right", "down", "left")
MODES = ("paint", "flood", "walk", "ice", "enemy", "entry", "tele", "seq", "macro")
SEQ_SOURCES = ("room", "enemy", "entry")
FLOAT_FIELDS = frozenset({"walk_speed", "fadeTime"})
STRING_FIELDS = frozenset({"text", "to_map"})


@dataclass
class GmapState:
    game_map: MapType
    map_path: Path
    tile_surfs: list
    room_i: int = 0
    layer: int = 0
    cam_x: int = 0
    cam_y: int = 0
    zoom: int = 1
    brush: int = 1
    enemy_sel: int = 0
    tele_sel: int = 0
    entry_sel: int = 0
    seq_sel: int = 0
    seq_ent_sel: int = 0
    seq_cmd_sel: int = 0
    seq_block_sel: int = 0
    seq_src: str = "room"
    tele_phase: int = 0  # 0 place/size, 1 set dest room, 2 place dx/dy
    tele_prev_room: int = 0
    macro_sel: int = 0
    macros: list[list[int]] = field(default_factory=list)
    dirty: bool = False
    status: str = ""
    show_grid: bool = True
    show_walk: bool = False
    solo: bool = False
    mode: str = "paint"
    tileset_scroll: int = 0
    message: str = ""
    message_until: float = 0.0

    @property
    def room(self) -> RoomType:
        return self.game_map.room[self.room_i]


def _load_tiles(game_map: MapType) -> list:
    pal = load_pal("data/palette/ll.pal")
    if game_map.tileset is None and game_map.tileset_filename:
        game_map.tileset = LLSystem_ImageLoad(game_map.tileset_filename)
    if game_map.tileset is None:
        return []
    return frame_surfaces(game_map.tileset, pal)


def _open_map(spec: str | None) -> GmapState:
    path = resolve_map_path(spec or DEFAULT_MAP)
    game_map = load_mapV(str(path), load_tileset=True)
    return GmapState(
        game_map=game_map,
        map_path=path,
        tile_surfs=_load_tiles(game_map),
        status=str(path),
    )


def _flash(st: GmapState, text: str, seconds: float = 2.0) -> None:
    st.message = text
    st.message_until = pygame.time.get_ticks() / 1000.0 + seconds


def _save(st: GmapState) -> None:
    save_mapV(st.map_path, st.game_map)
    st.dirty = False
    _flash(st, f"Saved {st.map_path.name}")


def _clamp_cam(st: GmapState) -> None:
    room = st.room
    max_x = max(0, room.x * 16 - VIEW_W // st.zoom)
    max_y = max(0, room.y * 16 - VIEW_H // st.zoom)
    st.cam_x = max(0, min(st.cam_x, max_x))
    st.cam_y = max(0, min(st.cam_y, max_y))


def _view_to_world(st: GmapState, mx: int, my: int) -> tuple[int, int] | None:
    if mx < 0 or my < 0 or mx >= VIEW_W or my >= VIEW_H:
        return None
    return st.cam_x + mx // st.zoom, st.cam_y + my // st.zoom


def _scale_mouse(pos: tuple[int, int]) -> tuple[int, int]:
    mx, my = pos
    win = pygame.display.get_surface()
    if win is not None and win.get_size() != (GMAP_W, GMAP_H):
        sx = GMAP_W / win.get_width()
        sy = GMAP_H / win.get_height()
        return int(mx * sx), int(my * sy)
    return mx, my


def _paint_at(st: GmapState, wx: int, wy: int) -> None:
    room = st.room
    tx, ty = wx // 16, wy // 16
    if tx < 0 or ty < 0 or tx >= room.x or ty >= room.y:
        return
    idx = ty * room.x + tx
    layout = room.layout[st.layer]
    if idx >= len(layout):
        return
    layout[idx] = (layout[idx] & 0xFF00) | (st.brush & 0xFF)
    st.dirty = True


def _enemy_at(st: GmapState, wx: int, wy: int) -> int:
    best = -1
    best_d = 1e9
    for i, e in enumerate(st.room.enemy):
        cx = e.x_origin + 8
        cy = e.y_origin + 8
        d = (cx - wx) ** 2 + (cy - wy) ** 2
        if d < best_d and d < 20 * 20:
            best_d = d
            best = i
    return best


def _tele_at(st: GmapState, wx: int, wy: int) -> int:
    for i, tp in enumerate(st.room.teleport):
        if tp.x <= wx < tp.x + max(1, tp.w) and tp.y <= wy < tp.y + max(1, tp.h):
            return i
    return -1


def _seq_owner(st: GmapState):
    return ops.seq_list_for(
        st.game_map, st.room, st.seq_src, st.enemy_sel, st.entry_sel
    )


def _selected_seq(st: GmapState):
    owner = _seq_owner(st)
    if not owner.seq:
        return None
    st.seq_sel = max(0, min(st.seq_sel, len(owner.seq) - 1))
    return owner.seq[st.seq_sel]


def _selected_cmd(st: GmapState):
    seq = _selected_seq(st)
    if seq is None or not seq.Command:
        return None
    st.seq_cmd_sel = max(0, min(st.seq_cmd_sel, len(seq.Command) - 1))
    return seq.Command[st.seq_cmd_sel]


def _selected_block(st: GmapState):
    cmd = _selected_cmd(st)
    if cmd is None or not cmd.ent:
        return None
    st.seq_block_sel = max(0, min(st.seq_block_sel, len(cmd.ent) - 1))
    return cmd.ent[st.seq_block_sel]


def _do_redimension(st: GmapState) -> None:
    room = st.room
    nx = prompt_int(f"New room X (was {room.x})", room.x, minimum=1, maximum=512)
    if nx is None:
        return
    ny = prompt_int(f"New room Y (was {room.y})", room.y, minimum=1, maximum=512)
    if ny is None:
        return
    fill = prompt_int("Fill tile (0-255)", st.brush, minimum=0, maximum=255)
    if fill is None:
        return
    ops.redimension_room(room, nx, ny, fill)
    st.dirty = True
    _clamp_cam(st)
    _flash(st, f"Room resized to {nx}x{ny}")


def _edit_block_field(st: GmapState) -> None:
    block = _selected_block(st)
    if block is None:
        _flash(st, "No command block")
        return
    labels = []
    for name in ops.COMMAND_DATA_FIELDS:
        cur = getattr(block, name)
        preview = repr(cur) if isinstance(cur, str) else str(cur)
        if len(preview) > 40:
            preview = preview[:37] + "..."
        labels.append(f"{name} = {preview}")
    picked = pick_list("Edit command block field", labels)
    if picked is None:
        return
    field = ops.COMMAND_DATA_FIELDS[picked]
    cur = getattr(block, field)
    if field in STRING_FIELDS:
        val = prompt_text(field, str(cur), allow_empty=True)
        if val is not None:
            setattr(block, field, val)
            st.dirty = True
    elif field in FLOAT_FIELDS:
        raw = prompt_text(field, str(cur), numeric=True, allow_empty=False)
        if raw is not None:
            try:
                setattr(block, field, float(raw))
                st.dirty = True
            except ValueError:
                _flash(st, f"Bad float for {field}")
    else:
        val = prompt_int(field, int(cur))
        if val is not None:
            setattr(block, field, val)
            st.dirty = True


def _pick_object_xml() -> str | None:
    root = data_root() / "object"
    files = sorted(p.stem for p in root.glob("*.xml"))
    idx = pick_list("Add enemy object", files)
    if idx is None:
        return None
    return f"data/object/{files[idx]}.xml"


def _pick_tileset(st: GmapState) -> None:
    root = data_root() / "pictures" / "tiles"
    files = sorted(p.name for p in root.glob("*.spr"))
    idx = pick_list("Load tileset", files)
    if idx is None:
        return
    rel = f"data/pictures/tiles/{files[idx]}"
    st.game_map.tileset_filename = rel
    st.game_map.tileset = None
    st.tile_surfs = _load_tiles(st.game_map)
    st.dirty = True
    _flash(st, f"Tileset {files[idx]}")


def _pick_parallax(st: GmapState) -> None:
    root = data_root() / "pictures"
    files = sorted(p.name for p in root.glob("*.spr"))
    idx = pick_list("Parallax image (Esc clears)", files)
    room = st.room
    if idx is None:
        room.parallax = 0
        room.para_filename = ""
        room.para_img = None
        st.dirty = True
        _flash(st, "Parallax cleared")
        return
    rel = f"data/pictures/{files[idx]}"
    room.para_filename = rel
    room.parallax = -1
    room.para_img = LLSystem_ImageLoad(rel)
    st.dirty = True
    _flash(st, f"Parallax {files[idx]}")


def _draw_sidebar(canvas: pygame.Surface, st: GmapState, font: pygame.font.Font) -> None:
    panel = pygame.Rect(VIEW_W + 8, 290, GMAP_W - VIEW_W - 16, GMAP_H - 298)
    pygame.draw.rect(canvas, (24, 24, 32), panel)
    pygame.draw.rect(canvas, (80, 80, 100), panel, 1)

    room = st.room
    lines = [
        f"Map: {st.map_path.name}{' *' if st.dirty else ''}",
        f"Room {st.room_i}/{max(0, st.game_map.rooms - 1)}  {room.x}x{room.y}",
        f"Layer {st.layer}  Zoom {st.zoom}x  Brush {st.brush}",
        f"Mode: {st.mode}  Grid:{int(st.show_grid)} Walk:{int(st.show_walk)} Solo:{int(st.solo)}",
    ]

    if st.mode == "enemy":
        lines.append(f"Enemy {st.enemy_sel}/{max(0, room.enemies - 1)}")
        if 0 <= st.enemy_sel < len(room.enemy):
            e = room.enemy[st.enemy_sel]
            name = Path(str(e.id).replace("\\", "/")).stem
            lines.append(f"  {name} @ {e.x_origin},{e.y_origin}")
            lines.append(f"  dir {e.direction} ({DIR_NAMES[e.direction & 3]})")
        lines.append("  Ins add object · Del remove")
    elif st.mode == "entry":
        lines.append(f"Entry {st.entry_sel}/{max(0, st.game_map.entries - 1)}")
        if 0 <= st.entry_sel < len(st.game_map.entry):
            en = st.game_map.entry[st.entry_sel]
            lines.append(f"  room {en.room} @ {en.x},{en.y} dir {en.direction}")
        lines.append("  click place · [/] dir · Ins/Del")
    elif st.mode == "tele":
        lines.append(f"Teleport {st.tele_sel}/{max(0, room.teleports - 1)}  phase {st.tele_phase}")
        if 0 <= st.tele_sel < len(room.teleport):
            tp = room.teleport[st.tele_sel]
            lines.append(f"  box {tp.x},{tp.y} {tp.w}x{tp.h}")
            lines.append(f"  to_room {tp.to_room}  dest {tp.dx},{tp.dy} dd {tp.dd}")
            lines.append(f"  to_map {tp.to_map!r} song {tp.to_song}")
            lines.append("  click set xy · Ctrl+click size")
            lines.append("  Enter phase · Ins/Del add/remove")
    elif st.mode == "seq":
        owner = _seq_owner(st)
        lines.append(f"Seq src {st.seq_src}  #{st.seq_sel}/{max(0, owner.seq_here - 1)}")
        seq = _selected_seq(st)
        if seq is not None:
            lines.append(f"  ents {seq.ents} cmds {seq.commands}")
            if seq.ent_code:
                code = seq.ent_code[min(st.seq_ent_sel, len(seq.ent_code) - 1)]
                lines.append(f"  ent[{st.seq_ent_sel}] code {code}")
            cmd = _selected_cmd(st)
            if cmd is not None:
                lines.append(f"  cmd[{st.seq_cmd_sel}] blocks {cmd.ents}")
                block = _selected_block(st)
                if block is not None:
                    preview = (block.text or "")[:28]
                    lines.append(f"  blk[{st.seq_block_sel}] {preview!r}")
                    lines.append(f"  -> {block.to_map}:{block.to_entry}")
        lines.append("  X src  Ins/Del seq  ;/' cmd")
        lines.append("  B edit any block field")
    elif st.mode == "macro":
        lines.append(f"Macros {len(st.macros)}  sel {st.macro_sel}")
        lines.append("  Ins new · C capture 6x6 · click stamp")
    elif st.mode == "flood":
        lines.append("Flood fill with brush (click map)")
    elif st.mode == "walk":
        lines.append("Walkables: click 8x8 quads to toggle")
        lines.append(f"  active layer {st.layer}")
    elif st.mode == "ice":
        lines.append("Ice: click tiles to toggle (layer 0)")
        lines.append("  Shift+I clear · Ctrl+I fill all")

    lines.append(f"Para:{'Y' if room.parallax else 'N'} {Path(room.para_filename).name if room.para_filename else ''}")
    lines.extend(
        [
            "",
            "P paint O flood K walk I ice",
            "E enemy N entry T tele Q seq M macro",
            "D redim H fill U tileset Y parallax",
            "Shift+R add room  Shift+Del del room",
            "[ ] room/sel  Tab modes  Ctrl+S save",
        ]
    )
    y = panel.y + 4
    for line in lines:
        canvas.blit(font.render(line, True, (220, 220, 230)), (panel.x + 6, y))
        y += 13
        if y > GMAP_H - 22:
            break

    if st.message and pygame.time.get_ticks() / 1000.0 < st.message_until:
        canvas.blit(font.render(st.message, True, (255, 220, 120)), (8, GMAP_H - 18))


def _draw_tileset(canvas: pygame.Surface, st: GmapState) -> None:
    x0, y0, tw, th = TILE_PANEL
    pygame.draw.rect(canvas, (16, 16, 20), (x0, y0, tw, th))
    pygame.draw.rect(canvas, (90, 90, 110), (x0, y0, tw, th), 1)
    if not st.tile_surfs:
        return
    cols = tw // 16
    rows = th // 16
    start = st.tileset_scroll * cols
    for n in range(cols * rows):
        idx = start + n
        if idx <= 0 or idx >= len(st.tile_surfs):
            continue
        surf = st.tile_surfs[idx]
        if surf is None:
            continue
        cx = x0 + (n % cols) * 16
        cy = y0 + (n // cols) * 16
        canvas.blit(surf, (cx, cy))
        if idx == st.brush:
            pygame.draw.rect(canvas, (255, 255, 0), (cx, cy, 16, 16), 1)


def _draw_view(canvas: pygame.Surface, st: GmapState) -> None:
    view = pygame.Surface((VIEW_W // st.zoom, VIEW_H // st.zoom)).convert()
    view.fill((0, 0, 0))
    layers = (st.layer,) if st.solo else (0, 1, 2)
    blit_room_tiles(view, st.room, st.tile_surfs, st.cam_x, st.cam_y, layers=layers)

    if st.show_grid:
        ox, oy = -(st.cam_x % 16), -(st.cam_y % 16)
        for x in range(ox, view.get_width() + 16, 16):
            pygame.draw.line(view, (40, 40, 50), (x, 0), (x, view.get_height()))
        for y in range(oy, view.get_height() + 16, 16):
            pygame.draw.line(view, (40, 40, 50), (0, y), (view.get_width(), y))

    show_walk = st.show_walk or st.mode == "walk"
    walk_layer = st.layer if st.mode == "walk" else 0
    if show_walk and walk_layer < len(st.room.layout):
        layout = st.room.layout[walk_layer]
        for ty in range(st.room.y):
            for tx in range(st.room.x):
                idx = ty * st.room.x + tx
                if idx >= len(layout):
                    continue
                bits = layout[idx]
                sx = tx * 16 - st.cam_x
                sy = ty * 16 - st.cam_y
                if not (-16 <= sx < view.get_width() and -16 <= sy < view.get_height()):
                    continue
                # Quad overlays (UL/UR/LL/LR) matching FB walkable bits.
                quads = (
                    (ops.UPPER_LEFT, 0, 0),
                    (ops.UPPER_RIGHT, 8, 0),
                    (ops.LOWER_LEFT, 0, 8),
                    (ops.LOWER_RIGHT, 8, 8),
                )
                for mask, ox, oy in quads:
                    if bits & mask:
                        s = pygame.Surface((8, 8), pygame.SRCALPHA)
                        s.fill((255, 60, 60, 110))
                        view.blit(s, (sx + ox, sy + oy))

    if (st.show_walk or st.mode == "ice") and st.room.layout:
        layout = st.room.layout[0]
        for ty in range(st.room.y):
            for tx in range(st.room.x):
                idx = ty * st.room.x + tx
                if idx >= len(layout):
                    continue
                if layout[idx] & ops.TILE_ICE:
                    sx = tx * 16 - st.cam_x
                    sy = ty * 16 - st.cam_y
                    if -16 <= sx < view.get_width() and -16 <= sy < view.get_height():
                        s = pygame.Surface((16, 16), pygame.SRCALPHA)
                        s.fill((120, 200, 255, 80))
                        view.blit(s, (sx, sy))

    for i, e in enumerate(st.room.enemy):
        sx = e.x_origin - st.cam_x
        sy = e.y_origin - st.cam_y
        color = (255, 220, 80) if i == st.enemy_sel and st.mode == "enemy" else (80, 200, 255)
        pygame.draw.rect(view, color, (sx, sy, 16, 16), 1)
        d = e.direction & 3
        cx, cy = sx + 8, sy + 8
        tip = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)][d]
        pygame.draw.line(view, color, (cx, cy), tip, 2)

    for i, tp in enumerate(st.room.teleport):
        sx = tp.x - st.cam_x
        sy = tp.y - st.cam_y
        color = (255, 120, 255) if i == st.tele_sel and st.mode == "tele" else (180, 80, 200)
        pygame.draw.rect(view, color, (sx, sy, max(1, tp.w), max(1, tp.h)), 1)
        if st.mode == "tele" and st.tele_phase == 2 and i == st.tele_sel:
            # Dest marker drawn in dest room view when phase 2 jumped rooms.
            pass

    if st.mode == "tele" and st.tele_phase == 2:
        # When viewing dest room, show dx/dy of the teleport owned by prev room.
        prev = st.game_map.room[st.tele_prev_room]
        if 0 <= st.tele_sel < len(prev.teleport):
            tp = prev.teleport[st.tele_sel]
            pygame.draw.circle(
                view,
                (255, 255, 80),
                (tp.dx - st.cam_x, tp.dy - st.cam_y),
                4,
                1,
            )

    for i, entry in enumerate(st.game_map.entry):
        if entry.room != st.room_i:
            continue
        sx = entry.x - st.cam_x
        sy = entry.y - st.cam_y
        color = (120, 255, 120) if i == st.entry_sel else (60, 160, 60)
        pygame.draw.rect(view, color, (sx, sy, 12, 12), 1)

    scaled = pygame.transform.scale(view, (VIEW_W, VIEW_H))
    canvas.blit(scaled, (0, 0))
    pygame.draw.rect(canvas, (120, 120, 140), (0, 0, VIEW_W, VIEW_H), 1)


def _hit_tileset(mx: int, my: int, st: GmapState) -> int | None:
    x0, y0, tw, th = TILE_PANEL
    if not (x0 <= mx < x0 + tw and y0 <= my < y0 + th):
        return None
    cols = tw // 16
    tx = (mx - x0) // 16
    ty = (my - y0) // 16
    idx = st.tileset_scroll * cols + ty * cols + tx
    if idx <= 0 or idx >= len(st.tile_surfs):
        return None
    return idx


def _list_maps() -> list[Path]:
    return sorted((data_root() / "map").glob("*.map"))


def _prompt_load(st: GmapState) -> GmapState | None:
    maps = _list_maps()
    if not maps:
        _flash(st, "No maps in data/map")
        return None
    try:
        sel = maps.index(st.map_path.resolve())
    except ValueError:
        sel = 0
    font = pygame.font.SysFont("consolas", 14)
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_UP, pygame.K_LEFT):
                    sel = (sel - 1) % len(maps)
                if event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                    sel = (sel + 1) % len(maps)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return _open_map(str(maps[sel]))
                if event.key == pygame.K_PAGEUP:
                    sel = max(0, sel - 12)
                if event.key == pygame.K_PAGEDOWN:
                    sel = min(len(maps) - 1, sel + 12)
        win = pygame.display.get_surface()
        if win is None:
            return None
        overlay = pygame.Surface((GMAP_W, GMAP_H))
        overlay.fill((10, 10, 16))
        overlay.blit(font.render("Load map (Enter)  Esc cancel", True, (240, 240, 240)), (20, 12))
        top = max(0, sel - 10)
        for i, path in enumerate(maps[top : top + 24]):
            y = 40 + i * 18
            color = (255, 230, 120) if top + i == sel else (200, 200, 210)
            mark = ">" if top + i == sel else " "
            overlay.blit(font.render(f"{mark} {path.name}", True, color), (24, y))
        win.blit(pygame.transform.smoothscale(overlay, win.get_size()), (0, 0))
        pygame.display.flip()
        clock.tick(30)


def _handle_keydown(st: GmapState, event: pygame.event.Event) -> GmapState | str | None:
    """Return updated state, 'quit', or None."""
    mods = pygame.key.get_mods()
    key = event.key

    if key == pygame.K_ESCAPE:
        if st.mode == "tele" and st.tele_phase != 0:
            # Cancel dest placement — restore room.
            st.room_i = st.tele_prev_room
            st.tele_phase = 0
            _clamp_cam(st)
            _flash(st, "Teleport dest cancelled")
            return None
        return "quit"

    if key == pygame.K_s and (mods & pygame.KMOD_CTRL):
        _save(st)
        return None

    if key == pygame.K_l:
        if st.dirty:
            _flash(st, "Unsaved changes — Ctrl+S first")
        else:
            loaded = _prompt_load(st)
            if loaded is not None:
                return loaded
        return None

    if key == pygame.K_TAB:
        st.mode = MODES[(MODES.index(st.mode) + 1) % len(MODES)]
        return None
    if key == pygame.K_p:
        st.mode = "paint"
        return None
    if key == pygame.K_o:
        st.mode = "flood"
        return None
    if key == pygame.K_k:
        st.mode = "walk"
        return None
    if key == pygame.K_i and not (mods & (pygame.KMOD_SHIFT | pygame.KMOD_CTRL)):
        st.mode = "ice"
        return None
    if key == pygame.K_e:
        st.mode = "enemy"
        return None
    if key == pygame.K_n:
        st.mode = "entry"
        return None
    if key == pygame.K_t:
        st.mode = "tele"
        st.tele_phase = 0
        return None
    if key == pygame.K_q:
        st.mode = "seq"
        return None
    if key == pygame.K_m:
        st.mode = "macro"
        return None
    if key == pygame.K_d:
        _do_redimension(st)
        return None
    if key == pygame.K_h:
        ops.layer_fill(st.room, st.layer, st.brush)
        st.dirty = True
        _flash(st, f"Layer {st.layer} filled with {st.brush}")
        return None
    if key == pygame.K_u:
        _pick_tileset(st)
        return None
    if key == pygame.K_y:
        _pick_parallax(st)
        return None
    if key == pygame.K_i and (mods & pygame.KMOD_SHIFT):
        ops.clear_layer_ice(st.room, fill=False)
        st.dirty = True
        _flash(st, "Ice cleared")
        return None
    if key == pygame.K_i and (mods & pygame.KMOD_CTRL):
        ops.clear_layer_ice(st.room, fill=True)
        st.dirty = True
        _flash(st, "Ice filled")
        return None
    if key == pygame.K_r and (mods & pygame.KMOD_SHIFT):
        ops.add_room(st.game_map)
        st.room_i = st.game_map.rooms - 1
        st.dirty = True
        _clamp_cam(st)
        _flash(st, f"Room {st.room_i} added")
        return None
    if key == pygame.K_DELETE and (mods & pygame.KMOD_SHIFT):
        if st.game_map.rooms <= 1:
            _flash(st, "Cannot delete last room")
        else:
            ops.delete_room(st.game_map, st.room_i)
            st.room_i = min(st.room_i, st.game_map.rooms - 1)
            st.dirty = True
            _clamp_cam(st)
            _flash(st, "Room deleted")
        return None

    if key == pygame.K_LEFTBRACKET:
        if st.mode == "enemy" and st.room.enemy:
            st.room.enemy[st.enemy_sel].direction = (
                st.room.enemy[st.enemy_sel].direction - 1
            ) & 3
            st.dirty = True
        elif st.mode == "entry" and st.game_map.entry:
            en = st.game_map.entry[st.entry_sel]
            en.direction = (en.direction - 1) & 7
            st.dirty = True
        elif st.mode == "tele" and st.room.teleport:
            st.tele_sel = (st.tele_sel - 1) % st.room.teleports
        elif st.mode == "seq":
            owner = _seq_owner(st)
            if owner.seq:
                st.seq_sel = (st.seq_sel - 1) % len(owner.seq)
                st.seq_cmd_sel = st.seq_block_sel = st.seq_ent_sel = 0
        elif st.mode == "macro" and st.macros:
            st.macro_sel = (st.macro_sel - 1) % len(st.macros)
        else:
            st.room_i = (st.room_i - 1) % max(1, st.game_map.rooms)
            st.enemy_sel = st.tele_sel = 0
            _clamp_cam(st)
        return None

    if key == pygame.K_RIGHTBRACKET:
        if st.mode == "enemy" and st.room.enemy:
            st.room.enemy[st.enemy_sel].direction = (
                st.room.enemy[st.enemy_sel].direction + 1
            ) & 3
            st.dirty = True
        elif st.mode == "entry" and st.game_map.entry:
            en = st.game_map.entry[st.entry_sel]
            en.direction = (en.direction + 1) & 7
            st.dirty = True
        elif st.mode == "tele" and st.room.teleport:
            st.tele_sel = (st.tele_sel + 1) % st.room.teleports
        elif st.mode == "seq":
            owner = _seq_owner(st)
            if owner.seq:
                st.seq_sel = (st.seq_sel + 1) % len(owner.seq)
                st.seq_cmd_sel = st.seq_block_sel = st.seq_ent_sel = 0
        elif st.mode == "macro" and st.macros:
            st.macro_sel = (st.macro_sel + 1) % len(st.macros)
        else:
            st.room_i = (st.room_i + 1) % max(1, st.game_map.rooms)
            st.enemy_sel = st.tele_sel = 0
            _clamp_cam(st)
        return None

    if key in (pygame.K_1, pygame.K_KP1):
        st.layer = 0
        return None
    if key in (pygame.K_2, pygame.K_KP2):
        st.layer = 1
        return None
    if key in (pygame.K_3, pygame.K_KP3):
        st.layer = 2
        return None
    if key == pygame.K_z:
        st.zoom = 2 if st.zoom == 1 else 1
        _clamp_cam(st)
        return None
    if key == pygame.K_g:
        st.show_grid = not st.show_grid
        return None
    if key == pygame.K_w:
        st.show_walk = not st.show_walk
        return None
    if key == pygame.K_s and not (mods & pygame.KMOD_CTRL):
        st.solo = not st.solo
        return None
    if key == pygame.K_COMMA:
        st.brush = max(1, st.brush - 1)
        return None
    if key == pygame.K_PERIOD:
        st.brush = min(max(1, len(st.tile_surfs) - 1), st.brush + 1)
        return None
    if key == pygame.K_PAGEUP:
        st.tileset_scroll = max(0, st.tileset_scroll - 1)
        return None
    if key == pygame.K_PAGEDOWN:
        st.tileset_scroll += 1
        return None

    # Mode-specific.
    if st.mode == "enemy":
        if key == pygame.K_INSERT:
            oid = _pick_object_xml()
            if oid is not None:
                ops.add_enemy(st.room, oid, st.cam_x + 16, st.cam_y + 16)
                st.enemy_sel = st.room.enemies - 1
                st.dirty = True
                _flash(st, f"Added {Path(oid).stem}")
        elif key == pygame.K_DELETE and st.room.enemy:
            ops.delete_enemy(st.room, st.enemy_sel)
            st.enemy_sel = max(0, min(st.enemy_sel, st.room.enemies - 1))
            st.dirty = True
        elif st.room.enemy:
            e = st.room.enemy[st.enemy_sel]
            step = 16 if mods & pygame.KMOD_SHIFT else 1
            if key == pygame.K_UP:
                e.y_origin -= step
                st.dirty = True
            elif key == pygame.K_DOWN:
                e.y_origin += step
                st.dirty = True
            elif key == pygame.K_LEFT:
                e.x_origin -= step
                st.dirty = True
            elif key == pygame.K_RIGHT:
                e.x_origin += step
                st.dirty = True
            elif key == pygame.K_EQUALS or key == pygame.K_PLUS:
                st.enemy_sel = (st.enemy_sel + 1) % st.room.enemies
            elif key == pygame.K_MINUS:
                st.enemy_sel = (st.enemy_sel - 1) % st.room.enemies

    elif st.mode == "entry":
        if key == pygame.K_INSERT:
            ops.add_entry(st.game_map, st.room_i)
            st.entry_sel = st.game_map.entries - 1
            st.dirty = True
            _flash(st, "Entry added")
        elif key == pygame.K_DELETE and st.game_map.entry:
            ops.delete_entry(st.game_map, st.entry_sel)
            st.entry_sel = max(0, min(st.entry_sel, st.game_map.entries - 1))
            st.dirty = True
        elif key in (pygame.K_EQUALS, pygame.K_PLUS) and st.game_map.entries:
            st.entry_sel = (st.entry_sel + 1) % st.game_map.entries
            en = st.game_map.entry[st.entry_sel]
            if en.room != st.room_i:
                st.room_i = en.room
                _clamp_cam(st)
        elif key == pygame.K_MINUS and st.game_map.entries:
            st.entry_sel = (st.entry_sel - 1) % st.game_map.entries
            en = st.game_map.entry[st.entry_sel]
            if en.room != st.room_i:
                st.room_i = en.room
                _clamp_cam(st)
        elif st.game_map.entry and key in (
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_LEFT,
            pygame.K_RIGHT,
        ):
            en = st.game_map.entry[st.entry_sel]
            step = 16 if mods & pygame.KMOD_SHIFT else 8
            if key == pygame.K_UP:
                en.y -= step
            elif key == pygame.K_DOWN:
                en.y += step
            elif key == pygame.K_LEFT:
                en.x -= step
            elif key == pygame.K_RIGHT:
                en.x += step
            st.dirty = True

    elif st.mode == "tele":
        if key == pygame.K_INSERT:
            ops.add_teleport(st.room)
            st.tele_sel = st.room.teleports - 1
            st.dirty = True
            _flash(st, "Teleport added")
        elif key == pygame.K_DELETE and st.room.teleport:
            ops.delete_teleport(st.room, st.tele_sel)
            st.tele_sel = max(0, min(st.tele_sel, st.room.teleports - 1))
            st.dirty = True
        elif key == pygame.K_RETURN and st.room.teleport:
            if st.tele_phase == 0:
                to_room = prompt_int(
                    "to_room (or -1 if to_map set)",
                    st.room.teleport[st.tele_sel].to_room,
                    minimum=-1,
                    maximum=st.game_map.rooms - 1,
                )
                if to_room is None:
                    return None
                tp = st.room.teleport[st.tele_sel]
                if to_room >= 0:
                    tp.to_room = to_room
                to_map = prompt_text("to_map (blank = same map)", tp.to_map, allow_empty=True)
                if to_map is not None:
                    tp.to_map = to_map
                st.dirty = True
                if tp.to_map:
                    st.tele_phase = 0
                    _flash(st, "Cross-map tele — set dx/dy with N")
                else:
                    st.tele_prev_room = st.room_i
                    st.room_i = tp.to_room
                    st.tele_phase = 2
                    _clamp_cam(st)
                    _flash(st, "Click dest dx/dy · Enter finish")
            elif st.tele_phase == 2:
                st.room_i = st.tele_prev_room
                st.tele_phase = 0
                _clamp_cam(st)
                _flash(st, "Teleport dest set")
        elif key == pygame.K_n and st.room.teleport:
            tp = st.room.teleport[st.tele_sel]
            dx = prompt_int("dx", tp.dx)
            dy = prompt_int("dy", tp.dy) if dx is not None else None
            dd = prompt_int("dd (dir)", tp.dd) if dy is not None else None
            if None not in (dx, dy, dd):
                tp.dx, tp.dy, tp.dd = dx, dy, dd
                st.dirty = True
        elif key == pygame.K_y and st.room.teleport:
            tp = st.room.teleport[st.tele_sel]
            song = prompt_int("to_song", tp.to_song)
            if song is not None:
                tp.to_song = song
                st.dirty = True
        elif st.room.teleport and key in (
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_LEFT,
            pygame.K_RIGHT,
        ):
            tp = st.room.teleport[st.tele_sel]
            step = 16 if mods & pygame.KMOD_SHIFT else 1
            if key == pygame.K_UP:
                tp.y -= step
            elif key == pygame.K_DOWN:
                tp.y += step
            elif key == pygame.K_LEFT:
                tp.x -= step
            elif key == pygame.K_RIGHT:
                tp.x += step
            st.dirty = True

    elif st.mode == "seq":
        if key == pygame.K_x:
            st.seq_src = SEQ_SOURCES[(SEQ_SOURCES.index(st.seq_src) + 1) % len(SEQ_SOURCES)]
            st.seq_sel = st.seq_cmd_sel = st.seq_block_sel = st.seq_ent_sel = 0
            _flash(st, f"Sequence source: {st.seq_src}")
        elif key == pygame.K_INSERT:
            owner = _seq_owner(st)
            ops.add_sequence(owner)
            st.seq_sel = owner.seq_here - 1
            st.dirty = True
        elif key == pygame.K_DELETE:
            owner = _seq_owner(st)
            ops.delete_sequence(owner, st.seq_sel)
            st.seq_sel = max(0, min(st.seq_sel, owner.seq_here - 1))
            st.dirty = True
        elif key == pygame.K_SEMICOLON:
            seq = _selected_seq(st)
            if seq is not None:
                ops.add_command(seq)
                st.seq_cmd_sel = seq.commands - 1
                st.dirty = True
        elif key == pygame.K_QUOTE:
            seq = _selected_seq(st)
            if seq is not None:
                ops.delete_command(seq, st.seq_cmd_sel)
                st.seq_cmd_sel = max(0, min(st.seq_cmd_sel, seq.commands - 1))
                st.dirty = True
        elif key == pygame.K_LEFT:
            seq = _selected_seq(st)
            if seq is not None and seq.Command:
                st.seq_cmd_sel = (st.seq_cmd_sel - 1) % seq.commands
                st.seq_block_sel = 0
        elif key == pygame.K_RIGHT:
            seq = _selected_seq(st)
            if seq is not None and seq.Command:
                st.seq_cmd_sel = (st.seq_cmd_sel + 1) % seq.commands
                st.seq_block_sel = 0
        elif key == pygame.K_UP:
            cmd = _selected_cmd(st)
            if cmd is not None and cmd.ent:
                st.seq_block_sel = (st.seq_block_sel - 1) % cmd.ents
        elif key == pygame.K_DOWN:
            cmd = _selected_cmd(st)
            if cmd is not None and cmd.ent:
                st.seq_block_sel = (st.seq_block_sel + 1) % cmd.ents
        elif key == pygame.K_b:
            _edit_block_field(st)
        elif key == pygame.K_EQUALS or key == pygame.K_PLUS:
            cmd = _selected_cmd(st)
            if cmd is not None:
                ops.add_command_block(cmd)
                st.seq_block_sel = cmd.ents - 1
                st.dirty = True
        elif key == pygame.K_MINUS:
            cmd = _selected_cmd(st)
            if cmd is not None:
                ops.delete_command_block(cmd, st.seq_block_sel)
                st.seq_block_sel = max(0, min(st.seq_block_sel, cmd.ents - 1))
                st.dirty = True
        elif key == pygame.K_c:
            # Edit entity code for selected ent slot.
            seq = _selected_seq(st)
            if seq is not None:
                if not seq.ent_code:
                    seq.ent_code = [0]
                    seq.ents = 1
                st.seq_ent_sel = max(0, min(st.seq_ent_sel, len(seq.ent_code) - 1))
                val = prompt_int(f"ent_code[{st.seq_ent_sel}]", seq.ent_code[st.seq_ent_sel])
                if val is not None:
                    seq.ent_code[st.seq_ent_sel] = val
                    st.dirty = True
        elif key == pygame.K_v:
            # Cycle entry selection when source is entry.
            if st.game_map.entries:
                st.entry_sel = (st.entry_sel + 1) % st.game_map.entries
                _flash(st, f"Entry {st.entry_sel}")

    elif st.mode == "macro":
        if key == pygame.K_INSERT:
            st.macros.append([st.brush & 0xFF] * 36)
            st.macro_sel = len(st.macros) - 1
            _flash(st, "Macro slot added (filled with brush)")
        elif key == pygame.K_DELETE and st.macros:
            del st.macros[st.macro_sel]
            st.macro_sel = max(0, min(st.macro_sel, len(st.macros) - 1))
        elif key == pygame.K_c:
            _flash(st, "Click map to capture 6x6 into selected macro")

    return None


def _handle_map_click(st: GmapState, wx: int, wy: int, button: int, mods: int) -> None:
    if button == 3:
        hit_e = _enemy_at(st, wx, wy)
        if hit_e >= 0:
            st.mode = "enemy"
            st.enemy_sel = hit_e
        return

    if button != 1:
        return

    if st.mode == "paint":
        _paint_at(st, wx, wy)
    elif st.mode == "flood":
        n = ops.flood_fill(st.room, st.layer, wx // 16, wy // 16, st.brush)
        if n:
            st.dirty = True
            _flash(st, f"Flood filled {n} tiles")
    elif st.mode == "walk":
        ops.toggle_quad(st.room, st.layer, wx // 8, wy // 8)
        st.dirty = True
    elif st.mode == "ice":
        ops.toggle_ice(st.room, wx // 16, wy // 16)
        st.dirty = True
    elif st.mode == "enemy":
        hit_e = _enemy_at(st, wx, wy)
        if hit_e >= 0:
            st.enemy_sel = hit_e
    elif st.mode == "entry":
        if not st.game_map.entry:
            ops.add_entry(st.game_map, st.room_i)
            st.entry_sel = 0
        en = st.game_map.entry[st.entry_sel]
        en.x = (wx // 8) * 8
        en.y = (wy // 8) * 8
        en.room = st.room_i
        st.dirty = True
    elif st.mode == "tele":
        if st.tele_phase == 2:
            prev = st.game_map.room[st.tele_prev_room]
            if 0 <= st.tele_sel < len(prev.teleport):
                tp = prev.teleport[st.tele_sel]
                tp.dx = (wx // 8) * 8
                tp.dy = (wy // 8) * 8
                st.dirty = True
            return
        if not st.room.teleport:
            ops.add_teleport(st.room)
            st.tele_sel = 0
            st.dirty = True
        hit = _tele_at(st, wx, wy)
        if hit >= 0 and not (mods & pygame.KMOD_CTRL):
            st.tele_sel = hit
        tp = st.room.teleport[st.tele_sel]
        if mods & pygame.KMOD_CTRL:
            tp.w = max(1, wx - tp.x)
            tp.h = max(1, wy - tp.y)
        else:
            tp.x, tp.y = wx, wy
        st.dirty = True
    elif st.mode == "macro":
        keys = pygame.key.get_pressed()
        tx, ty = wx // 16, wy // 16
        if keys[pygame.K_c] or keys[pygame.K_LCTRL]:
            # Capture requires a slot.
            if not st.macros:
                st.macros.append([0] * 36)
                st.macro_sel = 0
            st.macros[st.macro_sel] = ops.capture_macro(st.room, st.layer, tx, ty)
            _flash(st, f"Captured macro {st.macro_sel}")
        elif st.macros:
            ops.stamp_macro(st.room, st.layer, tx, ty, st.macros[st.macro_sel])
            st.dirty = True
            _flash(st, f"Stamped macro {st.macro_sel}")
        else:
            _flash(st, "Ins to add a macro first")
    elif st.mode == "seq":
        # Click entry or enemy to retarget source quickly.
        hit_e = _enemy_at(st, wx, wy)
        if hit_e >= 0:
            st.seq_src = "enemy"
            st.enemy_sel = hit_e
            st.seq_sel = 0
            _flash(st, f"Seq source enemy {hit_e}")
            return
        for i, entry in enumerate(st.game_map.entry):
            if entry.room == st.room_i and abs(entry.x - wx) < 12 and abs(entry.y - wy) < 12:
                st.seq_src = "entry"
                st.entry_sel = i
                st.seq_sel = 0
                _flash(st, f"Seq source entry {i}")
                return


def run_gmap(map_spec: str | None = None) -> int:
    chdir_project_root()
    pygame.init()
    pygame.display.set_caption("gMap Editor")
    pygame.display.set_mode((GMAP_W, GMAP_H), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 13)

    st = _open_map(map_spec)
    pygame.display.set_caption(f"gMap Editor - {st.map_path.name}")
    running = True
    painting = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                result = _handle_keydown(st, event)
                if result == "quit":
                    running = False
                elif isinstance(result, GmapState):
                    st = result
                    pygame.display.set_caption(f"gMap Editor - {st.map_path.name}")
            elif event.type == pygame.MOUSEWHEEL:
                st.tileset_scroll = max(0, st.tileset_scroll - event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = _scale_mouse(event.pos)
                hit = _hit_tileset(mx, my, st)
                if hit is not None and event.button == 1:
                    st.brush = hit
                    if st.mode not in ("flood", "macro"):
                        st.mode = "paint"
                elif mx < VIEW_W and my < VIEW_H:
                    world = _view_to_world(st, mx, my)
                    if world is not None:
                        if st.mode == "paint" and event.button == 1:
                            painting = True
                        _handle_map_click(
                            st, world[0], world[1], event.button, pygame.key.get_mods()
                        )
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    painting = False
            elif event.type == pygame.MOUSEMOTION:
                if painting and st.mode == "paint":
                    mx, my = _scale_mouse(event.pos)
                    world = _view_to_world(st, mx, my)
                    if world is not None:
                        _paint_at(st, *world)

        keys = pygame.key.get_pressed()
        pan = 8 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 4
        if st.mode not in ("enemy", "tele", "seq", "entry"):
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                st.cam_x -= pan
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                st.cam_x += pan
            if keys[pygame.K_UP] or keys[pygame.K_r]:
                st.cam_y -= pan
            if keys[pygame.K_DOWN] or keys[pygame.K_f]:
                st.cam_y += pan
        _clamp_cam(st)

        canvas = pygame.Surface((GMAP_W, GMAP_H)).convert()
        canvas.fill((12, 12, 18))
        _draw_view(canvas, st)
        _draw_tileset(canvas, st)
        _draw_sidebar(canvas, st, font)

        win = pygame.display.get_surface()
        assert win is not None
        win.fill((0, 0, 0))
        win.blit(pygame.transform.smoothscale(canvas, win.get_size()), (0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0
