"""The two proofs a stop retest has to pass before anything in it is read: the graft, and the ATR."""

import numpy as np
import pandas as pd

from studies.closing.atrCalculator.mae import before_entry

SAME = ("Open time", "Close time", "Open price", "Close price")
STOP = "Stop Loss"          # the `Close type` SQX writes for a trade its stop closed


def graft(reference: pd.DataFrame, probe: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Whether the X = 1000 probe reproduces the original trade for trade, per window.

    Args:
        reference: The original's trades, without a stop, with `segment`.
        probe: The same strategy with the grafted stop at 1000 ATR, which never fires.
        cfg: The study's config.

    Returns:
        One row per segment: both counts, how many trades differ in any of the four times
        and prices or by more than `proof.pl_tolerance` in P/L, the largest P/L difference,
        and `identical`. Anything but identical means the graft changed the strategy.
    """
    rows = []
    for s in sorted(set(reference["segment"]) | set(probe["segment"])):
        a = reference[reference["segment"] == s].sort_values("Open time").reset_index(drop=True)
        b = probe[probe["segment"] == s].sort_values("Open time").reset_index(drop=True)
        if len(a) != len(b):
            rows.append({"segment": s, "n_reference": len(a), "n_probe": len(b),
                         "differ": abs(len(a) - len(b)), "max_pl_diff": np.nan,
                         "identical": False})
            continue
        pl = (a["Profit/Loss"] - b["Profit/Loss"]).abs()
        differ = (pl > cfg["proof"]["pl_tolerance"]) | np.any(
            [a[c].to_numpy() != b[c].to_numpy() for c in SAME], axis=0)
        rows.append({"segment": s, "n_reference": len(a), "n_probe": len(b),
                     "differ": int(differ.sum()), "max_pl_diff": float(pl.max()),
                     "identical": not differ.any()})
    return pd.DataFrame(rows)


def atr(stopped: pd.DataFrame, index: pd.DatetimeIndex, values: np.ndarray) -> pd.DataFrame:
    """The ATR each stop implies against the ATR this study computes, bar by bar around the entry.

    Args:
        stopped: Trades closed by the stop, with the `x` their variant carried.
        index: Bar open times of the strategy's timeframe.
        values: `engines.market.atr.sqx` on those bars.

    Returns:
        One row per candidate bar — the entry bar, the bar before it (what shift 1 should
        mean) and the one before that: the median and the 90th percentile of the absolute
        residual `|close - open| - x * ATR` in price. The stop is placed from the fill and
        slips on exit, so the residual of the right bar is the fill's spread and the exit's
        slippage, the same for every trade; a wrong bar or a wrong recurrence scatters it
        by a share of the ATR.
    """
    distance = (stopped["Close price"] - stopped["Open price"]).abs().to_numpy()
    before = before_entry(index, stopped["Open time"])
    rows = []
    for label, shift in (("barra de la entrada", 1), ("barra anterior (shift 1)", 0),
                         ("dos barras antes", -1)):
        residual = np.abs(distance - stopped["x"].to_numpy() * values[before + shift])
        rows.append({"bar": label, "n": len(stopped),
                     "median_residual": float(np.median(residual)),
                     "p90_residual": float(np.percentile(residual, 90))})
    return pd.DataFrame(rows)
