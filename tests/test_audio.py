import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import lynn.object  # noqa: F401
from lynn.audio import (
    NUM_OF_SOUNDS,
    play_sample,
    sample_loops,
    sound_bush,
    sound_crickets,
    sound_enemyhit,
    sound_enemykill,
    sound_explosion,
    sound_from_name,
    sound_gulls2,
    sound_healthgrab,
    sound_lynn_die,
    sound_lynn_hurt_1,
    sound_mace_0,
    sound_mothdie,
    sound_null,
    sound_sea,
    sound_switch,
)
from lynn.constants import u_lynn
from lynn.events import bind_hero, bind_hero_only, bind_room
from lynn.gfx.loot import blit_enemy_loot
from lynn.hero import ctor_hero, ctor_hero_only
from lynn.object.char import CharType
from lynn.object.combat import LLObject_MAINDamage
from lynn.object.xml_load import LLSystem_ObjectFromXML, spawn_from_stub
from lynn.paths import project_root


def test_audio_output_disabled_under_dummy_driver():
    from lynn.audio import audio_output_enabled

    assert os.environ.get("SDL_AUDIODRIVER", "").lower() == "dummy"
    assert audio_output_enabled() is False


def test_music_strings_title_and_forest():
    from lynn.audio import MUSIC_STRINGS, music_path

    assert MUSIC_STRINGS[20].replace("\\", "/").endswith("title.it")
    assert MUSIC_STRINGS[13].replace("\\", "/").endswith("forest.it")
    assert music_path(20) == MUSIC_STRINGS[20]
    assert music_path(0) == ""
    assert (project_root() / "data/music/title.it").is_file()


def test_llmusic_start_records_last_song():
    from lynn.audio import LLMusic_Start, LLMusic_Stop, last_song

    LLMusic_Start("data/music/title.it")
    from lynn import audio

    assert audio.last_song.replace("\\", "/").endswith("title.it")
    LLMusic_Stop()
    assert audio.last_song == ""


def test_fade_music_out_reaches_stop():
    from lynn import clock
    from lynn.audio import LLMusic_Fade, SongFadingType
    from lynn.events import bind_hero_only, reset_events
    from lynn.hero import ctor_hero_only
    from lynn.object.dispatch import lookup_func

    reset_events()
    only = ctor_hero_only()
    bind_hero_only(only)
    clock.timer = 1.0
    lookup_func("__fade_music_out")(CharType())
    assert only.songFade is not None
    assert only.songFade.pulseLength == pytest.approx(4 / 64)
    for i in range(64):
        clock.timer = 1.0 + (i + 1) * 0.1
        LLMusic_Fade()
    assert only.songFade is None
    from lynn import audio

    assert audio.music_volume == 100


def test_title_room_song_is_title_it():
    from lynn.map.loader import load_mapV
    from lynn.paths import resolve_map_path

    m = load_mapV(str(resolve_map_path("title")), load_tileset=False)
    assert m.room[0].song == 20


def test_play_song_uses_chap_index():
    from lynn.audio import last_song
    from lynn.events import reset_events
    from lynn.object.dispatch import lookup_func

    reset_events()
    obj = CharType()
    obj.chap = 20
    lookup_func("__play_song")(obj)
    from lynn import audio

    assert audio.last_song.replace("\\", "/").endswith("title.it")


def test_sound_enum_and_name_lookup():
    assert sound_null == 0
    assert sound_from_name("sound_mace_0") == sound_mace_0
    assert sound_from_name("sound_bush") == sound_bush
    assert sound_from_name("nope") == sound_null
    assert NUM_OF_SOUNDS == 58
    assert (project_root() / "data/sounds/mace0.ogg").is_file()


def test_play_sample_records_last_play():
    play_sample(sound_mace_0, 50)
    from lynn import audio

    assert audio.last_play == (sound_mace_0, 50)
    play_sample(sound_switch)
    assert audio.last_play == (sound_switch, 100)


def test_crickets_and_explosion_are_loop_and_one_shot():
    assert sample_loops(sound_crickets) is True
    assert sample_loops(sound_explosion) is False
    assert (project_root() / "data/sounds/crickets.ogg").is_file()
    assert (project_root() / "data/sounds/explosion.ogg").is_file()


def test_lynn_and_moth_load_xml_snd_slots():
    lynn = CharType()
    lynn.id = "data/object/lynn.xml"
    LLSystem_ObjectFromXML(lynn, load_images=False)
    assert lynn.sounds >= 1
    assert lynn.sound[0] == sound_crickets

    moth = CharType()
    moth.id = "data/object/moth.xml"
    LLSystem_ObjectFromXML(moth, load_images=False)
    assert moth.sound[0] == sound_mothdie
    assert moth.vol[0] == 70

    gull = CharType()
    gull.id = "data/object/gull.xml"
    LLSystem_ObjectFromXML(gull, load_images=False)
    assert gull.sound[3] == sound_gulls2
    assert gull.vol[3] == 25


def test_play_sound_uses_chap_slot():
    from lynn.object.dispatch import lookup_func

    lynn = CharType()
    lynn.id = "data/object/lynn.xml"
    LLSystem_ObjectFromXML(lynn, load_images=False)
    lynn.chap = 0
    lookup_func("__play_sound")(lynn)
    from lynn import audio

    assert audio.last_play == (sound_crickets, 100)
    assert lynn.playing_handle is not None
    lookup_func("__stop_sound")(lynn)
    assert lynn.playing_handle is None

    moth = CharType()
    moth.id = "data/object/moth.xml"
    LLSystem_ObjectFromXML(moth, load_images=False)
    moth.chap = 0
    lookup_func("__play_sound")(moth)
    assert audio.last_play == (sound_mothdie, 70)


def test_title_begin_play_sound_is_crickets():
    """title.map entry 0 command 11: lynn play_sound chap 0."""
    from lynn.map.loader import load_mapV
    from lynn.object.dispatch import lookup_func
    from lynn.paths import resolve_map_path

    m = load_mapV(str(resolve_map_path("title")), load_tileset=False)
    cmd = m.entry[0].seq[0].Command[11]
    assert cmd.ent[0].active_ent == 0
    assert cmd.ent[0].ent_state == 26
    assert cmd.ent[0].chap == 0
    hero = ctor_hero(load_images=False)
    hero.chap = 0
    lookup_func("__play_sound")(hero)
    from lynn import audio

    assert audio.last_play == (sound_crickets, 100)


def test_explode_lynn_plays_explosion():
    from lynn.events import bind_hero, reset_events
    from lynn.object.dispatch import lookup_func

    reset_events()
    hero = ctor_hero(load_images=False)
    hero.coords_x = 80
    hero.coords_y = 64
    bind_hero(hero)
    boom = CharType()
    boom.id = "data/object/moth_explosion.xml"
    LLSystem_ObjectFromXML(boom, load_images=False)
    assert lookup_func("__explode_lynn") is not lookup_func("__noop")
    lookup_func("__explode_lynn")(boom)
    from lynn import audio

    assert audio.last_play == (sound_explosion, 100)
    assert boom.coords_x == 56
    assert boom.coords_y == 40


def test_vol_fade_stops_sample():
    from lynn import clock
    from lynn.object.dispatch import lookup_func

    lynn = CharType()
    lynn.id = "data/object/lynn.xml"
    LLSystem_ObjectFromXML(lynn, load_images=False)
    lynn.chap = 0
    lookup_func("__play_sound")(lynn)
    lookup_func("__set_vol_fade")(lynn)
    assert lynn.vol_fade_trig != 0
    clock.timer = 1.0
    for i in range(40):
        clock.timer = 1.0 + i * 0.31
        lookup_func("__do_vol_fade")(lynn)
        if lynn.vol_fade_trig == 0:
            break
    assert lynn.vol_fade_trig == 0
    assert lynn.playing_handle is None


def test_title_gull_play_sound_is_sea_then_gulls2():
    from lynn.hero import ctor_hero
    from lynn.map.loader import load_mapV
    from lynn.object.dispatch import lookup_func
    from lynn.object.xml_load import spawn_from_stub
    from lynn.paths import resolve_map_path
    from lynn.sequence import bind_sequence_ents
    from lynn import audio

    m = load_mapV(str(resolve_map_path("title")), load_tileset=False)
    objs = [spawn_from_stub(e, load_images=False) for e in m.room[0].enemy]
    hero = ctor_hero(load_images=False)
    seq = m.entry[0].seq[0]
    bind_sequence_ents(seq, hero, objs)
    c1 = seq.Command[1]
    gull = seq.ent[c1.ent[2].active_ent]
    assert "gull" in gull.id
    gull.chap = c1.ent[2].chap
    lookup_func("__play_sound")(gull)
    assert audio.last_play == (sound_sea, 100)
    c3 = seq.Command[3]
    gull2 = seq.ent[c3.ent[0].active_ent]
    gull2.chap = c3.ent[0].chap
    lookup_func("__play_sound")(gull2)
    assert audio.last_play == (sound_gulls2, 25)
    assert c1.ent[2].jump_count == 0
    assert seq.Command[2].ent[1].jump_count == 100


def test_explode_spawns_particles_and_plays():
    import pygame
    from lynn.object.dispatch import lookup_func
    from lynn.object.xml_load import LLSystem_ObjectFromXML

    pygame.init()
    pygame.display.set_mode((320, 200))
    crate = CharType()
    crate.id = "data/object/raycrate.xml"
    LLSystem_ObjectFromXML(crate, load_images=True)
    crate.coords_x = 104
    crate.coords_y = 112
    assert crate.explosions == 40
    assert crate.expl_anim == 1
    assert lookup_func("__explode") is not lookup_func("__noop")
    lookup_func("__explode")(crate)
    assert crate.cur_expl >= 1
    assert crate.explosion[0].alive != 0
    from lynn import audio

    assert audio.last_play == (sound_explosion, 70)
    pygame.quit()


def test_roamer_defaults_and_bush_sounds():
    roamer = CharType()
    roamer.id = "data/object/roamer.xml"
    LLSystem_ObjectFromXML(roamer, load_images=False)
    assert roamer.hit_sound == sound_enemyhit
    assert roamer.dead_sound == sound_enemykill

    bush = CharType()
    bush.id = "data/object/bush.xml"
    LLSystem_ObjectFromXML(bush, load_images=False)
    assert bush.hit_sound == sound_null
    assert bush.dead_sound == sound_bush


def test_lynn_attack_frame_carries_mace_sound():
    import pygame

    pygame.init()
    pygame.display.set_mode((320, 200))
    hero = ctor_hero(load_images=True)
    assert hero.dead_sound == sound_lynn_die
    assert hero.unique_id == u_lynn
    attack = hero.anim[3]
    assert attack.frame[0].sound == sound_mace_0
    assert attack.frame[0].vol == 50
    assert attack.frame[0].uni_sound == -1
    assert attack.frame[6].sound == sound_mace_0
    pygame.quit()


def test_enemy_hit_and_kill_sounds():
    from lynn.events import reset_events
    from lynn.object.combat import LLObject_ProcessHurt

    reset_events()
    roamer = CharType()
    roamer.id = "data/object/roamer.xml"
    LLSystem_ObjectFromXML(roamer, load_images=False)
    roamer.hurt = 1
    roamer.hp = 2
    LLObject_ProcessHurt(roamer)
    from lynn import audio

    assert audio.last_play == (sound_enemyhit, 100)
    roamer.hurt = 1
    LLObject_ProcessHurt(roamer)
    assert audio.last_play == (sound_enemykill, 100)


def test_contact_plays_hurt_voice():
    import pygame

    from lynn import audio

    pygame.init()
    pygame.display.set_mode((320, 200))
    hero = ctor_hero(load_images=True)
    only = ctor_hero_only()
    bind_hero_only(only)
    bind_hero(hero)
    from types import SimpleNamespace

    roamer = spawn_from_stub(
        SimpleNamespace(id="data/object/roamer.xml", x_origin=hero.coords_x, y_origin=hero.coords_y, direction=0),
        load_images=True,
    )
    bind_room(None, [roamer])
    LLObject_MAINDamage(hero, [roamer])
    assert audio.last_play is not None
    assert sound_lynn_hurt_1 <= audio.last_play[0] <= sound_lynn_hurt_1 + 2
    assert audio.last_play[1] == 50
    pygame.quit()


def test_loot_pickup_plays_healthgrab():
    from lynn import audio

    hero = ctor_hero(load_images=False)
    hero.hp = 5
    hero.maxhp = 6
    hero.coords_x = 10
    hero.coords_y = 10
    hero.perimeter_x = 16
    hero.perimeter_y = 16
    heart = CharType()
    heart.dropped = 1
    heart.drop_x = 12
    heart.drop_y = 12
    blit_enemy_loot(None, [heart], hero, 0, 0, [object(), object(), object()])
    assert audio.last_play == (sound_healthgrab, 100)


def test_save_write_plays_switch(tmp_path, monkeypatch):
    from lynn import audio
    from lynn.events import reset_events
    from lynn.object.dispatch import lookup_func
    from lynn.constants import TRUE
    import lynn.events as events

    reset_events()
    hero = ctor_hero(load_images=False)
    only = ctor_hero_only()
    bind_hero(hero)
    bind_hero_only(only)
    events.map_filename = "forest_fall.map"
    events.keys.enter_pulse = TRUE
    monkeypatch.setattr("lynn.object.save.project_root", lambda: tmp_path)
    sp = CharType()
    sp.id = "data/object/savepoint.xml"
    LLSystem_ObjectFromXML(sp, load_images=False)
    lookup_func("__do_menu_save")(sp)
    assert audio.last_play == (sound_switch, 100)
    sav = tmp_path / "ll_save1.sav"
    if sav.is_file():
        sav.unlink()
