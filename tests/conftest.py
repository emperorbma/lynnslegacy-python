import os

import pytest

# Keep pytest off the real audio device. Live check: `python -m lynn audio`.
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

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
