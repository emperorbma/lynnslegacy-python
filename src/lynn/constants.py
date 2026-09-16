"""FB headers/ll/constants.bi"""

FALSE = 0
TRUE = ~FALSE  # -1
NULL = 0

LL_EVENTS_MAX = 4096
MAX_TEMP_ENEMIES = 90
conf_Box = 65536

SCREEN_W = 320
SCREEN_H = 200

DF_NO_DAMAGE = 0
DF_ROOM_ENEMY = 1
DF_TEMP_ENEMY = 2
DF_MAIN_CHAR = 4
DF_PROJ = 65536

# FB LLPROJECTILE_STYLES
PROJECTILE_NONE = 0
PROJECTILE_ORB = 1
PROJECTILE_BEAM = 2
PROJECTILE_DIAGONAL = 3
PROJECTILE_CROSS = 4
PROJECTILE_8WAY = 5
PROJECTILE_FIREBALL = 6
PROJECTILE_SCHIZO = 7
PROJECTILE_SPIRAL = 8
PROJECTILE_SUN = 9
PROJECTILE_TRACK = 10

PROJ_STYLE_COUNTS: dict[str, tuple[int, int]] = {
    "projectile_fireball": (PROJECTILE_FIREBALL, 1),
    "projectile_orb": (PROJECTILE_ORB, 2),
    "projectile_beam": (PROJECTILE_BEAM, 2),
    "projectile_diagonal": (PROJECTILE_DIAGONAL, 4),
    "projectile_cross": (PROJECTILE_CROSS, 4),
    "projectile_8way": (PROJECTILE_8WAY, 8),
    "projectile_schizo": (PROJECTILE_SCHIZO, 24),
    "projectile_spiral": (PROJECTILE_SPIRAL, 8),
    "projectile_sun": (PROJECTILE_SUN, 128),
    "projectile_track": (PROJECTILE_TRACK, 1),
}

# FB ll_object_flags / _channels / box_jumps / ll_entity_codes.
no_alloc = 1
channel_static = 64
channel_gulls = 69
channel_sea = 70
channel_crickets = 71
box_jump_back = 0
box_kill_switch = 1
ent_textbox = 1024

# FB MO_FLAGS
MO_JUST_CHECKING = -1
MO_NO_RECURSION = -1

# FB LL_OBJVECTOR_FLAGS
OV_ONEBOX = 0
OV_FACE = 1

# FB LL_SEQUENCE_FLAGS
SF_BOX = 1024

# FB LLOBJECT_SPAWN_OPS
SO_NOT = 1
SO_AND = 2
SO_OR = 4

# FB sound_manage
sound_loop = 1

# FB LLMINI_DOORTYPES
DOOR_OPEN = 0
DOOR_LOCKED = 1
DOOR_BARRED = 2
DOOR_FKEYLOCKED = 3
DOOR_STAIR = 4

# FB LLFADE_FADETYPES
LLFADE_NORMAL = 0
LLFADE_WHITE = 1
LLFADE_GRAY = 2

# FB BOXSTUFF (also in gfx/box.py)
TEXTBOX_REGULAR = 0
TEXTBOX_CONFIRMATION = 1
TEXTBOX_SHUTDOWN = 2

# FB enemy_uniques — consecutive from 0. UniqueCheck order lives in xml_load.
u_null = 0
u_cell = 1
u_chest = 2
u_bluechest = 3
u_bluechestitem = 4
u_button = 5
u_gbutton = 6
u_bshape = 7
u_gshape = 8
u_bush = 9
u_tguard = 10
u_bguard = 11
u_eguard = 12
u_cguard = 13
u_torch = 14
u_ltorch = 15
u_gtorch = 16
u_ibug = 17
u_fbug = 18
u_gold = 19
u_silver = 20
u_health = 21
u_keydoor = 22
u_fkeydoor = 23
u_bardoor = 24
u_static = 25
u_statue = 26
u_pushrock = 27
u_menu = 28
u_savepoint = 29
u_crate = 30
u_crate_health = 31
u_grult = 32
u_ghut = 33
u_hotrock = 34
u_coldrock = 35
u_greyrock = 36
u_bombrock = 37
u_mole = 38
u_sign = 39
u_dyssius = 40
u_anger = 41
u_angerfireball = 42
u_charger = 43
u_sparkle = 44
u_sterach = 45
u_swordie = 46
u_slimeman = 47
u_beetle = 48
u_beamcrystal = 49
u_antiwall = 50
u_antiwall2 = 51
u_pmouth = 52
u_boss5_right = 53
u_boss5_left = 54
u_boss5_down = 55
u_boss5_crystal = 56
u_pekkle_blue = 57
u_pekkle_bomb = 58
u_pekkle_red = 59
u_pekkle_grey = 60
u_pekkle_big = 61
u_goldblock = 62
u_divine = 63
u_divine_bug = 64
u_divine_ball = 65
u_kambot = 66
u_auto = 67
u_mech = 68
u_haywire = 69
u_healthguy = 70
u_godstat = 71
u_steelstrider = 72
u_ferus = 73
u_core = 74
u_biglarva = 75
u_battleseed = 76
u_lynn = 77

# ll_sound_fx is the complete table in audio.py; ll_menu_gfx is in gfx/menu.py.
