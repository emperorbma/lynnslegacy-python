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

# FB enemy_uniques — values used by UniqueCheck / cripple / save blit.
u_null = 0
u_chest = 2
u_bluechest = 3
u_bluechestitem = 4
u_button = 5
u_gbutton = 6
u_bush = 9
u_torch = 14
u_ltorch = 15
u_gtorch = 16
u_gold = 19
u_silver = 20
u_health = 21
u_keydoor = 22
u_fkeydoor = 23
u_bardoor = 24
u_static = 25
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
u_mole = 38
u_healthguy = 70
u_lynn = 77
