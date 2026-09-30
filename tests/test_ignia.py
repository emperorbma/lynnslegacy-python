"""Ignia hazards: launcher fans, firebug bursts, Grolle's chase, Anger."""

import lynn.object  # noqa: F401
import lynn.object.boss as boss

from lynn import clock
from lynn.constants import PROJECTILE_8WAY, PROJECTILE_DIAGONAL, TRUE, u_fbug
from lynn.events import bind_hero, bind_room, reset_events
from lynn.object.char import CharType, EFuncs, EntityProjectile
from lynn.object.dispatch import lookup_func
from lynn.object.projectile import enemy_proj_drawable
from lynn.object.xml_load import LLSystem_ObjectFromXML


def _load(path: str) -> CharType:
    obj = CharType()
    obj.id = path
    return LLSystem_ObjectFromXML(obj, load_images=False)


def _funcs(states: int) -> EFuncs:
    return EFuncs(
        states=states,
        func=[[] for _ in range(states)],
        current_func=[0] * states,
        func_count=[1] * states,
    )


def test_dead_enemy_drops_its_shot_but_a_firebug_burst_spreads():
    corpse = CharType()
    corpse.dead = TRUE
    corpse.proj_style = PROJECTILE_DIAGONAL
    corpse.projectile = EntityProjectile(active=PROJECTILE_DIAGONAL, coords=[[10, 10]] * 4, length=20)
    lookup_func("__do_proj")(corpse)
    assert corpse.projectile.active == 0

    bug = _load("data/object/fbug.xml")
    assert bug.unique_id == u_fbug
    assert bug.proj_style == PROJECTILE_DIAGONAL
    bug.coords_x = 100
    bug.coords_y = 120
    bug.dead = TRUE
    assert lookup_func("__trigger_projectile")(bug) == 1
    clock.timer = 5
    lookup_func("__do_proj")(bug)
    assert bug.projectile.active != 0
    assert bug.projectile.travelled == 1
    bug.projectile.refreshTime = 0
    lookup_func("__do_proj")(bug)
    coords = bug.projectile.coords
    assert coords[0][0] < coords[2][0]
    assert coords[0][1] < coords[2][1]
    assert coords[1][0] > coords[3][0]
    assert enemy_proj_drawable(bug)


def test_launcher_eight_way_shots_leave_the_muzzle():
    launcher = _load("data/object/launcher.xml")
    assert launcher.proj_style == PROJECTILE_8WAY
    launcher.coords_x = 200
    launcher.coords_y = 160
    lookup_func("__trigger_projectile")(launcher)
    clock.timer = 5
    lookup_func("__do_proj")(launcher)
    assert enemy_proj_drawable(launcher)
    launcher.projectile.refreshTime = 0
    lookup_func("__do_proj")(launcher)
    coords = launcher.projectile.coords
    assert len({round(pair[0], 4) for pair in coords}) > 1
    assert len({round(pair[1], 4) for pair in coords}) > 1
    # First spoke is straight down (sin 0, cos 1), last spoke is down-left.
    assert coords[0][1] > coords[4][1]
    assert coords[2][0] > coords[6][0]


def test_grolle_reset_returns_to_the_chase():
    grolle = _load("data/object/grolle.xml")
    assert lookup_func("__return_jump_back") is not lookup_func("__noop")
    grolle.funcs.active_state = grolle.reset_state
    assert lookup_func("__return_jump_back")(grolle) == 0
    assert grolle.funcs.active_state == grolle.jump_state
    assert grolle.funcs.current_func[grolle.jump_state] == 1


def test_anger_procs_are_real():
    for name in (
        "__true_active_animate",
        "__anger_trigger",
        "__anger_teleport",
        "__anger_fireball2",
        "__anger_middle",
        "__anger_new_fireball",
        "__anger_kill_fireball",
        "__explode_jump",
        "__anger_fireball_circle",
        "__anger_shoot",
    ):
        assert lookup_func(name) is not lookup_func("__noop"), name


def test_true_active_animate_always_continues():
    anger = CharType()
    assert lookup_func("__true_active_animate")(anger) == 1
    assert anger.animating == 1


def test_anger_trigger_launches_eight_orbs_then_attacks():
    boss._anger_trigger_ball = 0
    reset_events()
    objs = []
    for i in range(59):
        obj = CharType()
        obj.num = i
        obj.funcs = _funcs(3)
        objs.append(obj)
    bind_room(None, objs)
    anger = objs[50]
    fn = lookup_func("__anger_trigger")
    for n in range(7):
        assert fn(anger) == 1
        assert objs[51 + n].funcs.active_state == 1
    assert fn(anger) == 0
    assert objs[58].funcs.active_state == 1
    assert anger.sway == -1
    assert anger.funcs.active_state == 2
    assert fn(anger) == 1
    assert objs[51].funcs.active_state == 1


def test_anger_orb_circle_and_respawn():
    boss._anger_new_ball = 0
    reset_events()
    clock.timer = 3
    ball = CharType()
    ball.x_origin = 100
    ball.y_origin = 200
    ball.radius = 32
    ball.degree = 0
    ball.walk_speed = 0.03
    ball.num = 0
    ball.walk_hold = 0
    assert lookup_func("__anger_fireball_circle")(ball) == 1
    assert ball.coords_x == 100
    assert abs(ball.coords_y - 168) < 1e-4
    assert ball.radius == 32.5
    assert ball.degree == 3

    objs = [CharType() for _ in range(59)]
    for i, obj in enumerate(objs):
        obj.num = i
        obj.degree = 10
        obj.funcs = _funcs(2)
    objs[50].degree = 20
    for i in range(51, 59):
        objs[i].id = "data/object/angerfireball.xml"
        LLSystem_ObjectFromXML(objs[i], load_images=False)
        objs[i].num = i
        objs[i].degree = 10
    bind_room(None, objs)
    anger = objs[50]
    fn = lookup_func("__anger_new_fireball")
    assert fn(anger) == 1
    assert objs[51].lose_time == -1
    assert objs[51].radius == 1
    assert objs[51].degree == 65
    assert objs[51].funcs.active_state == 0
    for _ in range(6):
        assert fn(anger) == 1
    assert fn(anger) == 0
    assert anger.funcs.active_state == 0
    assert objs[58].radius == 1


def test_anger_mouth_shot_homes_once_then_expires():
    boss._anger_lock_x = 1
    boss._anger_lock_y = 1
    reset_events()
    hero = CharType()
    hero.coords_x = 400
    hero.coords_y = 320
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero(hero)
    anger = _load("data/object/anger.xml")
    anger.coords_x = 320
    anger.coords_y = 320
    anger.projectile.length = 8
    clock.timer = 10
    assert lookup_func("__anger_fireball2")(anger) == 1
    assert anger.anger_proj_trig == 1
    assert anger.projectile.coords[0] == [331, 344]
    lookup_func("__do_anger_proj")(anger)
    assert anger.fly_x > 0
    assert anger.projectile.coords[0][0] > 331
    assert anger.anger_proj_trig == 1
    anger.projectile.length = anger.projectile.travelled
    lookup_func("__do_anger_proj")(anger)
    assert anger.anger_proj_trig == 0


def test_anger_middle_teleport_kill_and_orb_shot():
    reset_events()
    anger = CharType()
    anger.coords_x = 10
    anger.coords_y = 10
    assert lookup_func("__anger_middle")(anger) == 1
    assert (anger.coords_x, anger.coords_y) == (320, 320)
    anger.sway = 4
    assert lookup_func("__anger_teleport")(anger) == 1
    assert 256 <= anger.coords_x <= 415
    assert 256 <= anger.coords_y <= 415
    assert anger.sway == 0
    assert lookup_func("__explode_jump")(anger) == 1
    assert anger.jump_count == 20000

    objs = [CharType() for _ in range(59)]
    bind_room(None, objs)
    lookup_func("__anger_kill_fireball")(anger)
    assert all(objs[i].dead != 0 for i in range(51, 59))

    hero = CharType()
    hero.coords_x = 200
    hero.coords_y = 100
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    bind_hero(hero)
    orb = _load("data/object/angerfireball.xml")
    orb.coords_x = 40
    orb.coords_y = 40
    orb.perimeter_x = 16
    orb.perimeter_y = 16
    orb.projectile.length = 3
    clock.timer = 20
    orb.fly_timer = 0
    assert lookup_func("__anger_shoot")(orb) == 0 or orb.dead != 0
    assert orb.coords_x > 40
    assert orb.coords_y > 40
