"""FB ll/audio.bas init_snd / play_sample, plus LLMusic_* via pygame.mixer.music."""

from __future__ import annotations

import os
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
last_song: str = ""
music_volume: int = 100

# FB headers/utility.bi music_strings(25). Index is room.song / this.chap.
MUSIC_STRINGS: tuple[str, ...] = (
    "",
    "data/music/amb.it",
    "data/music/apox.it",
    "data/music/beneath.it",
    "data/music/boss.it",
    "data/music/boss2.it",
    "data/music/core.it",
    "data/music/cryspool.it",
    "data/music/dimension2.it",
    "data/music/dimhole.it",
    "data/music/dream.it",
    "data/music/evernight.it",
    "data/music/final.it",
    "data/music/forest.it",
    "data/music/fsun.it",
    "data/music/holy.it",
    "data/music/limbo.it",
    "data/music/logosta.it",
    "data/music/master.it",
    "data/music/sdesert.it",
    "data/music/title.it",
    "data/music/town.it",
    "data/music/valley.it",
    "data/music/world.it",
    "data/music/after.it",
    "data/music/faulty.it",
)


class SongFadingType:
    """FB lynn_structures.bi songFading_type."""

    def __init__(self, pulse: float = 0.0, pulseLength: float = 0.0, travelled: int = 0) -> None:
        self.pulse = pulse
        self.pulseLength = pulseLength
        self.travelled = travelled


def sound_from_name(text: str) -> int:
    return SOUND_NAMES.get(text.strip().lower(), sound_null)


def audio_output_enabled() -> bool:
    """False under the dummy driver (pytest). Live output is the game or `lynn audio`."""
    driver = os.environ.get("SDL_AUDIODRIVER", "").lower()
    if driver in ("dummy", "disk", "none"):
        return False
    try:
        import pygame

        return pygame.mixer.get_init() is not None
    except Exception:
        return False


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
    if not audio_output_enabled():
        return 1
    try:
        sample = snd[s]
        sample.set_volume(max(0.0, min(1.0, v / 100.0)))
        sample.play()
    except Exception:
        return 0
    return 1


def sounds_dir() -> Path:
    return project_root() / "data" / "sounds"


def music_path(index: int) -> str:
    if 0 <= int(index) < len(MUSIC_STRINGS):
        return MUSIC_STRINGS[int(index)]
    return ""


def LLMusic_SetVolume(volumeDesired: int) -> None:
    """FB BASS_CONFIG_GVOL_MUSIC, 0–100."""
    global music_volume
    music_volume = max(0, min(100, int(volumeDesired)))
    try:
        import pygame

        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.set_volume(music_volume / 100.0)
    except Exception:
        pass


def LLMusic_Stop() -> None:
    """FB bass_channelstop(llg(sng))."""
    global last_song
    last_song = ""
    try:
        import pygame

        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
    except Exception:
        pass


def LLMusic_Start(songName: str) -> None:
    """FB BASS_MusicLoad + BASS_ChannelPlay, looped. pygame.mixer.music plays .it."""
    global last_song
    name = (songName or "").replace("\\", "/")
    last_song = name
    if not name:
        LLMusic_Stop()
        last_song = ""
        return
    path = Path(name)
    if not path.is_file():
        path = project_root() / name
    if not path.is_file():
        return
    if not audio_output_enabled():
        return
    try:
        import pygame

        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(music_volume / 100.0)
        pygame.mixer.music.play(-1)
    except Exception:
        pass


def LLMusic_StartIndex(index: int) -> None:
    import lynn.events as events

    events.song = int(index)
    LLMusic_Start(music_path(index))


def LLMusic_Fade() -> None:
    """FB LLMusic_Fade: 64 slices from 100 to 0, then stop and restore volume."""
    from lynn import clock
    import lynn.events as events

    only = events.hero_only
    if only is None or only.songFade is None:
        return
    fade = only.songFade
    slices = 64
    if clock.timer > fade.pulse:
        tmp_val = (slices - fade.travelled) * 1.5625
        LLMusic_SetVolume(int(tmp_val))
        fade.travelled += 1
        fade.pulse = clock.timer + fade.pulseLength
    if fade.travelled == slices:
        LLMusic_Stop()
        LLMusic_SetVolume(100)
        only.songFade = None


def tick_music() -> None:
    import lynn.events as events

    only = events.hero_only
    if only is not None and only.songFade is not None:
        LLMusic_Fade()


def start_room_song(song: int, force: int = 0) -> None:
    """FB ll_main_entry / change_room: play room.song if it changed."""
    import lynn.events as events

    song = int(song)
    if force == 0 and song == events.song:
        return
    LLMusic_StartIndex(song)
