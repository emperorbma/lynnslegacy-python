from lynn.main import _caption_for, main, parse_cli, resolve_boot_map
from lynn.paths import DEFAULT_MAP, START_MAP


def test_help_exits_zero():
    assert main(["help"]) == 0
    assert main(["--help"]) == 0


def test_unknown_mode_exits_two():
    assert main(["not-a-mode"]) == 2


def test_parse_cli_map_default_and_override():
    assert parse_cli([]) == ("objects", None, [], None)
    assert parse_cli(["map"]) == ("map", None, [], None)
    assert parse_cli(["map", "valley"]) == ("map", "valley", [], None)
    assert parse_cli(["objects", "data/map/inhouse.map"]) == (
        "objects",
        "data/map/inhouse.map",
        [],
        None,
    )
    assert parse_cli(["test", "--map", "valley.map"]) == (
        "test",
        None,
        ["--map", "valley.map"],
        None,
    )
    assert parse_cli(["audio"]) == ("audio", None, [], None)
    assert parse_cli(["--save", "1"]) == ("objects", None, [], "1")
    assert parse_cli(["objects", "--save", "1"]) == ("objects", None, [], "1")
    assert parse_cli(["objects", "inhouse", "--save", "1"]) == (
        "objects",
        "inhouse",
        [],
        "1",
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


def test_resolve_boot_map_save_skips_splash():
    class _Save:
        map = "limbo3.map"

    assert resolve_boot_map("objects", None, _Save()) == ("limbo3.map", False)
    assert resolve_boot_map("objects", "inhouse", _Save()) == ("inhouse", False)
