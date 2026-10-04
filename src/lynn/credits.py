"""FB engine--LL.bas CreditScroll / LL_RollCredits.

The LÖVE port's three lines sit where that version inserted them, after the
testers. The Python lines follow that block. FreeBASIC wording is unchanged
(Love2D's "ALL art" / "Kith" typos are not copied).
"""

from __future__ import annotations

import time

import pygame

import lynn.events as events
from lynn import clock
from lynn.audio import (
    LLMusic_Fade,
    LLMusic_Start,
    SongFadingType,
    play_sample,
    sound_rayflap2,
)
from lynn.constants import SCREEN_H, SCREEN_W
from lynn.gfx.image import LLSystem_ImageLoad, frame_surfaces
from lynn.gfx.menu import MainMenu, _crop_glyph, graphicalString
from lynn.gfx.palette import LLPalette, load_pal
from lynn.object.char import CharType
from lynn.object.seq_funcs import __color_on as color_on
from lynn.object.seq_funcs import __fade_to_black as fade_to_black
from lynn.object.seq_funcs import __fade_up_to_color as fade_up_to_color

HOLY = "data/music/holy.it"
SONG_PULSE = 5 / 64
SCROLL_DT = 0.08
FLAP_DT = 0.1
TYPE_DT = 0.3
# FB fixed the stop at 90 rows. Pad past the last line so added credits clear y=0.
SCROLL_PAD = 13
TITLE_XY = (160 - 128, 100 - 32)
MOTH_XY = (160 - 48, 100 - 32)
THE_END = "The End."
END_Y = 168

PHASE_CARD = "card"
PHASE_FADE_OUT = "fade_out"
PHASE_SCROLL = "scroll"
PHASE_TITLE_IN = "title_in"
PHASE_TITLE_SONG = "title_song"
PHASE_TITLE_OUT = "title_out"
PHASE_MOTH_IN = "moth_in"
PHASE_MOTH_HOLD = "moth_hold"
PHASE_MOTH_FLAP = "moth_flap"
PHASE_MOTH_STILL = "moth_still"
PHASE_END_TYPE = "end_type"
PHASE_END_HOLD = "end_hold"
PHASE_END_KEY = "end_key"
PHASE_END_FADE = "end_fade"
PHASE_DONE = "done"

# Gap after the testers, then the port credits, then the original thank-you run.
_LOVE_LINES = (
    "Ported to Love2D by Derek Andrews",
    "so that this gem may continue to",
    "be enjoyed for years to come.",
)
_PYTHON_LINES = (
    "Ported to Python by Grok and",
    "Brian Angeletti (emperorbma)",
)

_BEFORE_PORTS = (
    "Directed by Josiah Tobin and cha0s",
    "",
    "All art by Josiah Tobin (some parallax",
    "backgrounds edited from stock art)",
    "",
    "All programming by cha0s",
    "",
    "Music and sound effects composed by",
    "Josiah Tobin (some stock effects used",
    "in the creation of certain sounds)",
    "",
    "Additional sounds by cha0s",
    "",
    "Dialog and manuscript by Josiah Tobin",
    "",
    "Additional dialog by cha0s",
    "",
    "Maps by Josiah Tobin",
    "",
    "Cutscenes scripted by cha0s",
    "",
    "All dungeons designed by Josiah Tobin",
    "",
    "Lynn 'Kona' Dempsey as:",
    "the voice of Lynn",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "Josiah Tobin special thanks:",
    "",
    "Amelia 'Tassimmet' Bennett,",
    "Chris Greer, James Kinney,",
    "Lynn Dempsey, Brian Tobin,",
    "Stephen Gazzard, 'The Reset Button',",
    "Anyone else who helped me out ",
    "or inspired me.",
    "",
    "",
    "",
    "cha0s special thanks:",
    "",
    "v1ctor, and everyone who contributes",
    "to the FreeBASIC Compiler...",
    "(http://www.freebasic.net/forum)",
    "Without it, this game would",
    "not have been possible.",
    "",
    "Shouts out to:",
    "",
    "Autumn, Boy, Dana, 'Diny, Doc. D,",
    "Fat Al, Gal, Guido, Harvey, HinD,",
    "Jay, Jaz, Jewish, Katie, Lizzie,",
    "Katty, Kiana, Keith, marzec, Matt,",
    "'niff, rel, Ron, Sara, Shelby,",
    "Stephanie (both!), The O.B.'s",
    "",
    "Anyone else I missed... Love ya.",
    "",
    "",
    "",
    "",
    "",
    "The Testers:",
    "Deleter, Kiwi Dan, Lachie Dazdarian,",
    "Pritchard, Ryan Szrama, syn9,",
    "voodooattack, Virus Scanner",
    "",
    "",
    "",
    "",
    "",
)

_AFTER_PORTS = (
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "And, thank you for playing!",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
)


def align_text(text: str) -> str:
    """FB alignText: center in a 40-column field. Blank lines stay empty."""
    pad = (40 - len(text)) >> 1
    if pad <= 0:
        return text
    return (" " * pad) + text


def text_center(text: str) -> int:
    """FB text_Center: left x so an 8px font is centered on 320."""
    return (SCREEN_W >> 1) - (len(text) << 2)


def credits_lines() -> list[str]:
    raw = (
        _BEFORE_PORTS
        + _LOVE_LINES
        + ("",)
        + _PYTHON_LINES
        + _AFTER_PORTS
    )
    return [align_text(line) if line else "" for line in raw]


def scroll_rows(lines: list[str]) -> int:
    return len(lines) + SCROLL_PAD


def _song_busy() -> bool:
    only = events.hero_only
    return only is not None and only.songFade is not None


def _arm_song_fade() -> None:
    only = events.hero_only
    if only is None:
        return
    only.songFade = SongFadingType(pulseLength=SONG_PULSE)


class CreditRoll:
    """One step per frame. Timings follow LL_RollCredits (0.08s per scroll pixel)."""

    def __init__(self, hero: CharType, lines: list[str] | None = None, moth_frames: int = 1) -> None:
        self.hero = hero
        self.lines = list(lines) if lines is not None else credits_lines()
        self.text = "\n".join(self.lines)
        self.moth_frames = max(0, int(moth_frames))
        self.phase = PHASE_CARD
        self.credit_y = 200
        self.scroll_end_y = 200
        self.moth_i = 0
        self.flap_i = 0
        self.end_shown = 0
        self._next = 0.0
        self._card_armed = False
        self.menu = None
        self.title = None
        self.moth: list = []
        events.fade_black = 0
        events.fade_white = 0
        events.fade_red = 0
        self.hero.fade_timer = 0
        self.hero.fade_count = 0

    @property
    def done(self) -> bool:
        return self.phase == PHASE_DONE

    def step(self, now: float, key_down: bool = False) -> None:
        clock.timer = now
        if self.phase == PHASE_DONE:
            return
        if self.phase == PHASE_END_KEY:
            if key_down:
                self._ready_fade()
                self.phase = PHASE_END_FADE
            return
        if self.phase == PHASE_CARD:
            self._card(now)
        elif self.phase == PHASE_FADE_OUT:
            self._fade_out(now)
        elif self.phase == PHASE_SCROLL:
            self._scroll(now)
        elif self.phase == PHASE_TITLE_IN:
            self._title_in(now)
        elif self.phase == PHASE_TITLE_SONG:
            self._title_song(now)
        elif self.phase == PHASE_TITLE_OUT:
            self._title_out(now)
        elif self.phase == PHASE_MOTH_IN:
            self._moth_in(now)
        elif self.phase == PHASE_MOTH_HOLD:
            self._moth_hold(now)
        elif self.phase == PHASE_MOTH_FLAP:
            self._moth_flap(now)
        elif self.phase == PHASE_MOTH_STILL:
            self._moth_still(now)
        elif self.phase == PHASE_END_TYPE:
            self._end_type(now)
        elif self.phase == PHASE_END_HOLD:
            self._end_hold(now)
        elif self.phase == PHASE_END_FADE:
            self._end_fade(now)

    def draw(self, canvas) -> None:
        canvas.fill((0, 0, 0))
        if self.menu is None:
            self._overlay(canvas)
            return
        if self.phase in (PHASE_CARD, PHASE_FADE_OUT):
            written = "Written by Josiah Tobin,"
            brought = "brought to life by cha0s"
            graphicalString(canvas, self.menu, written, text_center(written), 88)
            graphicalString(canvas, self.menu, brought, text_center(brought), 104)
        elif self.phase == PHASE_SCROLL:
            graphicalString(canvas, self.menu, self.text, 0, self.credit_y)
        elif self.phase in (PHASE_TITLE_IN, PHASE_TITLE_SONG, PHASE_TITLE_OUT):
            if self.title is not None:
                canvas.blit(self.title, TITLE_XY)
        elif self.phase in (
            PHASE_MOTH_IN,
            PHASE_MOTH_HOLD,
            PHASE_MOTH_FLAP,
            PHASE_MOTH_STILL,
            PHASE_END_TYPE,
            PHASE_END_HOLD,
            PHASE_END_KEY,
            PHASE_END_FADE,
        ):
            if self.moth and 0 <= self.moth_i < len(self.moth):
                canvas.blit(self.moth[self.moth_i], MOTH_XY)
            if self.phase in (PHASE_END_TYPE, PHASE_END_HOLD, PHASE_END_KEY, PHASE_END_FADE):
                shown = THE_END[: self.end_shown]
                if shown:
                    graphicalString(canvas, self.menu, shown, text_center(THE_END) + 4, END_Y)
        self._overlay(canvas)

    def _overlay(self, canvas) -> None:
        if not events.fade_black:
            return
        fade = pygame.Surface((SCREEN_W, SCREEN_H))
        fade.fill((0, 0, 0))
        fade.set_alpha(max(0, min(255, int(events.fade_black))))
        canvas.blit(fade, (0, 0))

    def _ready_fade(self) -> None:
        self.hero.fade_timer = 0
        self.hero.fade_count = 0

    def _blackout(self) -> None:
        events.fade_black = 255
        events.fade_white = 0
        self._ready_fade()

    def _card(self, now: float) -> None:
        if not self._card_armed:
            _arm_song_fade()
            self._card_armed = True
        LLMusic_Fade()
        if not _song_busy():
            self._ready_fade()
            self.phase = PHASE_FADE_OUT

    def _fade_out(self, now: float) -> None:
        if fade_to_black(self.hero):
            self._enter_scroll(now)

    def _enter_scroll(self, now: float) -> None:
        events.fade_black = 0
        events.fade_white = 0
        color_on(self.hero)
        LLMusic_Start(HOLY)
        self.credit_y = 199
        self._next = now + SCROLL_DT
        self.phase = PHASE_SCROLL

    def _scroll(self, now: float) -> None:
        limit = 200 - scroll_rows(self.lines) * 16
        moved = 0
        while now >= self._next and moved < 4:
            self.credit_y -= 1
            self._next += SCROLL_DT
            moved += 1
            if self.credit_y < limit:
                self.scroll_end_y = self.credit_y
                self._blackout()
                self.phase = PHASE_TITLE_IN
                return

    def _title_in(self, now: float) -> None:
        if fade_up_to_color(self.hero):
            _arm_song_fade()
            self.phase = PHASE_TITLE_SONG

    def _title_song(self, now: float) -> None:
        LLMusic_Fade()
        if not _song_busy():
            self.hero.fade_time = 0.06
            self._ready_fade()
            self.phase = PHASE_TITLE_OUT

    def _title_out(self, now: float) -> None:
        if fade_to_black(self.hero):
            self._blackout()
            self.moth_i = 0
            self.phase = PHASE_MOTH_IN

    def _moth_in(self, now: float) -> None:
        if fade_up_to_color(self.hero):
            self._next = now + 2
            self.phase = PHASE_MOTH_HOLD

    def _moth_hold(self, now: float) -> None:
        if now >= self._next:
            self.flap_i = 0
            self._next = now + FLAP_DT
            self.phase = PHASE_MOTH_FLAP

    def _moth_flap(self, now: float) -> None:
        if self.moth_frames <= 0:
            self._next = now + 2
            self.phase = PHASE_MOTH_STILL
            return
        if now < self._next:
            return
        self.moth_i = self.flap_i
        if self.flap_i == 3:
            play_sample(sound_rayflap2, 80)
        self.flap_i += 1
        self._next += FLAP_DT
        if self.flap_i >= self.moth_frames:
            self.moth_i = self.moth_frames - 1
            self._next = now + 2
            self.phase = PHASE_MOTH_STILL

    def _moth_still(self, now: float) -> None:
        if now >= self._next:
            self.end_shown = 0
            self._next = now + TYPE_DT
            self.phase = PHASE_END_TYPE

    def _end_type(self, now: float) -> None:
        if now < self._next:
            return
        self.end_shown += 1
        if self.end_shown >= len(THE_END):
            self.end_shown = len(THE_END)
            self._next = now + 3
            self.phase = PHASE_END_HOLD
            return
        self._next += TYPE_DT

    def _end_hold(self, now: float) -> None:
        if now >= self._next:
            # FB `Sleep` with no argument waits for a key, then fades out.
            self.phase = PHASE_END_KEY

    def _end_fade(self, now: float) -> None:
        if fade_to_black(self.hero):
            self.phase = PHASE_DONE


def _font_menu(palette: LLPalette) -> MainMenu:
    menu = MainMenu()
    header = LLSystem_ImageLoad("data/pictures/llfont.spr")
    menu.font = [_crop_glyph(surf) for surf in frame_surfaces(header, palette)]
    return menu


def _frames(path: str, palette: LLPalette) -> list:
    header = LLSystem_ImageLoad(path)
    if header.frames <= 0:
        return []
    return frame_surfaces(header, palette)


def roll_credits(canvas, present, frame_clock, palette: LLPalette | None, hero: CharType | None = None) -> None:
    """FB LL_RollCredits. Returns immediately unless __set_finish set xxyxx."""
    if events.xxyxx == 0:
        return
    if hero is None:
        hero = events.hero if events.hero is not None else CharType()
    if palette is None:
        palette = load_pal("data/palette/ll.pal")
    moth = _frames("data/pictures/char/moth_wings.spr", palette)
    title_frames = _frames("data/pictures/char/title.spr", palette)
    roll = CreditRoll(hero, moth_frames=len(moth) if moth else 1)
    roll.menu = _font_menu(palette)
    roll.title = title_frames[0] if title_frames else None
    roll.moth = moth
    pygame.display.set_caption("Lynn's Legacy")
    while not roll.done:
        now = time.perf_counter()
        key_down = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                return
            if event.key == pygame.K_F11 or (
                event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
            ):
                pygame.display.toggle_fullscreen()
                continue
            key_down = True
        roll.step(now, key_down=key_down and roll.phase == PHASE_END_KEY)
        roll.draw(canvas)
        present()
        frame_clock.tick(60)
