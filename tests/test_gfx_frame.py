from lynn import clock
from lynn.gfx.image import LLSystem_ImageHeader
from lynn.object.char import CharType, LLObject_FrameControl, LLObject_ImageHeader
from lynn.object.dispatch import lookup_func
from lynn.object.gfx_animation import __idle_animate
from lynn.object.gfx_frame import LLObject_IgnoreDirectional, LLObject_IncrementFrame
from lynn.object.tick import tick_object


def _anim_char(*, frames: int, dir_frames: int, rate: float, uni: int = 0) -> CharType:
    obj = CharType()
    header = LLSystem_ImageHeader(frames=frames)
    ctrl = LLObject_ImageHeader(dir_frames=dir_frames, rate=rate)
    ctrl.frame = [LLObject_FrameControl() for _ in range(frames)]
    obj.anim = [header]
    obj.animControl = [ctrl]
    obj.uni_directional = uni
    return obj


def test_ignore_directional_animating_and_uni():
    obj = CharType()
    assert LLObject_IgnoreDirectional(obj) == 0
    obj.uni_directional = -1
    assert LLObject_IgnoreDirectional(obj) == -1
    obj.uni_directional = 0
    obj.animating = 1
    assert LLObject_IgnoreDirectional(obj) == -1


def test_increment_frame_advances_after_hold():
    clock.timer = 10.0
    obj = _anim_char(frames=4, dir_frames=4, rate=0.5, uni=-1)
    assert LLObject_IncrementFrame(obj) == 0
    assert obj.frame == 1
    assert obj.frame_hold == 10.5
    assert LLObject_IncrementFrame(obj) == 0
    assert obj.frame == 1
    clock.timer = 10.51
    assert LLObject_IncrementFrame(obj) == 0
    assert obj.frame_hold == 0
    assert LLObject_IncrementFrame(obj) == 0
    assert obj.frame == 2


def test_increment_frame_returns_one_at_edge():
    clock.timer = 0.0
    obj = _anim_char(frames=3, dir_frames=3, rate=0.0, uni=-1)
    obj.frame = 2
    assert LLObject_IncrementFrame(obj) == 1
    assert obj.frame == 3


def test_idle_animate_then_return_idle_resets_block():
    import lynn.object  # noqa: F401

    clock.timer = 1.0
    obj = _anim_char(frames=2, dir_frames=2, rate=0.0, uni=-1)
    idle = lookup_func("__idle_animate")
    back = lookup_func("__return_idle")
    obj.funcs.states = 1
    obj.funcs.func = [[idle, back]]
    obj.funcs.func_count = [2]
    obj.funcs.current_func = [0]
    obj.funcs.active_state = 0
    assert __idle_animate(obj) == 0
    obj.frame = 1
    obj.frame_hold = 0
    assert __idle_animate(obj) == 1
    assert obj.frame == 0
    obj.funcs.current_func[0] = 1
    tick_object(obj)
    assert obj.funcs.active_state == 0
    assert obj.funcs.current_func[0] == 0


def test_rtele_xml_binds_idle_animate():
    import lynn.object  # noqa: F401
    from lynn.object.char import CharType
    from lynn.object.xml_load import LLSystem_ObjectFromXML

    obj = CharType()
    obj.id = "data/object/rtele2.xml"
    LLSystem_ObjectFromXML(obj, load_images=False)
    assert obj.funcs.func_count[0] == 2
    assert obj.funcs.func[0][0] is lookup_func("__idle_animate")
    assert obj.funcs.func[0][1] is lookup_func("__return_idle")
