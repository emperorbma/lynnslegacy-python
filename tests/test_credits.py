"""Ending credits: FreeBASIC roll, LÖVE lines, Python lines, __set_finish."""

import lynn.object  # noqa: F401 — registers sequence funcs
from lynn import clock
import lynn.audio as audio
from lynn.audio import sound_rayflap2
from lynn.credits import (
    PHASE_DONE,
    PHASE_END_KEY,
    CreditRoll,
    align_text,
    credits_lines,
    scroll_rows,
    text_center,
)
from lynn.events import bind_hero, bind_hero_only, reset_events
import lynn.events as events
from lynn.gfx.image import LLSystem_ImageLoad
from lynn.hero import MainCharType
from lynn.object.char import CharType
from lynn.object.dispatch import lookup_func
from lynn.object.seq_funcs import __end, __set_finish
from lynn.object.xml_load import LLSystem_ObjectFromXML

_LOVE = (
    "Ported to Love2D by Derek Andrews",
    "so that this gem may continue to",
    "be enjoyed for years to come.",
)
_PYTHON = (
    "Ported to Python by Grok and",
    "Brian Angeletti (emperorbma)",
)
_THANKS = "And, thank you for playing!"


def test_credit_lines_keep_fb_text_and_add_ports():
    lines = credits_lines()
    directed = "Directed by Josiah Tobin and cha0s"
    assert len(directed) == 34
    assert lines[0] == (" " * 3) + directed
    assert "" in lines
    assert all(not line.startswith(" " * 20) for line in lines)
    joined = "\n".join(lines)
    assert "All art by Josiah Tobin" in joined
    assert "ALL art" not in joined
    assert "Keith, marzec" in joined
    assert "Kith" not in joined
    assert "v1ctor, and everyone who contributes" in joined
    assert "Lynn 'Kona' Dempsey as:" in joined
    assert "Deleter, Kiwi Dan" in joined
    love = lines.index(align_text(_LOVE[0]))
    assert lines[love + 1] == align_text(_LOVE[1])
    assert lines[love + 2] == align_text(_LOVE[2])
    assert lines[love + 3] == ""
    assert lines[love + 4] == align_text(_PYTHON[0])
    assert lines[love + 5] == align_text(_PYTHON[1])
    thanks = lines.index(align_text(_THANKS))
    assert love < thanks
    assert lines[thanks - 1] == ""
    assert text_center("The End.") == 160 - (8 * 4)
    rows = scroll_rows(lines)
    final_y = 200 - rows * 16 - 1
    assert final_y + (len(lines) - 1) * 16 < 0
    assert final_y + thanks * 16 < 0


def test_set_finish_ends_play_without_quitting_the_title():
    reset_events()
    events.xxyxx = 0
    events.request_quit = 0
    assert __set_finish(CharType()) == 1
    assert events.xxyxx == -1
    assert events.request_quit == 0
    assert lookup_func("__set_finish") is __set_finish
    lynn = CharType()
    lynn.id = "data/object/lynn.xml"
    LLSystem_ObjectFromXML(lynn, load_images=False)
    wired = False
    for block in lynn.funcs.func:
        for fn in block:
            if getattr(fn, "__name__", "") == "__set_finish":
                wired = True
    assert wired
    events.xxyxx = 0
    __end(CharType())
    assert events.xxyxx == 0
    assert events.request_quit != 0
    reset_events()
    assert events.xxyxx == 0


def test_credit_roll_clears_the_thank_you_and_plays_holy():
    reset_events()
    try:
        only = MainCharType()
        hero = CharType()
        bind_hero_only(only)
        bind_hero(hero)
        moth = LLSystem_ImageLoad("data/pictures/char/moth_wings.spr")
        title = LLSystem_ImageLoad("data/pictures/char/title.spr")
        assert moth.frames >= 4
        assert title.frames >= 1
        lines = credits_lines()
        roll = CreditRoll(hero, lines, moth_frames=moth.frames)
        audio.last_song = ""
        audio.last_play = None
        now = 1000.0
        songs: list[str] = []
        plays: list[tuple[int, int]] = []
        for _ in range(8000):
            if roll.phase == PHASE_DONE:
                break
            now += 0.08
            roll.step(now, key_down=roll.phase == PHASE_END_KEY)
            if audio.last_song:
                songs.append(audio.last_song)
            if audio.last_play is not None:
                plays.append(audio.last_play)
        else:
            raise AssertionError(f"stuck in {roll.phase} y={roll.credit_y}")
        assert roll.phase == PHASE_DONE
        assert any(song.replace("\\", "/").endswith("data/music/holy.it") for song in songs)
        thanks = lines.index(align_text(_THANKS))
        assert roll.scroll_end_y + thanks * 16 < 0
        assert roll.scroll_end_y == 200 - scroll_rows(lines) * 16 - 1
        assert (sound_rayflap2, 80) in plays
        assert roll.end_shown == len("The End.")
    finally:
        reset_events()
        clock.timer = 0
