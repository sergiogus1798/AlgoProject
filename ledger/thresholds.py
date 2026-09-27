"""The versioned thresholds, and whether the code still uses the numbers they declare."""

import re
from functools import lru_cache

import pandas as pd
import yaml

from core.paths import ROOT

FILE = ROOT / "ledger" / "thresholds.yaml"
SELECTOR = re.compile(r"^(\w+)\[(\w+)=([^\]]+)\]$")
PLACEHOLDER = "ledger:"   # what a module's config.yaml writes where the ledger owns the number


def declared() -> list[dict]:
    """Every threshold this project has written down, with who set it and when.

    Returns:
        The rows of `thresholds.yaml`. Read by whoever needs a number; written by nobody.
        Parsed once per state of the file: 🔬 2026-09-27, `fill()` asked for it once per
        placeholder, 66 parses and ~5 s of a cold config load, the most of a 1-2 s study.
    """
    stat = FILE.stat()
    return _parsed(stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=4)
def _parsed(stamp: int, size: int) -> list[dict]:
    """`declared()` for one state of the file; the key changes the moment anyone edits it."""
    return yaml.safe_load(FILE.read_text(encoding="utf-8"))["thresholds"]


def value(key: str) -> object:
    """The number the ledger declares for one threshold.

    Args:
        key: As `thresholds.yaml` spells it, e.g. "gate.sanidad.min_trades".

    Returns:
        Its `value`. Raises KeyError unless the key is declared exactly once: a missing
        threshold must stop the run, and a key appended twice by two branches must not
        quietly resolve to whichever came last.
    """
    found = [row["value"] for row in declared() if row["key"] == key]
    if len(found) != 1:
        raise KeyError(f"{key}: declared {len(found)} times in {FILE.name}, "
                       "a module reading it needs exactly one")
    return found[0]


def fill(node: object) -> object:
    """A parsed config.yaml with every "ledger:<key>" replaced by the ledger's value.

    Args:
        node: The parsed YAML, before any command-line override is applied, so an
            override is still held to the type of the number it replaces.

    Returns:
        A copy, keys in their original order: the gate prints a screen's thresholds in
        the order its row lists them, and a report must not change because a number moved.
    """
    if isinstance(node, dict):
        return {k: fill(v) for k, v in node.items()}
    if isinstance(node, list):
        return [fill(v) for v in node]
    if isinstance(node, str) and node.startswith(PLACEHOLDER):
        return value(node.removeprefix(PLACEHOLDER))
    return node


def resolve(source: str) -> float:
    """The value the code actually uses, followed from a `file#a.b.c` pointer.

    Args:
        source: `path/to/config.yaml#key.sub.key`, where a step may also be
            `list[field=value]` to pick one entry out of a list of dicts.

    Returns:
        Whatever sits at the end of that path. Raises on a pointer that no longer
        resolves, which is the point: a threshold whose home moved is exactly the case a
        silent default would hide.
    """
    path, dotted = source.split("#", 1)
    return walk(yaml.safe_load((ROOT / path).read_text(encoding="utf-8")), dotted)


def walk(node: object, dotted: str) -> object:
    """Follow the part of a pointer after the `#` through a parsed config.

    Args:
        node: A parsed config, raw or as a module's config() returns it.
        dotted: `key.sub.key`, a step possibly `list[field=value]`.

    Returns:
        Whatever sits at the end of the path.
    """
    for step in dotted.split("."):
        picked = SELECTOR.match(step)
        if picked:
            name, field, wanted = picked.groups()
            node = next(item for item in node[name] if str(item[field]) == wanted)
        else:
            node = node[step]
    return node


def divergences() -> pd.DataFrame:
    """Where the register and the code disagree.

    Returns:
        One row per declared threshold, and where its module takes it from. `ledger`: the
        module's config.yaml holds `ledger:<this key>` and the number comes from here, so
        the two cannot diverge. `copia`: the config still holds its own number, which must
        equal the declared one. A placeholder naming another key is a divergence too.
    """
    rows = []
    for row in declared():
        live = resolve(row["source"])
        migrated = isinstance(live, str) and live.startswith(PLACEHOLDER)
        rows.append({"key": row["key"], "declarado": row["value"],
                     "lee_de": "ledger" if migrated else "copia",
                     "coincide": bool(live == PLACEHOLDER + row["key"] if migrated
                                      else live == row["value"]),
                     "fijado_por": row["set_by"], "el": row["set_on"]})
    return pd.DataFrame(rows)
