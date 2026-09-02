from lynn.gfx.box import parse_text, wrap_lines, _center_line, make_box, tick_box, BoxControl, TEXTBOX_CONFIRMATION
from lynn import clock
from lynn.constants import TRUE


def test_parse_newline_is_case_insensitive():
    assert "{NEWLINE}" in parse_text("Hello {newLine} world")
    assert "{NEWLINE}" in parse_text("Hello {NEWLINE} world")
    out = parse_text("A {NEWLINE} B")
    assert "{" not in out.replace("{NEWLINE}", "")
    assert "A " in out and " B" in out


def test_sign_directions_wrap_on_newline():
    text = (
        "South - New Sarrael City {NEWLINE} North - Sarrael Woods "
        "{NEWLINE} East - Sarrael Drylands {NEWLINE} West - TempleWood"
    )
    lines = wrap_lines(text)
    assert len(lines) == 4
    assert "South - New Sarrael City" in lines[0]
    assert "North - Sarrael Woods" in lines[1]
    assert "East - Sarrael Drylands" in lines[2]
    assert "West - TempleWood" in lines[3]
    for line in lines:
        assert "{NEWLINE}" not in line
        assert len(line) < 36


def test_word_wrap_at_36():
    text = "This is a fairly long sentence that should wrap onto a second line of the box."
    lines = wrap_lines(text)
    assert len(lines) >= 2
    for line in lines:
        assert len(line) < 36


def test_center_line_pads_left():
    line = "Welcome to New Sarrael City!"
    centered = _center_line(line)
    assert centered.strip() == line
    assert centered.startswith(" ")
    assert len(centered) < 38


def test_typewriter_plays_texttemp():
    from lynn import audio
    from lynn.audio import sound_texttemp

    box = BoxControl()
    clock.timer = 0.0
    make_box(box, "Hello")
    clock.timer = box.speed + 0.001
    tick_box(box, 0)
    assert audio.last_play == (sound_texttemp, 25)
    first = audio.last_play
    tick_box(box, 0)
    assert audio.last_play == first
    clock.timer = box.timer + box.speed + 0.001
    tick_box(box, 0)
    assert audio.last_play == (sound_texttemp, 25)


def test_space_confirms_short_box():
    box = BoxControl()
    clock.timer = 0.0
    make_box(box, "Eldqud's Lab")
    assert box.activated != 0
    assert len(box.rows) == 1
    assert "{NEWLINE}" not in box.rows[0]
    tick_box(box, TRUE)
    assert box.state == TEXTBOX_CONFIRMATION
    tick_box(box, TRUE)
    assert box.activated == 0
