"""Statue orb direction follows the map stub (0=up, 2=down)."""

from lynn.constants import u_statue
from lynn.map.loader import load_mapV
from lynn.object.projectile import LLObject_ClearProjectiles, LLObject_InitializeProjectiles
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import chdir_project_root, resolve_map_path


def _init_proj(obj):
    assert obj.projectile is not None
    LLObject_ClearProjectiles(obj)
    if not obj.projectile.coords:
        obj.projectile.coords = [[0, 0]]
    obj.projectile.saveDirection = 0
    LLObject_InitializeProjectiles(obj)
    return obj.projectile.direction


def test_limbo1_statue_map_dir_fires_down():
    chdir_project_root()
    m = load_mapV(str(resolve_map_path("limbo1.map")), load_tileset=False)
    stub = m.room[0].enemy[0]
    assert "statue" in stub.id
    assert stub.direction == 2
    obj = spawn_from_stub(stub, load_images=False)
    assert obj.unique_id == u_statue
    assert _init_proj(obj) == 2


def test_arx_statue_map_dir_0_fires_up():
    """Arx rooms that seat the statue below Lynn keep stub direction 0."""
    chdir_project_root()
    m = load_mapV(str(resolve_map_path("arx.map")), load_tileset=False)
    stub = m.room[42].enemy[8]
    assert "statue" in stub.id
    assert stub.direction == 0
    obj = spawn_from_stub(stub, load_images=False)
    assert obj.unique_id == u_statue
    assert _init_proj(obj) == 0
