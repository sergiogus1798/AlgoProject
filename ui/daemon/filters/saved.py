"""Filters saved by name, to apply again: `AlgoData/filters/saved.yaml`."""

from typing import TypedDict

import yaml

from core.paths import filters_root
from ui.daemon.filters.discards import stamp

FILE = filters_root() / "saved.yaml"


class SavedFilter(TypedDict):
    """A filter kept by name: its rows and the day it was saved."""

    rows: list[dict]
    saved: str


def every() -> dict[str, SavedFilter]:
    """name → {rows, saved}; {} when nothing was saved yet."""
    return yaml.safe_load(FILE.read_text(encoding="utf-8")) or {} if FILE.is_file() else {}


def save(name: str, rows: list[dict]) -> SavedFilter:
    """Keep one filter under a name, replacing a filter of the same name.

    Args:
        name: What the owner typed.
        rows: The filter's rows, [{metric, op, value}].

    Returns:
        What was written under that name.
    """
    kept = every()
    kept[name] = {"rows": rows, "saved": stamp()}
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(yaml.safe_dump(kept, allow_unicode=True, sort_keys=True), encoding="utf-8")
    return kept[name]
