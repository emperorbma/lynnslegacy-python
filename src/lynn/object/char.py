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
    low_frame: float = 0.0
    high_frame: float = 0.0
    is_psfing: int = 0
    no_cam: int = 0
    perimeter_x: int = 0
    perimeter_y: int = 0
    unique_id: int = 0
    strength: int = 0
    hp: int = 0
    maxhp: int = 0
    money: int = 0
    frame_hold: float = 0.0
    animating: int = 0
    mad: int = 0
    dead: int = 0
    total_dead: int = 0
    dead_hold: float = 0.0
    walk_hold: float = 0.0
    walk_speed: float = 0.009
    walk_length: int = 0
    walk_buffer: int = 0
    walk_steps: int = 0
    pause: float = 0.0
    on_ice: int = 0
    moving: int = 0
    num: int = 0
    unstoppable_by_screen: int = 0
    unstoppable_by_tile: int = 0
    unstoppable_by_object: int = 0
    impassable: int = 0
    switch_room: int = -1
    to_map: str = ""
    to_entry: int = 0
    # XML scratch
    frame_sound: int = 0
    action_sequence: int = 0
    seq_here: int = 0
    seq: list = field(default_factory=list)
    sel_seq: int = 0
    seq_release: int = 0
    seq_paused: int = 0
    spawn_cond: int = 0
    spawn_info: object | None = None
    spawn_kill_trig: int = 0
    spawn_wait_trig: int = 0
    chap: int = 0
    return_trig: int = 0
    invisible: int = 0
    invincible: int = 0
    dest_x: int = 0
    dest_y: int = 0
    moveBackwards: int = 0
    mod_lock: int = 0
    jump_count: int = 0
    jump_counter: int = 0
    jump_timer: float = 0.0
    jump_time: float = 0.0
    fade_time: float = 0.0
    fade_timer: float = 0.0
    fade_count: int = 0
    placed: int = 0
    state_shift: int = 0
    attack_state: int = 0
    hit_state: int = 0
    death_state: int = 0
    reset_state: int = 0
    dead_anim: int = 0
    dmg_id: int = 0
    dmg_index: int = 0
    dmg_specific: int = 0
    hurt: int = 0
    frame_check: int = 0
    fly_x: int = 0
    fly_y: int = 0
    fly_count: int = 0
    fly_timer: float = 0.0
    fly_length: int = 0
    fly_speed: float = 0.0
    fly_hold: int = 0
    mad_walk_speed: float = 0.0
    diag_chase: int = 0
    degree: int = 0
    sway: float = 0.0
    swaying: int = 0
    flash_timer: float = 0.0
    flash_count: int = 0
    flash_length: int = 30
    flash_time: float = 0.02
    mace_weak: int = 0
    star_weak: int = 0
    psycho: int = 0
    dropped: int = 0
    drop_x: int = 0
    drop_y: int = 0
    d_health: int = 0
    d_gold: int = 0
    d_silver: int = 0
    n_gold: int = 0
    n_silver: int = 0
    hit_sound: int = 0
    dead_sound: int = 0
    hit_sound_vol: int = 0
    dead_sound_vol: int = 0
    froggy: int = 0
    vision_field: int = 0
    jump_state: int = 0
    lose_time: float = 0.0
    must_align: int = 0
    shifty: int = 0
    shifty_lock: int = 0
    shifty_state: int = 0
    side_vision: int = 0
    menu_lock: int = 0
    menu_sel: int = 0
    read_lock: int = 0
    reset_delay: float = 0.0
    far_reset_delay: float = 0.0
    pause_hold: float = 0.0
    key: int = 0
    save: list = field(default_factory=list)
