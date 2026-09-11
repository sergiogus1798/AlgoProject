"""Read markets.yaml: which additional markets each base asset is retested on."""

from pathlib import Path

import yaml

FILE = Path(__file__).with_name("markets.yaml")


def load(symbol: str) -> dict:
    """One base asset's retest universe.

    Args:
        symbol: Base asset, e.g. "XAUUSD".

    Returns:
        Keys main, timeframe and additional, where additional is a list of {feed, role,
        data_from}. The base asset is never inside that list: it is the market the strategies
        were fitted on, so its random-entry p-value is not interpretable and it must not vote.
    """
    return yaml.safe_load(FILE.read_text(encoding="utf-8"))[symbol]


def feeds(symbol: str) -> list[str]:
    """Every SQX symbol the study needs bars for, base asset included.

    Args:
        symbol: Base asset.

    Returns:
        The main feed first, then the additional ones. Bars for the base asset are exported
        even though it does not vote, because the study reports it as the reference case.
    """
    spec = load(symbol)
    return [spec["main"]] + [m["feed"] for m in spec["additional"]]
