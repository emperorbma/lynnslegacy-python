"""gmap editor — Screen 19–sized workspace (800×600) like FB gmap.bas.

Core loop covers rooms, layers, tile paint, enemy select/move/facing, load/save.
Sequence / teleport / macro editing stays with the FB sources for now.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

from lynn.gfx.blit import blit_room_tiles
from lynn.gfx.image import LLSystem_ImageLoad, frame_surfaces
from lynn.gfx.palette import load_pal
from lynn.map.loader import load_mapV
from lynn.map.saver import save_mapV
from lynn.map.types import MapEnemyStub, MapType, RoomType
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


@dataclass
class GmapState:
    game_map: MapType
    map_path: Path
    tile_surfs: list
    room_i: int = 0
    layer: int = 0
    cam_x: int = 0
    cam_y: int = 0
    zoom: int = 1  # 1 or 2 (FB zooming flag style)
    brush: int = 1
    enemy_sel: int = 0
    dirty: bool = False
    status: str = ""
    show_grid: bool = True
    show_walk: bool = False
    solo: bool = False
    mode: str = "paint"  # paint | enemy
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


def _paint_at(st: GmapState, wx: int, wy: int) -> None:
    room = st.room
    tx, ty = wx // 16, wy // 16
    if tx < 0 or ty < 0 or tx >= room.x or ty >= room.y:
        return
    idx = ty * room.x + tx
    layout = room.layout[st.layer]
    if idx >= len(layout):
        return
    # Keep walk/ice high bits; replace tile index (low byte).
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


def _draw_sidebar(canvas: pygame.Surface, st: GmapState, font: pygame.font.Font) -> None:
    panel = pygame.Rect(VIEW_W + 8, 290, GMAP_W - VIEW_W - 16, GMAP_H - 298)
    pygame.draw.rect(canvas, (24, 24, 32), panel)
    pygame.draw.rect(canvas, (80, 80, 100), panel, 1)

    room = st.room
    lines = [
        f"Map: {st.map_path.name}{' *' if st.dirty else ''}",
        f"Room {st.room_i}/{max(0, st.game_map.rooms - 1)}  {room.x}x{room.y}",
        f"Layer {st.layer}  Zoom {st.zoom}x  Brush {st.brush}",
        f"Mode: {st.mode}   Grid:{'Y' if st.show_grid else 'N'} Walk:{'Y' if st.show_walk else 'N'}",
        f"Enemies: {room.enemies}  sel={st.enemy_sel}",
    ]
    if 0 <= st.enemy_sel < len(room.enemy):
        e = room.enemy[st.enemy_sel]
        name = Path(str(e.id).replace("\\", "/")).stem
        lines.append(f"  {name} @ {e.x_origin},{e.y_origin}")
        lines.append(f"  dir {e.direction} ({DIR_NAMES[e.direction & 3]})")

    lines.extend(
        [
            "",
            "Keys:",
            "[ ] room   1-3 layer   Z zoom",
            "G grid  W walk  S solo",
            "Tab mode  ,/. brush  T tile panel",
            "E enemy  [/] face  Arrows nudge",
            "Click paint / select enemy",
            "Ctrl+S save  L load list  Esc quit",
        ]
    )
    y = panel.y + 6
    for line in lines:
        canvas.blit(font.render(line, True, (220, 220, 230)), (panel.x + 6, y))
        y += 14

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
        room = st.room
        ox, oy = -(st.cam_x % 16), -(st.cam_y % 16)
        for x in range(ox, view.get_width() + 16, 16):
            pygame.draw.line(view, (40, 40, 50), (x, 0), (x, view.get_height()))
        for y in range(oy, view.get_height() + 16, 16):
            pygame.draw.line(view, (40, 40, 50), (0, y), (view.get_width(), y))
        _ = room
    if st.show_walk and st.room.layout:
        layout = st.room.layout[0]
        for ty in range(st.room.y):
            for tx in range(st.room.x):
                idx = ty * st.room.x + tx
                if idx >= len(layout):
                    continue
                bits = layout[idx]
                # High nibble walk quads (bits 12-15) — show any blocked.
                if bits & 0xF000:
                    sx = tx * 16 - st.cam_x
                    sy = ty * 16 - st.cam_y
                    if -16 <= sx < view.get_width() and -16 <= sy < view.get_height():
                        s = pygame.Surface((16, 16), pygame.SRCALPHA)
                        s.fill((255, 60, 60, 70))
                        view.blit(s, (sx, sy))

    for i, e in enumerate(st.room.enemy):
        sx = e.x_origin - st.cam_x
        sy = e.y_origin - st.cam_y
        color = (255, 220, 80) if i == st.enemy_sel else (80, 200, 255)
        pygame.draw.rect(view, color, (sx, sy, 16, 16), 1)
        # Facing tick.
        d = e.direction & 3
        cx, cy = sx + 8, sy + 8
        tip = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)][d]
        pygame.draw.line(view, color, (cx, cy), tip, 2)

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
    """Simple keyboard map picker drawn inside the window; returns new state or None."""
    maps = _list_maps()
    if not maps:
        _flash(st, "No maps in data/map")
        return None
    # Prefer current map index.
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
                if event.key in (pygame.K_ESCAPE,):
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
        canvas = pygame.display.get_surface()
        if canvas is None:
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
        canvas.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(30)


def run_gmap(map_spec: str | None = None) -> int:
    chdir_project_root()
    pygame.init()
    pygame.display.set_caption("gMap Editor")
    screen = pygame.display.set_mode((GMAP_W, GMAP_H), pygame.RESIZABLE)
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
                mods = pygame.key.get_mods()
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                    _save(st)
                elif event.key == pygame.K_l:
                    if st.dirty:
                        _flash(st, "Unsaved changes — Ctrl+S first")
                    else:
                        loaded = _prompt_load(st)
                        if loaded is not None:
                            st = loaded
                            pygame.display.set_caption(f"gMap Editor - {st.map_path.name}")
                elif event.key == pygame.K_LEFTBRACKET:
                    if st.mode == "enemy" and st.room.enemy:
                        e = st.room.enemy[st.enemy_sel]
                        e.direction = (e.direction - 1) & 3
                        st.dirty = True
                    else:
                        st.room_i = (st.room_i - 1) % max(1, st.game_map.rooms)
                        st.enemy_sel = 0
                        _clamp_cam(st)
                elif event.key == pygame.K_RIGHTBRACKET:
                    if st.mode == "enemy" and st.room.enemy:
                        e = st.room.enemy[st.enemy_sel]
                        e.direction = (e.direction + 1) & 3
                        st.dirty = True
                    else:
                        st.room_i = (st.room_i + 1) % max(1, st.game_map.rooms)
                        st.enemy_sel = 0
                        _clamp_cam(st)
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    st.layer = 0
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    st.layer = 1
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    st.layer = 2
                elif event.key == pygame.K_z:
                    st.zoom = 2 if st.zoom == 1 else 1
                    _clamp_cam(st)
                elif event.key == pygame.K_g:
                    st.show_grid = not st.show_grid
                elif event.key == pygame.K_w:
                    st.show_walk = not st.show_walk
                elif event.key == pygame.K_s and not (mods & pygame.KMOD_CTRL):
                    st.solo = not st.solo
                elif event.key == pygame.K_TAB:
                    st.mode = "enemy" if st.mode == "paint" else "paint"
                elif event.key == pygame.K_e:
                    st.mode = "enemy"
                elif event.key == pygame.K_COMMA:
                    st.brush = max(1, st.brush - 1)
                elif event.key == pygame.K_PERIOD:
                    st.brush = min(max(1, len(st.tile_surfs) - 1), st.brush + 1)
                elif event.key == pygame.K_PAGEUP:
                    st.tileset_scroll = max(0, st.tileset_scroll - 1)
                elif event.key == pygame.K_PAGEDOWN:
                    st.tileset_scroll += 1
                elif st.mode == "enemy" and st.room.enemy:
                    e = st.room.enemy[st.enemy_sel]
                    step = 16 if mods & pygame.KMOD_SHIFT else 1
                    if event.key == pygame.K_UP:
                        e.y_origin -= step
                        st.dirty = True
                    elif event.key == pygame.K_DOWN:
                        e.y_origin += step
                        st.dirty = True
                    elif event.key == pygame.K_LEFT:
                        e.x_origin -= step
                        st.dirty = True
                    elif event.key == pygame.K_RIGHT:
                        e.x_origin += step
                        st.dirty = True
            elif event.type == pygame.MOUSEWHEEL:
                st.tileset_scroll = max(0, st.tileset_scroll - event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Scale mouse if window resized.
                win = pygame.display.get_surface()
                if win is not None and win.get_size() != (GMAP_W, GMAP_H):
                    sx = GMAP_W / win.get_width()
                    sy = GMAP_H / win.get_height()
                    mx, my = int(mx * sx), int(my * sy)
                hit = _hit_tileset(mx, my, st)
                if hit is not None and event.button == 1:
                    st.brush = hit
                    st.mode = "paint"
                elif mx < VIEW_W and my < VIEW_H:
                    world = _view_to_world(st, mx, my)
                    if world is None:
                        continue
                    wx, wy = world
                    if event.button == 1:
                        if st.mode == "enemy":
                            hit_e = _enemy_at(st, wx, wy)
                            if hit_e >= 0:
                                st.enemy_sel = hit_e
                        else:
                            painting = True
                            _paint_at(st, wx, wy)
                    elif event.button == 3:
                        hit_e = _enemy_at(st, wx, wy)
                        if hit_e >= 0:
                            st.mode = "enemy"
                            st.enemy_sel = hit_e
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    painting = False
            elif event.type == pygame.MOUSEMOTION:
                if painting and st.mode == "paint":
                    mx, my = event.pos
                    win = pygame.display.get_surface()
                    if win is not None and win.get_size() != (GMAP_W, GMAP_H):
                        sx = GMAP_W / win.get_width()
                        sy = GMAP_H / win.get_height()
                        mx, my = int(mx * sx), int(my * sy)
                    world = _view_to_world(st, mx, my)
                    if world is not None:
                        _paint_at(st, *world)

        keys = pygame.key.get_pressed()
        pan = 8 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 4
        if st.mode != "enemy":
            # Arrows + A/D/R/F pan (W is walk-grid toggle on keydown).
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

        # Present letterboxed into the real window.
        win = pygame.display.get_surface()
        assert win is not None
        win.fill((0, 0, 0))
        scaled = pygame.transform.smoothscale(canvas, win.get_size())
        win.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0
