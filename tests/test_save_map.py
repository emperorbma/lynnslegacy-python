"""save_mapV round-trips the uncompressed map blob load_mapV reads."""

from __future__ import annotations

from pathlib import Path

from lynn.map.loader import load_mapV
from lynn.map.saver import map_to_bytes, save_mapV
from lynn.paths import chdir_project_root, resolve_map_path


def _cmp_maps(a, b) -> None:
    assert a.entries == b.entries
    assert a.rooms == b.rooms
    assert a.tileset_filename.replace("\\", "/") == b.tileset_filename.replace("\\", "/")
    assert len(a.room) == len(b.room)
    for ra, rb in zip(a.room, b.room, strict=True):
        assert (ra.x, ra.y, ra.parallax, ra.dark, ra.teleports, ra.enemies) == (
            rb.x,
            rb.y,
            rb.parallax,
            rb.dark,
            rb.teleports,
            rb.enemies,
        )
        assert ra.layout == rb.layout
        assert len(ra.enemy) == len(rb.enemy)
        for ea, eb in zip(ra.enemy, rb.enemy, strict=True):
            assert ea.x_origin == eb.x_origin
            assert ea.y_origin == eb.y_origin
            assert ea.id.replace("\\", "/") == eb.id.replace("\\", "/")
            assert ea.direction == eb.direction
            assert ea.seq_here == eb.seq_here
            assert ea.spawn_cond == eb.spawn_cond


def test_limbo1_roundtrip_bytes_reload(tmp_path: Path):
    chdir_project_root()
    src = resolve_map_path("limbo1.map")
    original = load_mapV(str(src), load_tileset=False)
    out = tmp_path / "limbo1_round.map"
    save_mapV(out, original)
    reloaded = load_mapV(str(out), load_tileset=False)
    _cmp_maps(original, reloaded)
    # Structural payload (ignore trailing pad zeros on some shipped maps).
    assert map_to_bytes(original, "data\\map\\limbo1.map") == map_to_bytes(
        reloaded, "data\\map\\limbo1.map"
    )


def test_statue_direction_survives_save(tmp_path: Path):
    chdir_project_root()
    src = resolve_map_path("limbo1.map")
    m = load_mapV(str(src), load_tileset=False)
    stub = m.room[0].enemy[0]
    assert "statue" in stub.id
    stub.direction = 2
    out = tmp_path / "limbo1_dir.map"
    save_mapV(out, m)
    again = load_mapV(str(out), load_tileset=False)
    assert again.room[0].enemy[0].direction == 2
