from lynn.main import main, parse_cli
from lynn.paths import DEFAULT_MAP


def test_help_exits_zero():
    assert main(["help"]) == 0
    assert main(["--help"]) == 0


def test_unknown_mode_exits_two():
    assert main(["not-a-mode"]) == 2


def test_parse_cli_map_default_and_override():
    assert parse_cli([]) == ("objects", None, [])
    assert parse_cli(["map"]) == ("map", None, [])
    assert parse_cli(["map", "valley"]) == ("map", "valley", [])
    assert parse_cli(["objects", "data/map/inhouse.map"]) == (
        "objects",
        "data/map/inhouse.map",
        [],
    )
    assert parse_cli(["test", "--map", "valley.map"]) == (
        "test",
        None,
        ["--map", "valley.map"],
    )
    assert DEFAULT_MAP == "island3.map"
