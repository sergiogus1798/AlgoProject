"""Where the literature lives on disk: the entries, the papers seen, their texts and the runs."""

import json
import re
from pathlib import Path
from typing import Any, cast

import yaml

from core.fsio import atomic_write
from core.researchpaths import research_literature_dir
from core.study import config as study_config

CONFIG = Path(__file__).with_name("config.yaml")
NUMBER = re.compile(r"^[A-Z]+-(\d+)")


def config() -> dict[str, Any]:
    """The parsed config.yaml."""
    return study_config.load(CONFIG, [])


def entries() -> list[dict]:
    """Every entry: the hand-built `edges-*.yaml` first, then the scout's `scout-*.yaml` by day."""
    root = research_literature_dir()
    files = sorted(root.glob("edges-*.yaml")) + sorted(root.glob("scout-*.yaml"))
    return [
        e
        for f in files
        for e in yaml.safe_load(f.read_text(encoding="utf-8"))["entries"]
    ]


def next_number() -> int:
    """One more than the largest number any entry id carries."""
    return 1 + max(
        int(cast("re.Match[str]", NUMBER.match(e["id"]))[1]) for e in entries()
    )


def add(entry: dict, day: str) -> Path:
    """Append one stamped entry to that day's `scout-<day>.yaml`."""
    path = research_literature_dir() / f"scout-{day}.yaml"
    held = (
        yaml.safe_load(path.read_text(encoding="utf-8"))
        if path.exists()
        else {"generated": day, "entries": []}
    )
    held["entries"].append(entry)
    path.write_text(
        yaml.safe_dump(held, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8",
    )
    return path


def replace(entry: dict) -> None:
    """Rewrite one scout entry in place, found by its id (the owner's answer to a question)."""
    for path in research_literature_dir().glob("scout-*.yaml"):
        held = yaml.safe_load(path.read_text(encoding="utf-8"))
        if any(e["id"] == entry["id"] for e in held["entries"]):
            held["entries"] = [
                entry if e["id"] == entry["id"] else e for e in held["entries"]
            ]
            path.write_text(
                yaml.safe_dump(held, sort_keys=False, allow_unicode=True, width=110),
                encoding="utf-8",
            )


def papers() -> dict[str, dict]:
    """Every paper the search ever returned, by key, in the order found."""
    path = research_literature_dir() / "papers.jsonl"
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return {r["key"]: r for r in rows}


def save_papers(rows: dict[str, dict]) -> None:
    """Write the papers register whole, through a temp file beside it."""
    path = research_literature_dir() / "papers.jsonl"
    atomic_write(
        path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows.values())
    )


def text_path(key: str) -> Path:
    """Where a paper's stored source is: `papers/<key>.txt`, with its `[page N]` marks."""
    folder = research_literature_dir() / "papers"
    folder.mkdir(exist_ok=True)
    return folder / f"{key}.txt"


def runs() -> list[dict]:
    """Every run's cost line, oldest first."""
    path = research_literature_dir() / "runs.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def add_run(row: dict) -> None:
    """Append one run's cost line."""
    with (research_literature_dir() / "runs.jsonl").open(
        "a", encoding="utf-8"
    ) as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
