from lynn.main import main, parse_cli
from lynn.paths import DEFAULT_MAP


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
    assert parse_cli(["--save", "1"]) == ("objects", None, [], "1")
    assert parse_cli(["objects", "--save", "1"]) == ("objects", None, [], "1")
    assert parse_cli(["objects", "inhouse", "--save", "1"]) == (
        "objects",
        "inhouse",
        [],
        "1",
    )
    assert DEFAULT_MAP == "forest_fall.map"
