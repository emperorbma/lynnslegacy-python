"""FB fidelity: __flicker and __cell_bounce."""

import lynn.object  # noqa: F401
import lynn.object.move_ai  # noqa: F401
from lynn import clock
from lynn.constants import u_charger
from lynn.events import bind_room, reset_events
from lynn.map.types import RoomType
from lynn.object.dispatch import lookup_func
from lynn.object.char import CharType
from lynn.object.xml_load import LLSystem_ObjectFromXML


def test_flicker_is_the_real_blink_not_a_stub():
    reset_events()
    flicker = lookup_func("__flicker")
    this = CharType()
    this.flash_length = 3
    this.flash_time = 0.02
    clock.timer = 10.0
    assert flicker(this) == 0
    assert this.invisible != 0
    results = []
    for _ in range(10):
        clock.timer += 0.03
        results.append(flicker(this))
        if results[-1]:
            break
    assert results[-1] == 1
    assert this.invisible == 0 and this.flash_count == 0


def test_flicker_exits_early_for_dead_charger():
    flicker = lookup_func("__flicker")
    this = CharType()
    this.flash_length = 30
    this.unique_id = u_charger
    this.dead = 1
    clock.timer = 10.0
    assert flicker(this) == 1


def test_cell_bounce_reflects_off_a_wall():
    reset_events()
    cell = lookup_func("__cell_bounce")
    this = CharType()
    this.id = "data/object/cell.xml"
    LLSystem_ObjectFromXML(this, load_images=False)
    this.direction = 5
    this.walk_hold = 0
    this.coords_x = 0
    this.coords_y = 0
    room = RoomType()
    room.x = room.y = 4
    bind_room(room, [this])
    clock.timer = 10.0
    assert cell(this) == 1
    assert this.walk_hold > clock.timer
    assert 4 <= this.direction <= 7
