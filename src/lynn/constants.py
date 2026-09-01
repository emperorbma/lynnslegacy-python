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

# FB enemy_uniques — values used by UniqueCheck / cripple / save blit.
u_null = 0
u_chest = 2
u_bluechest = 3
u_bluechestitem = 4
u_button = 5
u_gbutton = 6
u_bush = 9
u_menu = 28
u_savepoint = 29
u_crate = 30
u_crate_health = 31
u_ghut = 33
u_hotrock = 34
u_coldrock = 35
u_greyrock = 36
u_lynn = 77
