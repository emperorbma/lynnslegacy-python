"""FB ll/audio.bas init_snd / play_sample. OGG SFX only; .it music is later."""

from __future__ import annotations

from pathlib import Path

from lynn.paths import project_root

sound_null = 0
sound_bassdrop = 1
sound_beam = 2
sound_bigchest = 3
sound_boss_hit = 4
sound_cashget = 5
sound_doorfkey = 6
sound_doorsmall = 7
sound_enemyhit = 8
sound_enemykill = 9
sound_explosion = 10
sound_flare = 11
sound_healthgrab = 12
sound_heart = 13
sound_ice = 14
sound_portal = 15
sound_smallchest = 16
sound_switch = 17
sound_treepull = 18
sound_lowhealth = 19
sound_bush = 20
sound_crateting = 21
sound_sea = 22
sound_lynn_attack_1 = 23
sound_lynn_attack_2 = 24
sound_lynn_attack_3 = 25
sound_lynn_attack_4 = 26
sound_lynn_hurt_1 = 27
sound_lynn_hurt_2 = 28
sound_lynn_hurt_3 = 29
sound_lynn_die = 30
sound_mace_0 = 31
sound_mace_1 = 32
sound_mace_2 = 33
sound_texttemp = 34
sound_torchlight = 35
sound_greystatic = 36
sound_crickets = 37
sound_gulls2 = 38
sound_rayflap2 = 39
sound_flap = 40
sound_sploosh = 41
sound_camera = 42
sound_ferusstep = 43
sound_ferusbeep = 44
sound_ferusgarbled = 45
sound_beamcharge = 46
sound_corealarm = 47
sound_corealarm2 = 48
sound_rumble = 49
sound_coreclunk = 50
sound_gunfire = 51
sound_limboloop = 52
sound_podopen = 53
sound_turret = 54
sound_heal = 55
sound_build = 56
sound_mothdie = 57
NUM_OF_SOUNDS = 58

# (enum, filename, loop). Loop is stored; ambients are not auto-started.
_SAMPLE_FILES: tuple[tuple[int, str, bool], ...] = (
    (sound_bassdrop, "bassdrop.ogg", False),
    (sound_beam, "beam.ogg", False),
    (sound_bigchest, "bigchest.ogg", False),
    (sound_boss_hit, "boss_hit.ogg", False),
    (sound_cashget, "cashget.ogg", False),
    (sound_doorfkey, "doorfkey.ogg", False),
    (sound_doorsmall, "doorsmall.ogg", False),
    (sound_enemyhit, "enemyhit.ogg", False),
    (sound_enemykill, "enemykill.ogg", False),
    (sound_explosion, "explosion.ogg", False),
    (sound_flare, "flare.ogg", False),
    (sound_healthgrab, "healthgrab.ogg", False),
    (sound_heart, "heart.ogg", False),
    (sound_ice, "ice.ogg", False),
    (sound_portal, "portal.ogg", False),
    (sound_smallchest, "smallchest.ogg", False),
    (sound_switch, "switch.ogg", False),
    (sound_treepull, "treepull.ogg", False),
    (sound_lowhealth, "lowhealth.ogg", False),
    (sound_bush, "bush.ogg", False),
    (sound_crateting, "crateting.ogg", False),
    (sound_sea, "sea.ogg", True),
    (sound_lynn_attack_1, "lynn_attack_1.ogg", False),
    (sound_lynn_attack_2, "lynn_attack_2.ogg", False),
    (sound_lynn_attack_3, "lynn_attack_3.ogg", False),
    (sound_lynn_attack_4, "lynn_attack_4.ogg", False),
    (sound_lynn_hurt_1, "lynn_hurt_1.ogg", False),
    (sound_lynn_hurt_2, "lynn_hurt_2.ogg", False),
    (sound_lynn_hurt_3, "lynn_hurt_3.ogg", False),
    (sound_lynn_die, "lynn_die3.ogg", False),
    (sound_mace_0, "mace0.ogg", False),
    (sound_mace_1, "mace1.ogg", False),
    (sound_mace_2, "mace2.ogg", False),
    (sound_texttemp, "texttemp.ogg", False),
    (sound_torchlight, "torchlight.ogg", False),
    (sound_greystatic, "greystatic.ogg", True),
    (sound_crickets, "crickets.ogg", True),
    (sound_gulls2, "gulls2.ogg", False),
    (sound_rayflap2, "rayflap2.ogg", False),
    (sound_flap, "flap.ogg", False),
    (sound_sploosh, "sploosh.ogg", False),
    (sound_camera, "ferus_camera.ogg", False),
    (sound_ferusstep, "ferus_step.ogg", False),
    (sound_ferusbeep, "ferus_beepsound.ogg", False),
    (sound_ferusgarbled, "garbled.ogg", False),
    (sound_beamcharge, "beam_charge.ogg", True),
    (sound_corealarm, "alarm_loop.ogg", True),
    (sound_corealarm2, "single_alarm.ogg", False),
    (sound_rumble, "rumble.ogg", True),
    (sound_coreclunk, "coreclunk.ogg", False),
    (sound_gunfire, "gunfire.ogg", False),
    (sound_limboloop, "limboloop.ogg", True),
    (sound_podopen, "pod_open.ogg", False),
    (sound_turret, "turret.ogg", False),
    (sound_heal, "heal.ogg", False),
    (sound_build, "build.ogg", False),
    (sound_mothdie, "mothdie.ogg", False),
)

SOUND_NAMES: dict[str, int] = {
    name: val
    for name, val in globals().items()
    if name.startswith("sound_") and isinstance(val, int)
}

snd: list = [None] * NUM_OF_SOUNDS
last_play: tuple[int, int] | None = None


def sound_from_name(text: str) -> int:
    return SOUND_NAMES.get(text.strip().lower(), sound_null)


def init_mixer() -> bool:
    """pygame.mixer.init. Safe when there is no audio device."""
    try:
        import pygame

        if pygame.mixer.get_init() is None:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init(44100, -16, 2, 512)
        pygame.mixer.set_num_channels(32)
        return pygame.mixer.get_init() is not None
    except Exception:
        return False


def init_snd() -> None:
    """FB init_snd: load data/sounds/*.ogg into llg(snd)."""
    global snd
    snd = [None] * NUM_OF_SOUNDS
    try:
        import pygame
    except ImportError:
        return
    if pygame.mixer.get_init() is None:
        return
    folder = project_root() / "data" / "sounds"
    for idx, filename, _loop in _SAMPLE_FILES:
        path = folder / filename
        if not path.is_file():
            continue
        try:
            snd[idx] = pygame.mixer.Sound(str(path))
        except Exception:
            continue
    _apply_vol_tweaks()


def _apply_vol_tweaks() -> None:
    """FB lazy_macro default volumes (0-100 → 0-1)."""

    def _set(idx: int, vol: int) -> None:
        sample = snd[idx] if 0 <= idx < len(snd) else None
        if sample is not None:
            sample.set_volume(vol / 100.0)

    for idx in (sound_lynn_attack_1, sound_lynn_attack_2, sound_lynn_attack_3, sound_lynn_attack_4):
        _set(idx, 45)
    for idx in (sound_mace_0, sound_mace_1, sound_mace_2):
        _set(idx, 75)
    for idx in (sound_lynn_hurt_1, sound_lynn_hurt_2, sound_lynn_hurt_3):
        _set(idx, 75)
    _set(sound_rayflap2, 75)
    _set(sound_flare, 35)
    _set(sound_ice, 35)
    _set(sound_explosion, 45)
    _set(sound_sea, 75)
    _set(sound_texttemp, 45)
    _set(sound_crickets, 45)
    _set(sound_gulls2, 55)


def play_sample(s: int, v: int = 0) -> int:
    """FB play_sample: llg(snd)[s], volume 0-100 (0 means 100)."""
    global last_play
    if v == 0:
        v = 100
    last_play = (int(s), int(v))
    if not s:
        return 0
    if s < 0 or s >= len(snd) or snd[s] is None:
        return 0
    try:
        sample = snd[s]
        sample.set_volume(max(0.0, min(1.0, v / 100.0)))
        sample.play()
    except Exception:
        return 0
    return 1


def sounds_dir() -> Path:
    return project_root() / "data" / "sounds"
