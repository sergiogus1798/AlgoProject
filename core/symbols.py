"""The short name a market is called by on screen, from its SQX symbol or feed name."""

import re

import yaml

from core.paths import ASSETS

ALIASES = ASSETS / "_aliases.yaml"
RENAMES = ASSETS / "_feed_renames.yaml"


def _overrides() -> dict:
    """The override file, parsed fresh: it is a handful of lines, edited by hand."""
    return yaml.safe_load(ALIASES.read_text()) or {}


def alias(symbol: str) -> str:
    """The short name a study or the window shows for one SQX symbol.

    Args:
        symbol: A full SQX symbol or feed name, e.g. `USDJPY_M1`, or an already
            short name, e.g. `USDJPY` (returned unchanged).

    Returns:
        The override from `assets/_aliases.yaml` when one is named, else the ticker before the
        first underscore: `AUDUSD_DarwTick_FTMO` -> `AUDUSD`. A symbol with no underscore
        (already short) passes through unchanged.
    """
    override = _overrides().get(symbol)
    if override:
        return override
    return symbol.split("_", 1)[0]


_compiled: dict = {}


def renames() -> dict[str, str]:
    """Old SQX feed name -> the name SQX holds today, from `assets/_feed_renames.yaml`."""
    return yaml.safe_load(RENAMES.read_text()) or {}


def current(text: str) -> str:
    """Text with every old feed name replaced by today's, for anything written before a rename.

    Args:
        text: A feed name read off an older `.sqx` or archive, or a whole task XML of an
            older project or the donor.

    Returns:
        The same text; longer names are replaced first so no old name is cut in half.
        The table is re-read only when its file changes, so a lookup per feed is cheap.
    """
    stamp = RENAMES.stat().st_mtime_ns
    if _compiled.get("stamp") != stamp:
        old = renames()
        rx = re.compile("|".join(sorted(map(re.escape, old), key=len, reverse=True))) if old else None
        _compiled.update(stamp=stamp, old=old, rx=rx)
    rx, old = _compiled["rx"], _compiled["old"]
    return rx.sub(lambda m: old[m.group(0)], text) if rx else text
