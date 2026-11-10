"""Limbo statue orbs always fire down (FB LLObject_InitializeProjectiles)."""

from lynn.constants import u_statue
from lynn.map.loader import load_mapV
from lynn.object.projectile import LLObject_ClearProjectiles, LLObject_InitializeProjectiles
from lynn.object.xml_load import spawn_from_stub
from lynn.paths import chdir_project_root, resolve_map_path


def test_limbo1_statue_fires_down_despite_map_stub_dir_0():
    """Map stub direction is 0; FB Case u_statue still forces proj direction 2."""
    chdir_project_root()
    m = load_mapV(str(resolve_map_path("limbo1.map")), load_tileset=False)
    stub = m.room[0].enemy[0]
    assert "statue" in stub.id
    assert stub.direction == 0
    obj = spawn_from_stub(stub, load_images=False)
    assert obj.unique_id == u_statue
    assert obj.direction == 0
    assert obj.projectile is not None
    LLObject_ClearProjectiles(obj)
    if not obj.projectile.coords:
        obj.projectile.coords = [[0, 0]]
    obj.projectile.saveDirection = 0
    LLObject_InitializeProjectiles(obj)
    assert obj.projectile.direction == 2
