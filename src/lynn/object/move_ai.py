"""FB object_move.bas __randomize_path / __walk (roamer patrol)."""

from __future__ import annotations

import random

import lynn.events as events
from lynn import clock
from lynn.map.collision import move_object
from lynn.object.char import CharType
from lynn.object.dispatch import register_func
from lynn.object.gfx_frame import LLObject_IncrementFrame

MO_JUST_CHECKING = -1


def __randomize_path(this: CharType) -> int:
    length = int(this.walk_length) if this.walk_length else 40
    this.walk_buffer = length - (int(random.random() * (length + 1)) - (length // 2))
    room = events.current_room
    others = events.current_others
    for _ in range(20):
        this.direction += int(random.random() * 3) - 1
        if this.direction == -1:
            this.direction = 3
        this.direction = abs(this.direction) & 3
        if room is None:
            break
        if move_object(this, room, only_looking=MO_JUST_CHECKING, others=others) != 0:
            break
    return 1


def __walk(this: CharType) -> int:
    room = events.current_room
    others = events.current_others
    if this.walk_buffer <= 0:
        this.walk_buffer = int(this.walk_length) if this.walk_length else 40
    if clock.timer > this.walk_hold:
        this.walk_hold = 0
    if this.walk_hold == 0 and room is not None:
        moved = move_object(this, room, only_looking=0, moment=1, others=others)
        this.walk_hold = clock.timer + (this.walk_speed or 0.059)
        if moved != 0:
            this.walk_steps += 1
            if LLObject_IncrementFrame(this) != 0:
                this.frame = 0
                rate = this.animControl[this.current_anim].rate if this.animControl else 0.03
                this.frame_hold = clock.timer + rate
        else:
            this.walk_steps = this.walk_buffer
    if this.walk_steps >= this.walk_buffer:
        this.frame = 0
        this.walk_steps = 0
        return 1
    return 0


def __copter_path(this: CharType) -> int:
    """FB object_move.bas: 8-dir random heading that can actually step."""
    this.walk_buffer = int(this.walk_length) if this.walk_length else 80
    room = events.current_room
    others = events.current_others
    for _ in range(20):
        this.direction += int(random.random() * 8) - 1
        if this.direction == -1:
            this.direction = 7
        this.direction = abs(this.direction) & 7
        if room is None:
            break
        if move_object(this, room, only_looking=MO_JUST_CHECKING, others=others) != 0:
            break
    return 1


register_func("__randomize_path", __randomize_path)
register_func("__walk", __walk)
register_func("__copter_path", __copter_path)