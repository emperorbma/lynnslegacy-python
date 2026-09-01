"""FB engine--object_XML.bas / Lua engine_object_XML.lua."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from lynn.gfx.image import LLSystem_ImageHeader, LLSystem_ImageLoad
from lynn.object.char import CharType, LLObject_FrameControl, LLObject_ImageHeader
from lynn.object.dispatch import BLOCK_MACROS, lookup_func
from lynn.paths import project_root


def _resolve(rel: str) -> Path:
    p = Path(rel.replace("\\", "/"))
    if p.is_file():
        return p
    return project_root() / p

_IMAGE_CACHE: dict[str, LLSystem_ImageHeader] = {}
_XML_CACHE: dict[str, str] = {}


def get_image_header(filename: str, load_pixels: bool = True) -> LLSystem_ImageHeader:
    key = filename.replace("\\", "/").lower()
    if key not in _IMAGE_CACHE:
        path = _resolve(key)
        if load_pixels and path.is_file():
            _IMAGE_CACHE[key] = LLSystem_ImageLoad(str(path))
        else:
            header = LLSystem_ImageHeader(filename=key)
            _IMAGE_CACHE[key] = header
    return _IMAGE_CACHE[key]


def get_object_xml(object_id: str) -> str:
    key = object_id.replace("\\", "/").lower()
    if key not in _XML_CACHE:
        _XML_CACHE[key] = _resolve(key).read_text(encoding="latin-1")
    return _XML_CACHE[key]


def _xml_number(text: str):
    text = text.strip()
    if text == "":
        return None
    try:
        if "." in text or "e" in text.lower():
            return float(text)
        return int(text)
    except ValueError:
        return None


def _install(obj: CharType, func_name: str) -> None:
    state = obj.funcs.active_state
    idx = obj.funcs.current_func[state]
    lst = obj.funcs.func[state]
    while len(lst) <= idx:
        lst.append(lookup_func("__noop"))
    lst[idx] = lookup_func(func_name)
    obj.funcs.current_func[state] = idx + 1


def LLSystem_ObjectFromXML(obj: CharType, load_images: bool = True) -> CharType:
    xml_text = get_object_xml(obj.id)
    root = ET.fromstring(xml_text)
    path: list[str] = []

    def start(elem: ET.Element) -> None:
        path.append(elem.tag.lower())
        name = elem.tag.lower()
        if name == "sprite":
            obj.current_anim = obj.anims
            obj.anims += 1
            obj.anim.append(LLSystem_ImageHeader())
            obj.animControl.append(LLObject_ImageHeader())
        elif name == "fp":
            obj.funcs.active_state = obj.funcs.states
            obj.funcs.func.append([])
            obj.funcs.func_count.append(0)
            obj.funcs.current_func.append(0)
            obj.funcs.states += 1
        elif name == "snd":
            pass

    def text_node(elem: ET.Element) -> None:
        if elem.text is None:
            return
        text = elem.text.strip().replace("\\", "/")
        if text == "" or len(path) < 2:
            return
        if path[1] == "sprite":
            _sprite_text(obj, path, text, load_images)
        elif path[1] == "fp":
            _fp_text(obj, path, text)
        elif len(path) == 2:
            converted = _xml_number(text)
            if converted is None:
                setattr(obj, path[1], text)
            else:
                setattr(obj, path[1], converted)

    def close(name: str) -> None:
        if name.lower() == "fp" and obj.funcs.states:
            obj.funcs.current_func[obj.funcs.active_state] = 0
        if path:
            path.pop()

    def walk(elem: ET.Element) -> None:
        start(elem)
        text_node(elem)
        for child in elem:
            walk(child)
        close(elem.tag)

    walk(root)
    if getattr(obj, "real_x", None) is not None:
        obj.perimeter_x = int(obj.real_x)
    if getattr(obj, "real_y", None) is not None:
        obj.perimeter_y = int(obj.real_y)
    obj.current_anim = 0
    obj.funcs.active_state = 0
    return obj


def _sprite_text(obj: CharType, path: list[str], text: str, load_images: bool) -> None:
    anim = obj.anim[obj.current_anim]
    ctrl = obj.animControl[obj.current_anim]
    if len(path) == 3 and path[2] == "filename":
        header = get_image_header(text, load_pixels=load_images)
        obj.anim[obj.current_anim] = header
        ctrl.frame = [LLObject_FrameControl() for _ in range(max(header.frames, 1))]
    elif len(path) == 3 and path[2] == "dir_frames":
        ctrl.dir_frames = int(_xml_number(text) or 0)
    elif len(path) == 3 and path[2] == "rate":
        ctrl.rate = float(_xml_number(text) or 0)
    elif len(path) == 3 and path[2] == "madrate":
        ctrl.rateMad = float(_xml_number(text) or 0)
    elif len(path) == 3 and path[2] == "x_off":
        ctrl.x_off = int(_xml_number(text) or 0)
    elif len(path) == 3 and path[2] == "y_off":
        ctrl.y_off = int(_xml_number(text) or 0)
    elif len(path) == 3 and path[2] == "anim_id":
        if text == "dead_anim":
            obj.dead_anim = obj.current_anim
        elif text == "proj_anim":
            obj.proj_anim = obj.current_anim
        elif text == "expl_anim":
            obj.expl_anim = obj.current_anim
    elif len(path) >= 4 and path[2] == "sound" and path[3] == "frame":
        obj.frame_sound = int(_xml_number(text) or 0)


def _fp_text(obj: CharType, path: list[str], text: str) -> None:
    if len(path) < 3:
        return
    kind = path[2]
    state = obj.funcs.active_state
    if kind == "proc_id":
        setattr(obj, text, state)
    elif kind == "func":
        obj.funcs.func_count[state] += 1
        _install(obj, "__" + text)
    elif kind == "block_macro":
        names = BLOCK_MACROS.get(text, ())
        obj.funcs.func_count[state] += len(names)
        for name in names:
            _install(obj, name)


def LLSystem_CopyNewObject(obj: CharType, load_images: bool = True) -> CharType:
    return LLSystem_ObjectFromXML(obj, load_images=load_images)


def spawn_from_stub(stub, load_images: bool = True) -> CharType:
    obj = CharType()
    obj.id = stub.id.replace("\\", "/")
    LLSystem_CopyNewObject(obj, load_images=load_images)
    obj.x_origin = stub.x_origin
    obj.y_origin = stub.y_origin
    obj.coords_x = stub.x_origin
    obj.coords_y = stub.y_origin
    obj.direction = stub.direction
    obj.ori_dir = stub.direction
    return obj
