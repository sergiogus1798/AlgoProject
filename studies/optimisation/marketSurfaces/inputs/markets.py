"""The markets `assets/_markets.yaml` declares for an asset: category, first date, group and weight."""

from datetime import date
from typing import cast

import pandas as pd

from core import assetdata, assetmarkets

PROVISIONAL = "PROVISIONAL"
GROUPS = "near_identical"      # the optional key of an asset's block in _markets.yaml


def declared(symbol: str) -> pd.DataFrame:
    """The cross-check markets fixed for this asset before any result was looked at.

    Args:
        symbol: The main asset, e.g. "NIKKEI225".

    Returns:
        One row per market, in the file's order: `feed`, `category` (the file's own word),
        `data_from` (ISO date or None) and `group` (the position of its group of
        near-identical markets in the block's `near_identical` list, -1 when it has none).
    """
    block = assetmarkets.markets(symbol)
    group = {feed: i for i, feeds in enumerate(block.get(GROUPS) or []) for feed in feeds}
    return pd.DataFrame(
        [{"feed": m["feed"], "category": category,
          "data_from": m["data_from"].isoformat() if isinstance(m.get("data_from"), date) else None,
          "group": group.get(m["feed"], -1)}
         for category, rows in block["categories"].items() for m in rows or []])


def provisional(feed: str) -> bool:
    """Whether a market's cost card still carries a placeholder: a `why` that starts PROVISIONAL."""
    costs = assetdata.load(cast(str, assetdata.symbol_for(feed)))["costs"]
    return any(str(c.get("why", "")).startswith(PROVISIONAL) for c in costs.values())
