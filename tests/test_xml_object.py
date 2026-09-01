from pathlib import Path

import pytest

from lynn.object.char import CharType
from lynn.object.dispatch import BLOCK_MACROS, lookup_func
from lynn.object.xml_load import LLSystem_ObjectFromXML
from lynn.paths import project_root

OBJ = project_root() / "data" / "object"


def _load(name: str) -> CharType:
    obj = CharType()
    obj.id = str(OBJ / name).replace("\\", "/")
    # Tests resolve via relative data/ paths like the engine.
    obj.id = f"data/object/{name}"
    return LLSystem_ObjectFromXML(obj, load_images=False)


@pytest.mark.skipif(not (OBJ / "chest.xml").is_file(), reason="chest.xml missing")
def test_chest_sprites_and_idle_fp():
    obj = _load("chest.xml")
    assert obj.anims == 2
    assert obj.anim[0].filename.endswith("chest.spr")
    assert obj.funcs.states == 4
    assert obj.funcs.func_count[0] == 1
    assert obj.funcs.func_count[1] == 5
    assert obj.uni_directional == 1
    assert obj.perimeter_x == 16
    assert obj.hp == 1


@pytest.mark.skipif(not (OBJ / "bat.xml").is_file(), reason="bat.xml missing")
def test_bat_proc_ids_and_dead_drop_block():
    obj = _load("bat.xml")
    assert obj.hit_state == 1
    assert obj.death_state == 2
    assert obj.fire_state == 3
    assert obj.ice_state == 4
    assert obj.funcs.func_count[2] == len(BLOCK_MACROS["dead_drop_block"])
    assert obj.funcs.func_count[3] == len(BLOCK_MACROS["fire_block"])
    assert obj.animControl[0].dir_frames == 4


@pytest.mark.skipif(not (OBJ / "lynn.xml").is_file(), reason="lynn.xml missing")
def test_lynn_walk_sprite():
    obj = _load("lynn.xml")
    assert obj.anim[0].filename.endswith("lynn24.spr")
    assert obj.animControl[0].dir_frames == 8
    assert obj.animControl[0].y_off == 8
    assert obj.animControl[0].rate == pytest.approx(0.08)


def test_bush_dead_sound_name_resolves():
    from lynn.audio import sound_bush, sound_null

    obj = _load("bush.xml")
    assert obj.dead_sound == sound_bush
    assert obj.hit_sound == sound_null


def test_unknown_func_returns_zero():
    fn = lookup_func("__definitely_missing_func")
    dummy = CharType()
    assert fn(dummy) == 0
