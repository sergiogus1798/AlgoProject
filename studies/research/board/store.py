"""Where the board and the proposals live under the data root."""

import json
from pathlib import Path
from typing import Any

from core.fsio import atomic_write
from core.researchpaths import research_memory_dir


def board_dir() -> Path:
    """`AlgoData/research/board/`, created on first use."""
    path = research_memory_dir().parent / "board"
    path.mkdir(parents=True, exist_ok=True)
    return path


def proposals_dir() -> Path:
    """`AlgoData/research/proposals/`: one `<id>.json` and `<id>.md` per proposal."""
    path = research_memory_dir().parent / "proposals"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write(path: Path, data: dict) -> Path:
    """A dict as indented UTF-8 JSON, written whole through a temp file beside it."""
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=1))
    return path


def read(path: Path) -> dict[str, Any]:
    """A JSON file as a dict."""
    return json.loads(path.read_text(encoding="utf-8"))
