"""The owner's prior per asset, timeframe, direction and family: Alta, Media or nothing."""

from pathlib import Path

import yaml

PRIOR = yaml.safe_load((Path(__file__).parent / "prior.yaml").read_text(encoding="utf-8"))
LEVEL = {"A": "Alta", "M": "Media", "B": "Baja"}


def level(symbol: str, timeframe: str, direction: str, family: str) -> str:
    """What the prior says of one of its own families in one cell.

    Returns:
        "Alta" when the matrix rates it Alta for the asset or the family is the main or the
        secondary one of that timeframe; "Media" or "Baja" from the matrix otherwise; "" when
        the prior does not cover the asset, the family, or — where it says «(largo)» — the side.
    """
    if symbol not in PRIOR["matrix"] or family not in PRIOR["families"]:
        return ""
    if direction == "short" and family in PRIOR["long_only"].get(symbol, []):
        return ""
    if family in PRIOR["by_timeframe"][symbol][timeframe]:
        return "Alta"
    return LEVEL[PRIOR["matrix"][symbol][PRIOR["families"].index(family)]]


def of(symbol: str, timeframe: str, direction: str, family: str, pullback_as: str) -> dict:
    """The prior of a cell of the board, whose families are the profile's seven.

    Args:
        symbol, timeframe, direction, family: The cell, family in the profile's key.
        pullback_as: The profile family the prior's `pullback` is filed under.

    Returns:
        `level` (the higher of the family's own and, for `pullback_as`, pullback's) and
        `pullback` (the level came from pullback: the idea is a trend context with a
        reversion trigger).
    """
    own = level(symbol, timeframe, direction, family)
    pull = level(symbol, timeframe, direction, "pullback") if family == pullback_as else ""
    order = ["", "Baja", "Media", "Alta"]
    best = max(own, pull, key=order.index)
    return {"level": best, "pullback": bool(pull) and order.index(pull) > order.index(own)}
