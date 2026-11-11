"""FB frame concurrents — Dyssius / Steel Strider icecloud attachments."""

from __future__ import annotations

import lynn.object  # noqa: F401 — register funcs

from lynn import clock
from lynn.object.char import CharType
from lynn.object.concurrent import current_frame_concurrents, execute_concurrents
from lynn.object.tick import tick_objects
from lynn.object.xml_load import LLSystem_ObjectFromXML


def _load(path: str) -> CharType:
    obj = CharType()
    obj.id = path
    return LLSystem_ObjectFromXML(obj, load_images=False)


def test_dyssius_frame_1_has_four_iceclouds():
    boss = _load("data/object/dyssius.xml")
    assert boss.animControl
    ctrl = boss.animControl[0]
    assert len(ctrl.frame) >= 2
    assert ctrl.frame[0].concurrents == 0
    assert ctrl.frame[1].concurrents == 4
    origins = {(c.origin_x, c.origin_y) for c in ctrl.frame[1].concurrent}
    assert origins == {(0, 70), (55, 127), (203, 127), (255, 70)}
    for conc in ctrl.frame[1].concurrent:
        assert conc.char is not None
        assert conc.char.id.endswith("icecloud.xml")
        assert conc.char.anim  # materialized
        assert conc.char.perimeter_x == 32
        assert conc.char.perimeter_y == 32


def test_steelstrider_matches_dyssius_attachments():
    boss = _load("data/object/steelstrider.xml")
    assert boss.animControl[0].frame[1].concurrents == 4
    assert all(
        c.char is not None and c.char.id.endswith("icecloud.xml")
        for c in boss.animControl[0].frame[1].concurrent
    )


def test_execute_concurrents_snaps_to_origin():
    boss = _load("data/object/dyssius.xml")
    boss.coords_x = 100
    boss.coords_y = 200
    boss.frame = 1
    boss.current_anim = 0
    clock.timer = 1.0
    execute_concurrents(boss)
    concs = current_frame_concurrents(boss)
    assert len(concs) == 4
    # origin (0,70), perimeter 32 → coords = parent + origin - 16
    first = next(c for c in concs if c.origin_x == 0 and c.origin_y == 70)
    assert first.char is not None
    assert first.char.coords_x == 100 + 0 - 16
    assert first.char.coords_y == 200 + 70 - 16


def test_frame_0_has_no_active_concurrents():
    boss = _load("data/object/dyssius.xml")
    boss.frame = 0
    assert current_frame_concurrents(boss) == []
    execute_concurrents(boss)  # no-op


def test_tick_objects_runs_concurrents():
    """Attachments tick via ExecuteConcurrents when the boss is on frame 1."""
    boss = _load("data/object/dyssius.xml")
    boss.coords_x = 50
    boss.coords_y = 50
    boss.frame = 1
    clock.timer = 1.0
    tick_objects([boss], cam=None)
    child = boss.animControl[0].frame[1].concurrent[0].char
    assert child is not None
    assert child.coords_x == 50 + 0 - 16
    assert child.coords_y == 50 + 70 - 16
