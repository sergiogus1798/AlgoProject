"""A study's knobs: its config.yaml read, overridden from the command line, and fingerprinted."""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import yaml


def _cast(old: object, raw: str) -> object:
    """Read one override as YAML and hold it to the type of the value it replaces.

    Args:
        old: The value in config.yaml.
        raw: What followed the "=" on the command line.

    Returns:
        The new value. An int is widened where a float stood; any other change of type is
        refused, so a threshold typed on the command line cannot silently become a string.
    """
    new = yaml.safe_load(raw)
    if old is None or type(new) is type(old):
        return new
    if isinstance(old, float) and isinstance(new, int) and not isinstance(new, bool):
        return float(new)
    raise ValueError(f"{raw!r} is a {type(new).__name__}, the knob it replaces is a "
                     f"{type(old).__name__}")


def apply(cfg: dict, overrides: list[str], names: dict | None = None) -> dict:
    """Apply "section.key=value" overrides in place.

    Args:
        cfg: The parsed config.
        overrides: As --set gives them; the path may be as deep as the YAML is,
            e.g. "global.n_sims=20000" or "family_d.windows.months=12".
        names: Extra first-level names that resolve to a node inside cfg, for a config whose
            sections live in a list (the gate addresses a screen by its own name).

    Returns:
        cfg, changed.
    """
    for item in overrides:
        where, raw = item.split("=", 1)
        *path, leaf = where.split(".")
        # A key at the top of the file ("min_trades=40") has no section to walk into.
        node = ((names or {}).get(path[0]) or cfg[path[0]]) if path else cfg
        for key in path[1:]:
            node = node[key]
        node[leaf] = _cast(node[leaf], raw)
    return cfg


def load(path: Path, overrides: list[str],
         names: Callable[[dict], dict] | None = None) -> dict:
    """A config.yaml with its overrides applied.

    Args:
        path: The module's config.yaml.
        overrides: "section.key=value" strings.
        names: Builds apply()'s extra names from the parsed config.

    Returns:
        The parsed config.
    """
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    return apply(cfg, overrides, names(cfg) if names else None)


def fingerprint(cfg: dict) -> str:
    """The config's hash, signed into every result computed under it.

    Args:
        cfg: A parsed config, overrides applied.

    Returns:
        16 hex characters. The window marks a stored result stale when this differs from the
        drawer's, so a number is never read as the answer to a question it was not asked.
    """
    blob = json.dumps(cfg, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
