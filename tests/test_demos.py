import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from lynn.constants import SCREEN_H, SCREEN_W
from lynn.demos import (
    PALETTE_CELL,
    draw_map_demo,
    draw_palette_demo,
    load_map_demo,
    load_palette_demo,
)
from lynn.main import _cam_for_room
from lynn.paths import project_root


@pytest.fixture(scope="module")
def pygame_dummy():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((SCREEN_W, SCREEN_H))
    yield
    pygame.quit()


def _canvas():
    return pygame.Surface((SCREEN_W, SCREEN_H)).convert()


@pytest.mark.skipif(not (project_root() / "data/palette/ll.pal").is_file(), reason="no pal")
def test_palette_demo_ramp_matches_lut(pygame_dummy):
    palette, surfs = load_palette_demo()
    canvas = _canvas()
    draw_palette_demo(canvas, palette, surfs, elapsed=0.0)
    cell_w, cell_h = PALETTE_CELL
    for i in (0, 1, 15, 16, 255):
        x = (i % 16) * cell_w + 2
        y = (i // 16) * cell_h + 2
        assert canvas.get_at((x, y))[:3] == palette.colors[i]


@pytest.mark.skipif(not (project_root() / "data/pictures/char/lynn24.spr").is_file(), reason="no spr")
def test_palette_demo_draws_lynn_sprite(pygame_dummy):
    palette, surfs = load_palette_demo()
    canvas = _canvas()
    draw_palette_demo(canvas, palette, surfs, elapsed=0.0)
    # Sprite is blitted at (32, 140); sample interior, not the transparent corner.
    px = canvas.get_at((32 + 8, 140 + 12))[:3]
    assert px != (0, 0, 0)
    assert px != palette.colors[0]


def test_map_demo_spawn_is_not_flat_gray(pygame_dummy, map_spec):
    demo = load_map_demo(with_objects=False, map_path=map_spec)
    canvas = _canvas()
    cam_x, cam_y = _cam_for_room(demo.game_map, 0)
    draw_map_demo(canvas, demo, 0, cam_x, cam_y)
    colors = {
        canvas.get_at((x, y))[:3]
        for y in range(0, SCREEN_H, 8)
        for x in range(0, SCREEN_W, 8)
    }
    # Failed blit is 1 color; title.map spawn is a simple loading field (~7).
    assert len(colors) > 2


def test_objects_demo_changes_pixels_vs_tiles_only(pygame_dummy, map_spec):
    tiles = load_map_demo(with_objects=False, map_path=map_spec)
    objs = load_map_demo(with_objects=True, map_path=map_spec)
    if not objs.objects_by_room or not objs.objects_by_room[0]:
        pytest.skip("no XML entities in room 0")
    cam_x, cam_y = _cam_for_room(tiles.game_map, 0)
    a = _canvas()
    b = _canvas()
    draw_map_demo(a, tiles, 0, cam_x, cam_y)
    draw_map_demo(b, objs, 0, cam_x, cam_y)
    tobytes = getattr(pygame.image, "tobytes", pygame.image.tostring)
    assert tobytes(a, "RGB") != tobytes(b, "RGB")
