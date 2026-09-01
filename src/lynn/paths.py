"""Project / data paths. Chdir to the project root like FB ChDir ExePath."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    # src/lynn/paths.py -> parents[2] == project root
    return Path(__file__).resolve().parents[2]


def data_root() -> Path:
    return project_root() / "data"


def data_file(*parts: str) -> Path:
    rel = Path(*parts)
    return data_root() / rel


def chdir_project_root() -> Path:
    root = project_root()
    os.chdir(root)
    return root


DEFAULT_MAP = "forest_fall.map"


def resolve_map_path(spec: str | None = None) -> Path:
    """Accept a stem (`valley`), file (`valley.map`), or path. Default: forest_fall."""
    raw = (spec or DEFAULT_MAP).strip().replace("\\", "/")
    name = Path(raw).name
    if not name.lower().endswith(".map"):
        name = name + ".map"
    candidates = [
        Path(raw),
        project_root() / raw,
        data_root() / "map" / name,
        data_root() / "map" / Path(raw).name,
        Path(raw).expanduser().resolve(),
    ]
    seen: set[Path] = set()
    for cand in candidates:
        try:
            resolved = cand.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    raise FileNotFoundError(f"map not found: {spec or DEFAULT_MAP}")
