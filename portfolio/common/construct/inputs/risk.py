"""A member's sizing factor: its worst build day of floating loss, the scale it sets, its floor lot."""

from pathlib import Path
from typing import TypedDict

import pandas as pd

from core.archive import read as archive_read


class Sizing(TypedDict):
    """A member's sizing inputs: its worst build day in SQX dollars, the lot floor and the factor."""

    worst_day: float
    min_size: float
    factor: float


def worst_day(trades: pd.DataFrame) -> float:
    """The worst day of floating loss on build, in SQX dollars at SQX's own sizing (positive).

    A day's loss is the sum of the MAE of the trades that close on it (feed clock), build (`IS`)
    only so no held-out sample sizes the member. Summing MAEs that did not happen at the same
    minute over-states the day; a trade at a gain at the day's open can lose more that day than
    its MAE, which under-states it.
    # ponytail: per-trade MAE by close day; the exact figure is the universe's M5 low per firm day

    Raises:
        ValueError: No build trade ever went against the strategy -- nothing to size it by.
    """
    build = trades.loc[trades["sample"] == "IS"]
    loss = build["MAE ($)"].clip(upper=0.0)
    worst = -float(loss.groupby(build["Close time"].dt.date).sum().min())
    if not worst > 0:
        raise ValueError("sin pérdida flotante en build: nada con que dimensionarla")
    return worst


def sizing(identity: str, version: str) -> Sizing:
    """The member's factor, `f = 1 / worst_day`: SQX dollars to per-(r*S) dollars.

    The member keeps SQX's own money management (`knowhow/sqx-format/money-management-atr-fixed-risk.md`)
    scaled by one constant, so at level `r` of a balance `S` its worst build day of floating loss
    is `r * S`. The funded search's `open_risk_cap` then bounds the sum of those worst days over
    the members against the plan's daily-loss room (`search/stagea.open_cap`).

    Args:
        identity: SHA-256 of the strategy's normalised XML.
        version: The archived version folder name.

    Returns:
        `worst_day` (`worst_day()` of `harvest/trades.parquet`), `min_size` (the smallest trade
        lot SQX drew, every sample), `factor`.
    """
    got = archive_read.load(identity, version)
    trades = pd.read_parquet(Path(got["folder"]) / "harvest" / "trades.parquet")
    worst = worst_day(trades)
    return {
        "worst_day": worst,
        "min_size": float(trades["Size"].min()),
        "factor": 1.0 / worst,
    }
