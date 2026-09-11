"""The input contract: any time-ordered trade list, reduced to what every family needs."""

from pathlib import Path

import numpy as np
import pandas as pd

from core import trades
from strategies.monteCarlo import costs

def _from_frame(frame: pd.DataFrame, asset: dict, risk: float) -> dict:
    """The arrays every family runs on, from a frame already in time order.

    Args:
        frame: Trades as core.trades.read() returns them.
        asset: What costs.load() returned.
        risk: USD risked per trade, the divisor of the R-multiple.

    Returns:
        Aligned numpy arrays. `pnl` is net USD as SQX booked it and is the primary input of
        every family; `cost` and `spread` are what Family C perturbs; `sample` is IS/OOS as
        SQX labelled it. Nothing here is imputed: a column the export does not carry does
        not appear.
    """
    pnl = frame["Profit/Loss"].to_numpy(dtype=float)
    return {"pnl": pnl, "r": pnl / risk, "cost": costs.recovered(frame, asset),
            "spread": costs.spread_cost(frame, asset),
            "mae": frame["MAE ($)"].to_numpy(dtype=float),
            "size": frame["Size"].to_numpy(dtype=float),
            "open": frame["Open time"].to_numpy(),
            "close": frame["Close time"].to_numpy(),
            "sample": frame["Sample type"].to_numpy(dtype=object)}


def build(path: Path, asset: dict, risk: float) -> dict:
    """One strategy's exported trades as a stream.

    Args:
        path: A CSV written by `-tools action=orderstocsv`, one strategy.
        asset: What costs.load() returned.
        risk: USD risked per trade.

    Returns:
        The stream contract: its name, the source frame, and the arrays of _from_frame().
    """
    frame = trades.read(path)
    return {"name": path.stem, "frame": frame, **_from_frame(frame, asset, risk)}


def portfolio(paths: list[Path], asset: dict, risk: float, name: str) -> dict:
    """Several strategies as one trade stream, in time order.

    Args:
        paths: One CSV per strategy.
        asset: What costs.load() returned.
        risk: USD risked per trade.
        name: What to call the combined stream.

    Returns:
        The same contract build() returns. Every family runs on it unchanged, because the
        trade list is the only thing they were ever given. Read overlap() before believing
        an order-dependent statistic of it.
    """
    frame = pd.concat([trades.read(p) for p in paths]).sort_values("Open time")
    frame = frame.reset_index(drop=True)
    return {"name": name, "frame": frame, **_from_frame(frame, asset, risk)}


def samples(stream: dict) -> dict[str, np.ndarray]:
    """Where the in-sample and out-of-sample trades sit in the stream.

    Args:
        stream: What build() returned.

    Returns:
        {"IS": positions, "OOS": positions}, empty for a label the export does not carry.
        SQX writes IST for in-sample and OOS1 for the retest window; which labels a strategy
        has depends on how it was last retested, so this reads them rather than assuming.
    """
    tag = np.array([str(s)[:3] for s in stream["sample"]])
    return {"IS": np.flatnonzero(tag == "IST"), "OOS": np.flatnonzero(tag == "OOS")}


def overlap(stream: dict) -> float:
    """Share of trades that were open while the previous one was still open.

    Args:
        stream: What build() returned.

    Returns:
        A fraction. Zero for one strategy that trades one position at a time; above zero for
        a portfolio, where order-dependent statistics — the longest losing run above all —
        stop meaning what they mean for a single strategy. The report says so when it is.
    """
    order = np.argsort(stream["open"])
    opens, closes = stream["open"][order], stream["close"][order]
    return float(np.mean(opens[1:] < closes[:-1])) if len(opens) > 1 else 0.0
