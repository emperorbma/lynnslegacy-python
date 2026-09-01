"""FB object_structures.bi — fields needed to load XML and blit idle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from lynn.gfx.image import LLSystem_ImageHeader


@dataclass
class LLObject_ImageHeader:
    x_off: int = 0
    y_off: int = 0
    dir_frames: int = 0
    cur_frame: int = 0
    rate: float = 0.0
    rateMad: float = 0.0
    frame: list = field(default_factory=list)


@dataclass
class LLObject_FrameControl:
    sound_lock: int = 0
    concurrents: int = 0
    concurrent: list = field(default_factory=list)
    rate: float = 0.0
    rateMad: float = 0.0


@dataclass
class EFuncs:
    active_state: int = 0
    states: int = 0
    func: list[list[Callable]] = field(default_factory=list)
    current_func: list[int] = field(default_factory=list)
    func_count: list[int] = field(default_factory=list)


@dataclass
class CharType:
    id: str = ""
    x_origin: int = 0
    y_origin: int = 0
    coords_x: int = 0
    coords_y: int = 0
    direction: int = 0
    ori_dir: int = 0
    frame: int = 0
    current_anim: int = 0
    anims: int = 0
    anim: list[LLSystem_ImageHeader] = field(default_factory=list)
    animControl: list[LLObject_ImageHeader] = field(default_factory=list)
    funcs: EFuncs = field(default_factory=EFuncs)
    uni_directional: int = 0
    no_cam: int = 0
    perimeter_x: int = 0
    perimeter_y: int = 0
    unique_id: int = 0
    hp: int = 0
    maxhp: int = 0
    frame_hold: float = 0.0
    animating: int = 0
    mad: int = 0
    dead: int = 0
    walk_hold: float = 0.0
    walk_speed: float = 0.009
    moving: int = 0
    num: int = 0
    unstoppable_by_screen: int = 0
    unstoppable_by_tile: int = 0
    unstoppable_by_object: int = 0
    impassable: int = 0
    # XML scratch
    frame_sound: int = 0
