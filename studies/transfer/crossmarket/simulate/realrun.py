"""The real backtest: its statistics, and the mechanical checks that say whether to believe it.

Two populations, deliberately. **Everything SQX reported** is what the run *did* — net profit,
drawdown, profit factor, the trade count — and it is what the panel's master table shows, so the
page reconciles with the databank. **The trades the bar grid can hold** are what a test can compare:
a trade that opens and closes inside one bar has no interval to displace, no blind window of its own
duration, and no occupied bars. Measured on this databank the two differ by 1.84%, and by 9.8% on
the worst (strategy, market) pair, so the difference is printed rather than assumed away."""

import numpy as np
import pandas as pd

from core import trades as tradeio
from studies.transfer.crossmarket.mechanics import equity, pricing
from studies.transfer.crossmarket.simulate import metrics

# The exits a null can reproduce at a random location: one counts bars, the other reads the
# calendar. Everything else is the strategy's own signal, and `trade_models` reuses the
# recorded hold instead — which is why those trades make the test a joint entry-and-exit one.
REPRODUCIBLE = ("Exit After X Bars", "End Of Friday (Time)")


def reported(fixed: dict, cfg: dict) -> dict:
    """What the backtest did, over every trade SQX reported — the databank's own numbers.

    Args:
        fixed: What setting() returned.
        cfg: What config.load() returned.

    Returns:
        What metrics.observed() returned, computed on **all** the trades in close-time order,
        so net profit, drawdown, profit factor and the trade count reconcile with SQX instead
        of being short by whatever the bar grid could not hold. `real()` stays on the located
        subset and is the one the null comparison uses: the real run and its random
        counterparts have to be the same trades or the p-value measures the difference
        between two trade lists.
    """
    return metrics.observed(fixed["all"]["pnl"], cfg["equity"]["starting"])


def exits(fixed: dict) -> list[dict]:
    """How the real trades actually ended, and what each way of ending was worth.

    Args:
        fixed: What setting() returned.

    Returns:
        One row per `Close type` the export carries, with its trade count, its share of the
        trades and its share of the **profit**, largest first. The count alone was already on
        the page and it is the wrong number to read: what matters is how much of the money
        rests on an exit the null can reproduce. `Exit After X Bars` and `End Of Friday
        (Time)` are rules of the bar count and of the calendar, and every model reproduces
        them; `Exit Signal` is not reproducible without reading the `.sqx`, so the p of a
        strategy that carries it is a joint entry-and-exit statement, and this table says how
        much of the result that caveat covers.
    """
    d = fixed["aligned"]
    pnl = d["Profit/Loss"].to_numpy()
    total = np.abs(pnl).sum() or 1.0
    out = []
    for kind, group in d.groupby("Close type", sort=False, observed=False):
        at = d["Close type"].to_numpy() == kind
        out.append({"exit": str(kind), "trades": int(at.sum()),
                    "share": float(at.mean()), "net": float(pnl[at].sum()),
                    "gross_share": float(np.abs(pnl[at]).sum() / total),
                    "reproducible": str(kind) in REPRODUCIBLE})
    return sorted(out, key=lambda r: -r["trades"])


def real(fixed: dict, bars: pd.DataFrame, cfg: dict) -> dict:
    """The real backtest's own statistics and equity curve.

    Args:
        fixed: What setting() returned.
        bars: That market's bars.
        cfg: What config.load() returned.

    Returns:
        Keys stats and curve. `net` here is SQX's own reported profit summed, not a
        reconstruction, so the number on the page is the number in the databank.
    """
    e = cfg["equity"]
    pnl = fixed["pnl"]
    stats = metrics.observed(pnl, e["starting"])
    logret = pricing.realised(bars, fixed["held"], fixed["fill"]["convention"]) - fixed["cost"]
    stats["mean_r"] = float(logret.mean() / fixed["scale"])
    curve = equity.path(pnl[None, :], fixed["held"]["exit"].to_numpy()[None, :],
                        fixed["market"]["n_bars"], e["steps"], e["starting"])
    return {"stats": stats, "curve": curve[0].tolist()}


def diagnostics(fixed: dict, bars: pd.DataFrame, entries: np.ndarray) -> dict:
    """The checks that decide whether a market's result may be believed at all.

    Args:
        fixed: What setting() returned.
        bars: That market's bars.
        entries: One batch of the random runs' entry indices.

    Returns:
        Trade count, how many trades fell off the bar grid, fill error, share of entries on a
        bar open, share of exits at the bar cap and at the Friday close, median hold, cost,
        how much of the real entries' calendar the random runs kept, and the volatility at
        the real entries against the market's own average.
    """
    held, aligned = fixed["held"], fixed["aligned"]
    clock = bars.index.dayofweek.to_numpy() * 24 + bars.index.hour.to_numpy()
    entry_atr = pricing.atr(bars)[held["entry"].to_numpy()]
    kept = (float("nan") if entries.shape[1] != len(held)
            else float(np.mean(clock[entries] == clock[held["entry"].to_numpy()])))
    return {"trades": len(held), "off_grid": fixed["off_grid"],
            "convention": fixed["fill"]["convention"],
            "fill_error": fixed["profile"]["error"],
            "fill_offset": fixed["profile"]["offset"],
            "on_open_price": fixed["profile"]["at_open"],
            # The clock reading, kept because it is what a reader expects to see and because a
            # gap between the two is informative -- but nothing warns on it any more. 🔬 The
            # 4,613 entries of 960,705 stamped mid-bar are priced exactly like the rest.
            "on_bar_open": tradeio.on_bar_open(aligned, bars.index),
            "bar_cap": float((aligned["Close type"] == "Exit After X Bars").mean()),
            "friday_exit": float((aligned["Close type"] == "End Of Friday (Time)").mean()),
            "hold_median": float(held["hold"].median()),
            "cost_rate": fixed["cost"], "point_value": fixed["point_value"],
            "calendar_kept": kept,
            "atr_ratio": float(np.nanmean(entry_atr) / np.nanmean(pricing.atr(bars)))}
