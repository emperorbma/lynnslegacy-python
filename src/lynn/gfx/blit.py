"""SCREEN 13 tile blit. FB LLEngine_BlitLayer / Lua layoutLayer."""

from __future__ import annotations

import pygame

from lynn.constants import SCREEN_H, SCREEN_W
from lynn.map.types import RoomType


def blit_layer(
    canvas: pygame.Surface,
    room: RoomType,
    layer: int,
    tile_surfs: list[pygame.Surface],
    cam_x: int,
    cam_y: int,
) -> None:
    if layer >= len(room.layout) or not tile_surfs:
        return
    layout = room.layout[layer]
    tile_w = tile_surfs[0].get_width()
    tile_h = tile_surfs[0].get_height()
    top_tx = cam_x // tile_w
    top_ty = cam_y // tile_h
    off_x = -(cam_x % tile_w)
    off_y = -(cam_y % tile_h)
    # 21 columns (0..320 step 16), 14 rows (0..208 step 16) — matches FB/Lua.
    cols = SCREEN_W // tile_w + 1
    rows = SCREEN_H // tile_h + 2
    for row in range(rows):
        ty = top_ty + row
        screen_y = off_y + row * tile_h
        for col in range(cols):
            tx = top_tx + col
            if tx < 0 or ty < 0 or tx >= room.x or ty >= room.y:
                continue
            idx = ty * room.x + tx
            if idx < 0 or idx >= len(layout):
                continue
            tile_index = layout[idx] & 0xFF
            if tile_index == 0 or tile_index >= len(tile_surfs):
                continue
            canvas.blit(tile_surfs[tile_index], (off_x + col * tile_w, screen_y))


def blit_room_tiles(
    canvas: pygame.Surface,
    room: RoomType,
    tile_surfs: list[pygame.Surface],
    cam_x: int,
    cam_y: int,
    para_surf: pygame.Surface | None = None,
    layers: tuple[int, ...] = (0, 1, 2),
) -> None:
    if para_surf is not None:
        canvas.blit(para_surf, (-cam_x // 12, -cam_y // 12))
    for layer in layers:
        blit_layer(canvas, room, layer, tile_surfs, cam_x, cam_y)


def blit_object(canvas: pygame.Surface, obj, cam_x: int, cam_y: int, tile_surfs_for_anim) -> None:
    """FB blit_object_ex. tile_surfs_for_anim is the current anim's frame surfaces."""
    from lynn.macros import LLObject_CalculateFrame

    if not tile_surfs_for_anim:
        return
    ctrl = obj.animControl[obj.current_anim] if obj.animControl else None
    x_off = ctrl.x_off if ctrl else 0
    y_off = ctrl.y_off if ctrl else 0
    frame = LLObject_CalculateFrame(obj)
    if frame < 0 or frame >= len(tile_surfs_for_anim):
        frame = 0
    x = int(obj.coords_x) - (0 if obj.no_cam else cam_x) - x_off
    y = int(obj.coords_y) - (0 if obj.no_cam else cam_y) - y_off
    canvas.blit(tile_surfs_for_anim[frame], (x, y))
