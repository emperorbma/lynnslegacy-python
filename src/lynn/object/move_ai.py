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


def _in_dir_small(d: int) -> int:
    if d < 0:
        return 3
    if d > 3:
        return 0
    return d


def __make_face(this: CharType) -> int:
    """FB object_move.bas: face the hero on the longer axis."""
    hero = events.hero
    if hero is None:
        return 1
    ox = this.coords_x + (int(this.perimeter_x) >> 1)
    oy = this.coords_y + (int(this.perimeter_y) >> 1)
    hx = hero.coords_x + (int(hero.perimeter_x) >> 1)
    hy = hero.coords_y + (int(hero.perimeter_y) >> 1)
    dx = abs(hx - ox)
    dy = abs(hy - oy)
    if dx >= dy:
        if hx > ox:
            this.direction = 1
        elif hx < ox:
            this.direction = 3
    else:
        if hy > oy:
            this.direction = 2
        elif hy < oy:
            this.direction = 0
    return 1


def __chase(this: CharType) -> int:
    """FB object_move.bas: home in on the hero until out_proximity resets."""
    import math

    hero = events.hero
    room = events.current_room
    others = events.current_others
    if hero is None:
        return 0
    hx = hero.coords_x + (int(hero.perimeter_x) >> 1)
    hy = hero.coords_y + (int(hero.perimeter_y) >> 1)
    ox = this.coords_x + (int(this.perimeter_x) >> 1)
    oy = this.coords_y + (int(this.perimeter_y) >> 1)
    if this.sway == 0:
        this.degree = (this.degree + 1) % 360
        this.sway = clock.timer + 0.002
    if clock.timer > this.sway:
        this.sway = 0
    if this.walk_hold == 0 and room is not None:
        px = 1 if hx > ox else (-1 if hx < ox else 0)
        py = 1 if hy > oy else (-1 if hy < oy else 0)
        if px == 1 and py == 1:
            this.direction = 6
        elif px == 1 and py == 0:
            this.direction = 1
        elif px == 1 and py == -1:
            this.direction = 5
        elif px == -1 and py == 1:
            this.direction = 7
        elif px == -1 and py == 0:
            this.direction = 3
        elif px == -1 and py == -1:
            this.direction = 4
        elif px == 0 and py == 1:
            this.direction = 2
        elif px == 0 and py == -1:
            this.direction = 0
        if px != 0 or py != 0:
            if move_object(this, room, only_looking=0, moment=1, others=others) == 0:
                tmp = this.direction
                sway_calc = math.sin(math.radians(this.degree))
                if sway_calc > 0:
                    this.direction += 1
                elif sway_calc < 0:
                    this.direction -= 1
                this.direction = _in_dir_small(this.direction)
                move_object(this, room, only_looking=0, moment=1, others=others)
                this.direction = tmp
        if this.uni_directional == 0:
            this.direction = _in_dir_small(this.direction)
        __make_face(this)
        rate = this.mad_walk_speed if this.mad_walk_speed else (this.walk_speed or 0.059)
        this.walk_hold = clock.timer + rate
        if this.animControl and this.current_anim < len(this.animControl):
            if LLObject_IncrementFrame(this) != 0:
                this.frame = 0
                ctrl = this.animControl[this.current_anim]
                mad = ctrl.rateMad if ctrl.rateMad else (ctrl.rate or 0.03)
                this.frame_hold = clock.timer + mad
    if clock.timer > this.walk_hold:
        this.walk_hold = 0
    return 0


def __home(this: CharType) -> int:
    """FB object_move.bas: walk to dest_x/dest_y one axis at a time."""
    room = events.current_room
    others = events.current_others
    this.moving = 0
    x_home = int(this.dest_x)
    y_home = int(this.dest_y)
    if int(this.coords_x) == x_home and int(this.coords_y) == y_home:
        this.walk_hold = 0
        this.frame = 0
        return 1
    if room is None:
        this.coords_x = x_home
        this.coords_y = y_home
        this.walk_hold = 0
        this.frame = 0
        return 1

    def _back() -> None:
        if this.moveBackwards != 0:
            this.direction = (int(this.direction) + 2) & 3

    if this.walk_hold == 0:
        y_move = 0
        if y_home > this.coords_y:
            y_move = 1
        elif y_home < this.coords_y:
            y_move = -1
        if y_move == -1:
            this.direction = 0
        elif y_move == 1:
            this.direction = 2
        if y_move != 0:
            move_object(this, room, only_looking=0, moment=1, others=others)
            _back()
        x_move = 0
        if x_home > this.coords_x:
            x_move = 1
        elif x_home < this.coords_x:
            x_move = -1
        if x_move == -1:
            this.direction = 3
        elif x_move == 1:
            this.direction = 1
        if x_move != 0:
            move_object(this, room, only_looking=0, moment=1, others=others)
            _back()
        if int(this.coords_x) == x_home and int(this.coords_y) == y_home:
            this.walk_hold = 0
            this.frame = 0
            this.moving = 0
            return 1
        this.walk_hold = clock.timer + (this.walk_speed or 0.059)
        this.moving = 1
    if clock.timer >= this.walk_hold:
        this.walk_hold = 0
    if LLObject_IncrementFrame(this) != 0:
        this.frame = 0
        rate = this.animControl[this.current_anim].rate if this.animControl else 0.08
        this.frame_hold = clock.timer + rate
    return 0


def __move_backwards(this: CharType) -> int:
    this.moveBackwards = -1
    return 1


def __move_normal(this: CharType) -> int:
    this.moveBackwards = 0
    return 1


register_func("__randomize_path", __randomize_path)
register_func("__walk", __walk)
register_func("__copter_path", __copter_path)
register_func("__make_face", __make_face)
register_func("__chase", __chase)
register_func("__home", __home)
register_func("__move_backwards", __move_backwards)
register_func("__move_normal", __move_normal)