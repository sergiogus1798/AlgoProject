"""The two proofs a stop retest has to pass before anything in it is read: the graft, and the ATR."""

import numpy as np
import pandas as pd

from studies.closing.atrCalculator.mae import before_entry

SAME = ("Open time", "Close time", "Open price", "Close price")
STOP = "SL"          # the `Close type` SQX writes for a trade its stop closed (🔬 2026-09-26)


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


def atr(stopped: pd.DataFrame, index: pd.DatetimeIndex, values: np.ndarray,
        cfg: dict) -> pd.DataFrame:
    """The ATR each stop implies against the ATR this study computes, bar by bar around the entry.

    Args:
        stopped: Trades closed by the stop, with `segment` and the `x` their variant carried.
        index: Bar open times of the strategy's timeframe.
        values: `engines.market.atr.sqx` on those bars.
        cfg: The study's config.

    Returns:
        One row per window and candidate bar — the entry bar, the bar before it (what SQX's
        shift 1 should mean) and the one before that: the ratio `|close - open| / (x * ATR)`
        at its 5th, 50th and 95th percentile, the `spread` between those two tails, and
        `matches` when the spread is within `proof.atr_spread`, and `slip`, the median of
        `|close - open| - x * ATR` in price, which on the right bar is the exit's slippage. The stop slips on exit by a
        fixed amount per window, so the right bar gives a ratio a hair above 1 for every
        trade; a wrong bar or a wrong recurrence scatters it by a share of the ATR.
    """
    rows = []
    for s, here in stopped.groupby("segment"):
        distance = (here["Close price"] - here["Open price"]).abs().to_numpy()
        before = before_entry(index, here["Open time"])
        for label, shift in (("barra de la entrada", 1), ("barra anterior (shift 1)", 0),
                             ("dos barras antes", -1)):
            stop = here["x"].to_numpy() * values[before + shift]
            p5, p50, p95 = np.percentile(distance / stop, [5, 50, 95])
            rows.append({"segment": s, "bar": label, "n": len(here), "p5": p5, "median": p50,
                         "p95": p95, "spread": p95 - p5,
                         "slip": float(np.median(distance - stop)),
                         "matches": bool(p95 - p5 <= cfg["proof"]["atr_spread"])})
    return pd.DataFrame(rows)
