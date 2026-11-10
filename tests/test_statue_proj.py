"""FB Case u_statue: orbs always fire down (2), superseding map stub facing."""

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


def test_limbo1_statue_stub_dir_0_still_fires_down():
    """gmap leaves stub direction 0; FB hardcode supersedes to 2."""
    chdir_project_root()
    m = load_mapV(str(resolve_map_path("limbo1.map")), load_tileset=False)
    stub = m.room[0].enemy[0]
    assert "statue" in stub.id
    assert stub.direction == 0
    obj = spawn_from_stub(stub, load_images=False)
    assert obj.unique_id == u_statue
    assert obj.direction == 0
    assert _init_proj(obj) == 2


def test_arx_statue_stub_dir_2_also_fires_down():
    chdir_project_root()
    m = load_mapV(str(resolve_map_path("arx.map")), load_tileset=False)
    stub = m.room[20].enemy[0]
    assert "statue" in stub.id
    assert stub.direction == 2
    obj = spawn_from_stub(stub, load_images=False)
    assert _init_proj(obj) == 2
