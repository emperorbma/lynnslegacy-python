from lynn.main import (
    _caption_for,
    _play_caption,
    _set_window_icon,
    apply_debug_god,
    main,
    parse_cli,
    resolve_boot_map,
)
from lynn.paths import DEFAULT_MAP, START_MAP, data_file


def test_help_exits_zero():
    assert main(["help"]) == 0
    assert main(["--help"]) == 0


def test_unknown_mode_exits_two():
    assert main(["not-a-mode"]) == 2


def test_parse_cli_map_default_and_override():
    assert parse_cli([]) == ("objects", None, [], None, False)
    assert parse_cli(["map"]) == ("map", None, [], None, False)
    assert parse_cli(["map", "valley"]) == ("map", "valley", [], None, False)
    assert parse_cli(["objects", "data/map/inhouse.map"]) == (
        "objects",
        "data/map/inhouse.map",
        [],
        None,
        False,
    )
    assert parse_cli(["test", "--map", "valley.map"]) == (
        "test",
        None,
        ["--map", "valley.map"],
        None,
        False,
    )
    assert parse_cli(["audio"]) == ("audio", None, [], None, False)
    assert parse_cli(["config"]) == ("config", None, [], None, False)
    assert parse_cli(["credits"]) == ("credits", None, [], None, False)
    assert parse_cli(["--save", "1"]) == ("objects", None, [], "1", False)
    assert parse_cli(["objects", "--save", "1"]) == ("objects", None, [], "1", False)
    assert parse_cli(["objects", "inhouse", "--save", "1"]) == (
        "objects",
        "inhouse",
        [],
        "1",
        False,
    )
    assert parse_cli(["--godmode"]) == ("objects", None, [], None, True)
    assert parse_cli(["objects", "gelidus", "--godmode"]) == (
        "objects",
        "gelidus",
        [],
        None,
        True,
    )
    assert parse_cli(["objects", "--godmode", "--save", "4"]) == (
        "objects",
        None,
        [],
        "4",
        True,
    )
    assert DEFAULT_MAP == "forest_fall.map"
    assert START_MAP == "title.map"


def test_resolve_boot_map_default_is_splash_and_title():
    assert resolve_boot_map("objects", None, None) == (START_MAP, True)
    assert resolve_boot_map("objects", "forest_fall", None) == ("forest_fall", False)
    assert resolve_boot_map("map", None, None) == (DEFAULT_MAP, False)
    assert resolve_boot_map("palette", None, None) == (DEFAULT_MAP, False)


def test_default_objects_caption_is_plain():
    assert _caption_for("objects", None) == "Lynn's Legacy"
    assert _caption_for("objects", START_MAP, quiet=True) == "Lynn's Legacy"
    assert _caption_for("objects", "forest_fall") == "Lynn's Legacy - forest_fall"
    assert "forest_fall" in _caption_for("map", None)


def test_window_icon_is_the_fb_ll_ico():
    path = data_file("pictures", "ll.ico")
    assert path.is_file()
    assert path.stat().st_size == 2238
    import pygame

    pygame.display.set_mode((32, 32))
    surf = pygame.image.load(str(path))
    assert surf.get_width() >= 16
    assert surf.get_height() >= 16
    _set_window_icon()


def test_debug_god_sets_and_clears_only_its_own_invincible():
    import lynn.events as events
    from lynn.events import reset_events

    reset_events()

    class Hero:
        invincible = 1

    hero = Hero()
    apply_debug_god(hero)
    assert hero.invincible == 1
    events.debug_god = -1
    apply_debug_god(hero)
    assert hero.invincible == -1
    assert _play_caption() == "Lynn's Legacy [godmode]"
    events.debug_god = 0
    apply_debug_god(hero)
    assert hero.invincible == 0
    hero.invincible = 1
    apply_debug_god(hero)
    assert hero.invincible == 1
    assert _play_caption() == "Lynn's Legacy"
    reset_events()


def test_resolve_boot_map_save_skips_splash():
    class _Save:
        map = "limbo3.map"

    assert resolve_boot_map("objects", None, _Save()) == ("limbo3.map", False)
    assert resolve_boot_map("objects", "inhouse", _Save()) == ("inhouse", False)
