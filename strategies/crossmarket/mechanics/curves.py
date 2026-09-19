"""Each market's equity on its own real calendar, and what it is worth at equal risk.

Every market runs its **own independent account**: the same starting capital, its own real
position sizes, its own dates. Nothing here adds two markets together — that is
simulate/portfolio.py, where the drawdown of a combination has to be computed on the combined curve, never summed
from the parts."""

import numpy as np
import pandas as pd

COMBINED = "cuenta combinada"    # what the whole account is called on the portfolio chart


def sampled(equity: np.ndarray, closed: pd.DatetimeIndex, cfg: dict) -> dict:
    """One cumulative P&L series thinned to the points a chart can draw.

    Args:
        equity: Cumulative P&L in USD, in close order.
        closed: When each of those trades closed.
        cfg: What config.load() returned.

    Returns:
        Keys dates (ISO) and pct, per cent of the starting account. Thinned by index rather
        than by time, so a stretch with no trades is a flat line between two real points
        instead of a hundred repeated ones.
    """
    steps = min(cfg["equity"]["steps"], len(equity))
    edges = np.unique(np.linspace(0, len(equity) - 1, steps).astype(int))
    return {"dates": [str(closed[i].date()) for i in edges],
            "pct": (equity[edges] / cfg["equity"]["starting"] * 100).tolist()}


def combined(merged: pd.DataFrame, cfg: dict) -> dict:
    """The combined account's equity, and what each market contributed to it.

    Args:
        merged: What portfolio.stream() returned — every market's trades in close order.
        cfg: What config.load() returned.

    Returns:
        {"cuenta combinada": series} plus one per market, in the shape overlays.equity() draws. Every
        market's line is its own cumulative P&L inside the **shared** account, so the lines
        add up to the combined one. That is the difference from series() below, where each
        market has an independent account and the heights are not comparable at all: here a
        market's line reads as "how much of the combined result is this one", and a line that
        spends the sample under zero is a market the rest of the account carried.
    """
    parts = [(COMBINED, merged)] + [(f, merged[merged["feed"] == f])
                                       for f in merged["feed"].unique()]
    return {feed: sampled(np.cumsum(part["pnl"].to_numpy()),
                          pd.DatetimeIndex(part["close"].to_numpy()), cfg)
            for feed, part in parts}


def series(fixed: dict, cfg: dict) -> dict:
    """One market's equity through its own backtest, as a share of the starting account.

    Args:
        fixed: What backtest.setting() returned.
        cfg: What config.load() returned.

    Returns:
        Keys dates (ISO, one per step) and pct (per cent of the starting account, starting at
        zero). Per cent rather than dollars because the sizes differ by market: silver risking
        ten times gold would otherwise flatten gold to a straight line on a shared axis. Each
        trade lands on its **exit**, when the money is realised, and the axis is the market's
        own dates — a market whose backtest starts in 2011 starts in 2011 on the chart.

        Drawn from **every** trade SQX reported, not from the ones the bar grid could hold: a
        curve that silently omits 2% of the trades does not end where the databank says the
        account ended.
    """
    return sampled(np.cumsum(fixed["all"]["pnl"]),
                   pd.DatetimeIndex(fixed["all"]["close"]), cfg)


def equalised(stats: dict, cfg: dict) -> dict:
    """What this market returned once its worst drawdown is scaled to a common size.

    Args:
        stats: What metrics.observed() returned for the real backtest.
        cfg: What config.load() returned, for equity.risk_target_dd and the account size.

    Returns:
        Keys factor, return_pct and target. Position size is multiplied by `factor` so that
        the worst drawdown of the sample becomes exactly `risk_target_dd` of the account, and
        the return is multiplied by the same number — the sizing here is fixed per trade, so
        the whole curve scales linearly and nothing has to be re-simulated.

        It answers the only fair version of "which market did better": silver making twice
        the money while drawing down three times as hard did not do better, it took more
        risk. Its weakness is that it hangs off **one** moment of the sample — the single
        worst peak-to-trough — so read it next to Ret/DD, which is scale-free and uses the
        same two numbers without pinning the account size.
    """
    target = cfg["equity"]["risk_target_dd"] * cfg["equity"]["starting"]
    factor = target / stats["dd"] if stats["dd"] > 0 else float("nan")
    return {"factor": factor, "target": cfg["equity"]["risk_target_dd"],
            "return_pct": stats["net"] * factor / cfg["equity"]["starting"] * 100}
