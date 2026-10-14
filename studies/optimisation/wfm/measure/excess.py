"""Each trade's net excess with oos2 re-charged at its own costs, and the weekly oos2 panel."""

from collections.abc import Sequence
from typing import cast

import numpy as np
import pandas as pd

from engines.market import reprice
from engines.weekly import panel
from studies.optimisation.wfm.inputs.asset import Asset
from studies.screening.analysis import tradelevel

CLEAN = "oos2"


def recharge(trades: pd.DataFrame, charged: reprice.Costs, real: reprice.Costs) -> np.ndarray:
    """What a trade charged at one segment's costs would have paid on top at another's.

    Args:
        trades: `Size` (lots) and `Open price` (SQX's fill), one row per trade.
        charged: `reprice.costs` of the segment SQX's task was charged with.
        real: `reprice.costs` of the segment the trade is judged at.

    Returns:
        Account currency per trade, to SUBTRACT from SQX's P/L: lots x point value x (the
        spread's difference + twice the slippage's, which SQX charges at the entry and at
        the exit) plus the commission's difference. The swap is the same card's in every
        segment. First order: a stop or a target that the wider spread would have touched
        at another moment is not moved.
    """
    size = trades["Size"].to_numpy(float)
    value = real["point_value"] * size

    def fee(costs: reprice.Costs) -> np.ndarray:
        """The commission of one card, charged once at the open as `reprice.pnl` does."""
        return ({"PercentageBased": value * trades["Open price"].to_numpy(float) / 100,
                 "SizeBased": size}[costs["commission_method"]] * costs["commission"])
    return (value * (real["spread"] - charged["spread"]
                     + 2 * (real["slippage"] - charged["slippage"])) + fee(real) - fee(charged))


def per_trade(trades: pd.DataFrame, the: Asset, unit: str) -> pd.DataFrame:
    """Trades as net excess, each tagged with the segment it closes in.

    Args:
        trades: SQX's trades of one strategy: `Type`, `Open time`, `Open price`, `Size`,
            `Close time`, `Profit/Loss` and the `unit` column.
        the: `inputs.asset.of`.
        unit: The column naming whose trade it is: a cell (`result`) or the mother.

    Returns:
        `unit`, `open`, `close`, `segment` (build, oos1, oos2 by the day it CLOSES; NaN
        outside them), `charge` (what `recharge` adds, zero outside oos2), `drift`
        (`tradelevel.drift_term` under the gate's block, measured on the bars of the trade's
        own calendar window) and `net` = Profit/Loss - charge - drift; `gross` repeats `net`,
        because `engines.weekly.panel.weekly` sums both and SQX's export holds no cost split.
    """
    day = trades["Close time"].dt.normalize()
    segment = pd.Series(np.nan, trades.index, dtype=object)
    for name, (first, last) in the["windows"].items():
        segment[(day >= first) & (day <= last)] = name
    charge = np.where(segment == CLEAN, recharge(trades, the["charged"], the["real"]), 0.0)
    drift, label = tradelevel.drift_term(trades, the["bars"], the["span"], the["drift"]["window"],
                                         the["drift"]["variant"], the["real"]["point_value"])
    assert np.isfinite(drift).all(), f"no bars to measure the drift of {set(label[~np.isfinite(drift)])}"
    net = trades["Profit/Loss"].to_numpy(float) - charge - drift
    return pd.DataFrame({unit: trades[unit].astype(str), "open": trades["Open time"],
                         "close": trades["Close time"], "segment": segment, "charge": charge,
                         "drift": drift, "net": net, "gross": net}, index=trades.index)


def weekly(per: pd.DataFrame, window: tuple[str, str], unit: str,
           units: Sequence[str]) -> pd.DataFrame:
    """Weeks x units of net excess over oos2, each trade whole in the week it closes in.

    Args:
        per: per_trade()'s rows.
        window: oos2's (first day, last day).
        unit: The unit column.
        units: The panel's columns; one without a trade closing in oos2 is a column of zeros.

    Returns:
        `engines.weekly.panel.weekly`'s `net` frame, over the trades that CLOSE in oos2 only.
    """
    return panel.weekly(cast(pd.DataFrame, per[per["segment"] == CLEAN]), window, unit, units)["net"]


def by_segment(per: pd.DataFrame, unit: str, covered: pd.DataFrame) -> pd.DataFrame:
    """Each unit's excess per year in each segment, over the years its runs covered of it.

    Args:
        per: per_trade()'s rows.
        unit: The unit column.
        covered: Indexed by unit, one column per segment: the years of that segment the
            unit's out-of-sample runs cover (a cell's first run starts years into `build`).

    Returns:
        Indexed by unit, one column per segment of `covered`: account currency per year;
        NaN where the unit's runs do not reach the segment.
    """
    total = per.pivot_table(index=unit, columns="segment", values="net", aggfunc="sum")
    total = total.reindex(index=covered.index, columns=covered.columns).fillna(0.0)
    return total / covered.where(covered > 0)
