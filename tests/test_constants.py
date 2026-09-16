"""FB headers/ll/engine_enums.bi enemy_uniques + UniqueCheck suffix order."""

from lynn import constants as C
from lynn.object.char import CharType
from lynn.object.xml_load import _UNIQUE_CHECK_NAMES, _assign_unique_id

# engine_enums.bi consecutive values from u_null = 0.
_ENUM_ORDER = (
    "null",
    "cell",
    "chest",
    "bluechest",
    "bluechestitem",
    "button",
    "gbutton",
    "bshape",
    "gshape",
    "bush",
    "tguard",
    "bguard",
    "eguard",
    "cguard",
    "torch",
    "ltorch",
    "gtorch",
    "ibug",
    "fbug",
    "gold",
    "silver",
    "health",
    "keydoor",
    "fkeydoor",
    "bardoor",
    "static",
    "statue",
    "pushrock",
    "menu",
    "savepoint",
    "crate",
    "crate_health",
    "grult",
    "ghut",
    "hotrock",
    "coldrock",
    "greyrock",
    "bombrock",
    "mole",
    "sign",
    "dyssius",
    "anger",
    "angerfireball",
    "charger",
    "sparkle",
    "sterach",
    "swordie",
    "slimeman",
    "beetle",
    "beamcrystal",
    "antiwall",
    "antiwall2",
    "pmouth",
    "boss5_right",
    "boss5_left",
    "boss5_down",
    "boss5_crystal",
    "pekkle_blue",
    "pekkle_bomb",
    "pekkle_red",
    "pekkle_grey",
    "pekkle_big",
    "goldblock",
    "divine",
    "divine_bug",
    "divine_ball",
    "kambot",
    "auto",
    "mech",
    "haywire",
    "healthguy",
    "godstat",
    "steelstrider",
    "ferus",
    "core",
    "biglarva",
    "battleseed",
    "lynn",
)


def _uid(filename: str) -> int:
    obj = CharType()
    obj.id = f"data/object/{filename}"
    if not filename.endswith(".xml"):
        obj.id += ".xml"
    _assign_unique_id(obj)
    return obj.unique_id


def test_enemy_uniques_match_fb_enum_order():
    assert C.u_null == 0
    assert C.u_lynn == 77
    assert C.u_healthguy == 70
    for i, stem in enumerate(_ENUM_ORDER):
        assert getattr(C, "u_" + stem) == i, stem


def test_uniquecheck_covers_every_unique_and_uses_named_constants():
    for stem in _UNIQUE_CHECK_NAMES:
        assert hasattr(C, "u_" + stem), stem
        assert _uid(stem + ".xml") == getattr(C, "u_" + stem)


def test_uniquecheck_suffix_traps():
    """Longer/overlapping filenames must not steal a shorter unique."""
    assert _uid("bluechest.xml") == C.u_bluechest
    assert _uid("bluechestitem.xml") == C.u_bluechestitem
    assert _uid("chest.xml") == C.u_chest
    assert _uid("gtorch.xml") == C.u_gtorch
    assert _uid("ltorch.xml") == C.u_ltorch
    assert _uid("torch.xml") == C.u_torch
    assert _uid("crate_health.xml") == C.u_crate_health
    assert _uid("health.xml") == C.u_health
    assert _uid("fkeydoor.xml") == C.u_fkeydoor
    assert _uid("keydoor.xml") == C.u_keydoor
    assert _uid("gbutton.xml") == C.u_gbutton
    assert _uid("button.xml") == C.u_button
    assert _uid("divine_ball.xml") == C.u_divine_ball
    assert _uid("divine_bug.xml") == C.u_divine_bug
    assert _uid("divine.xml") == C.u_divine
    assert _uid("antiwall2.xml") == C.u_antiwall2
    assert _uid("antiwall.xml") == C.u_antiwall
    assert _uid("angerfireball.xml") == C.u_angerfireball
    assert _uid("anger.xml") == C.u_anger
    assert _uid("hsavepoint.xml") == C.u_savepoint
    assert _uid("ferus.xml") == C.u_ferus


def test_damage_and_spawn_flags():
    assert C.DF_MAIN_CHAR == 4
    assert C.DF_PROJ == 65536
    assert C.SF_BOX == 1024
    assert C.SO_AND == 2
    assert C.LLFADE_WHITE == 1
    assert C.PROJECTILE_FIREBALL == 6
