import pytest

from lynn.paths import DEFAULT_MAP, resolve_map_path


def pytest_addoption(parser):
    parser.addoption(
        "--map",
        action="store",
        default=DEFAULT_MAP,
        help=f"Map stem or path for demo tests (default: {DEFAULT_MAP})",
    )


@pytest.fixture
def map_spec(request) -> str:
    return request.config.getoption("--map")


@pytest.fixture
def map_path(map_spec):
    try:
        path = resolve_map_path(map_spec)
    except FileNotFoundError:
        pytest.skip(f"map not found: {map_spec}")
    return path
