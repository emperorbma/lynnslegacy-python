"""FB LLEngine_ExecuteConcurrents — frame-attached secondary objects (iceclouds)."""

from __future__ import annotations

from lynn.object.char import CharType, LLObject_FrameConcurrent


def current_frame_concurrents(obj: CharType) -> list[LLObject_FrameConcurrent]:
    """Attachments for the parent's current anim/frame, if any."""
    if not obj.animControl or not (0 <= obj.current_anim < len(obj.animControl)):
        return []
    ctrl = obj.animControl[obj.current_anim]
    if not ctrl.frame:
        return []
    fi = int(obj.frame)
    if fi < 0 or fi >= len(ctrl.frame):
        return []
    fc = ctrl.frame[fi]
    if not fc.concurrents or not fc.concurrent:
        return []
    return list(fc.concurrent)


def execute_concurrents(obj: CharType) -> None:
    """FB LLEngine_ExecuteConcurrents: tick each attachment then snap to origin.

    Position: parent.coords + (origin - perimeter/2).
    """
    from lynn.object.tick import tick_object

    for conc in current_frame_concurrents(obj):
        child = conc.char
        if child is None:
            continue
        tick_object(child)
        child.coords_x = int(obj.coords_x) + conc.origin_x - (int(child.perimeter_x) >> 1)
        child.coords_y = int(obj.coords_y) + conc.origin_y - (int(child.perimeter_y) >> 1)
        child.x_origin = child.coords_x
        child.y_origin = child.coords_y
