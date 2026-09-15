"""What the study runs on: the export says which markets exist, markets.yaml says what they are."""

from pathlib import Path

import yaml

FILE = Path(__file__).with_name("markets.yaml")
UNCLASSIFIED = "sin clasificar"


def load(symbol: str) -> dict:
    """One base asset's declared retest universe.

    Args:
        symbol: Base asset, e.g. "XAUUSD".

    Returns:
        Keys main, timeframe and categories, where categories maps a category name to a list
        of {feed, data_from}. This is the declaration, fixed before results are looked at; it
        classifies markets and never decides which ones the study runs on.
    """
    return yaml.safe_load(FILE.read_text(encoding="utf-8"))[symbol]


def discovered(trades: Path) -> list[str]:
    """Which markets the export actually carries trades for.

    Args:
        trades: The export's `trades/` directory, one subdirectory per feed.

    Returns:
        Feed names, sorted. Written by export_retest from the trades' own Symbol column, so
        this is what the retest really ran, not what a task list or this file claims.
    """
    return sorted(d.name for d in trades.iterdir() if d.is_dir())


def classify(symbol: str) -> dict[str, str]:
    """Feed to category, for every market the declaration names.

    Args:
        symbol: Base asset.

    Returns:
        {feed: category}. The base asset is not in it: it belongs to no category because it
        is the market the strategies were fitted on.
    """
    return {m["feed"]: name for name, markets in load(symbol)["categories"].items()
            for m in markets}


def dates(symbol: str) -> dict[str, str]:
    """Feed to the first date its data covers, as the declaration states it.

    Args:
        symbol: Base asset.

    Returns:
        {feed: data_from}, stringified. Nothing is filtered on it; it is reported so the
        shrinking of the common window across markets is visible.
    """
    return {m["feed"]: str(m["data_from"]) for markets in load(symbol)["categories"].values()
            for m in markets}


def declared(symbol: str) -> list[str]:
    """Every SQX symbol the declaration names, base asset first.

    Args:
        symbol: Base asset.

    Returns:
        The main feed, then every feed of every category. This is the list to export bars
        for: bars are pulled **before** the retest is exported, so there is nothing to
        discover from yet and the declaration is all there is. Everything after that point
        works from universe(), which reconciles the declaration against what really ran.
    """
    spec = load(symbol)
    return [spec["main"]] + [m["feed"] for markets_ in spec["categories"].values()
                             for m in markets_]


def universe(symbol: str, trades: Path) -> dict:
    """Reconcile what the export carries against what markets.yaml declares.

    Args:
        symbol: Base asset.
        trades: The export's `trades/` directory.

    Returns:
        Keys main, timeframe, markets and absent. `markets` is one row per feed the export
        carries besides the base asset, each with its category and data_from — a feed the
        declaration does not name is kept and marked UNCLASSIFIED rather than dropped, so a
        mismatch is visible instead of silently shrinking the study. `absent` names the
        declared feeds the export has no trades for, which is the other half of the same
        mismatch.
    """
    spec = load(symbol)
    known, first = classify(symbol), dates(symbol)
    present = [f for f in discovered(trades) if f != spec["main"]]
    return {"main": spec["main"], "timeframe": spec["timeframe"],
            "markets": [{"feed": f, "category": known.get(f, UNCLASSIFIED),
                         "data_from": first.get(f, "unknown")} for f in present],
            "absent": sorted(set(known) - set(present))}


def feeds(universe_: dict) -> list[str]:
    """Every SQX symbol the study needs bars for, base asset first.

    Args:
        universe_: What universe() returned.

    Returns:
        The main feed, then every market. Bars for the base asset are loaded even though it
        is never tested against its own null, because it is reported as the reference case.
    """
    return [universe_["main"]] + [m["feed"] for m in universe_["markets"]]
