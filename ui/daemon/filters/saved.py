"""Filters saved by name, to apply again: `AlgoData/filters/saved.yaml`."""

import yaml

from ui.daemon.filters.discards import root, stamp

FILE = root() / "saved.yaml"


def every() -> dict[str, dict]:
    """name → {rows, saved}; {} when nothing was saved yet."""
    return yaml.safe_load(FILE.read_text(encoding="utf-8")) or {} if FILE.is_file() else {}


def save(name: str, rows: list[dict]) -> dict:
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
