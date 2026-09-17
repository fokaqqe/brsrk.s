"""Resolve card image paths across machines and launch directories."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_image_path(image_path):
    if not image_path:
        return None

    raw_path = Path(str(image_path))
    candidates = [raw_path]
    if not raw_path.is_absolute():
        candidates.append(PROJECT_ROOT / raw_path)
    candidates.append(PROJECT_ROOT / "images" / raw_path.name)

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None
