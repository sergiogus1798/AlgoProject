"""Where the board and the proposals live under the data root."""

import json
from pathlib import Path

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
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)
    return path


def read(path: Path) -> dict:
    """A JSON file as a dict."""
    return json.loads(path.read_text(encoding="utf-8"))
