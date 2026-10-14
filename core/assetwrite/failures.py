"""Write one entry of an asset's `live_failures` list — why a strategy of it left the live protocol."""

from datetime import date
from typing import TypedDict

from core.assetdata import SYMBOLS
from core.assetyaml import read, write


class LiveFailure(TypedDict):
    """One entry of an asset's `live_failures` list."""

    date: str
    strategy: str
    row: str
    value: float | None


def add_live_failure(symbol: str, day: date, strategy: str, row: str,
                     value: float | None) -> LiveFailure:
    """Append one failure to the asset's card, comments and every other line untouched.

    Args:
        symbol: Asset name.
        day: The day stage A judged the strategy.
        strategy: The strategy's name in the live register.
        row: The step-26 row that failed ("2", "3a", "5").
        value: The measured figure of that row (None when it could not be computed).

    Returns:
        The entry as written; `live_failures` is created at the end of the card on the first one.
    """
    path = SYMBOLS / f"{symbol}.yaml"
    doc = read(path)
    entry: LiveFailure = {"date": day.isoformat(), "strategy": strategy, "row": row,
             "value": None if value is None else round(float(value), 4)}
    doc.setdefault("live_failures", []).append(entry)
    write(path, doc)
    from core.assetwrite import reindex

    reindex()
    return entry
