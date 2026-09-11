"""Run one strategy's real trades and its random counterparts on one market, under a given model."""

import numpy as np
import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import envelope, pricing, trade_models

SEED = 20260908     # fixed and shared across markets, so one draw is one displacement everywhere
BLOCK_MONTHS = 6    # regime blocks; six months keeps enough trades in each to move them


def score(entries: np.ndarray, holds: np.ndarray, enter_px: np.ndarray, leave_px: np.ndarray,
          cost: float) -> np.ndarray:
    """Mean log return per trade of each run, net of cost.

    Args:
        entries: A (runs, trades) array of entry bar indices.
        holds: Bars held, same shape.
        enter_px: Fill price for an entry on each bar.
        leave_px: Fill price for an exit on each bar.
        cost: Round-turn cost as a fraction of price.

    Returns:
        One mean per run. A trade whose exit would fall past the last bar is dropped from its
        own run's mean rather than clipped, which would score it as flat.
    """
    out = entries + holds
    valid = out < leave_px.size
    ret = np.where(valid, np.log(leave_px[np.where(valid, out, 0)] / enter_px[entries]) - cost,
                   np.nan)
    return np.nanmean(ret, axis=1)


def setting(trades: pd.DataFrame, bars: pd.DataFrame) -> dict:
    """Fix how this market is priced, before anything random is drawn.

    Args:
        trades: One market's real trades.
        bars: That market's bars.

    Returns:
        The bar locations of the real trades, the fill convention that reproduced SQX, the
        prices, the cost and the scale. The convention is re-derived per market rather than
        assumed: real and random runs must be priced identically or the comparison measures
        the gap between two pricers instead of the timing.
    """
    held = envelope.occupancy(trades, bars)
    aligned = trades.loc[held.index]
    best = pricing.reconcile(aligned, bars, held)[0]
    enter_col, leave_col = pricing.CONVENTIONS[best["convention"]]
    value = pricing.point_value(aligned)
    return {"held": held, "aligned": aligned, "fill": best, "point_value": value,
            "enter_px": bars[enter_col].to_numpy(), "leave_px": bars[leave_col].to_numpy(),
            "cost": pricing.cost_rate(aligned, value), "scale": pricing.unit(bars),
            "market": envelope.describe(bars, held, BLOCK_MONTHS)}


def diagnostics(fixed: dict, bars: pd.DataFrame, entries: np.ndarray) -> dict:
    """The checks that decide whether a market's result may be believed at all.

    Args:
        fixed: What setting() returned.
        bars: That market's bars.
        entries: The random runs' entry indices.

    Returns:
        Trade count, fill error, share of entries on a bar open, share of exits at the bar cap,
        median hold, cost, how much of the real entries' calendar the random runs kept, and the
        volatility at the real entries against the market's own average.
    """
    held, aligned = fixed["held"], fixed["aligned"]
    clock = bars.index.dayofweek.to_numpy() * 24 + bars.index.hour.to_numpy()
    entry_atr = pricing.atr(bars)[held["entry"].to_numpy()]
    return {"trades": len(held),
            "convention": fixed["fill"]["convention"],
            "fill_error": fixed["fill"]["entry_median"] + fixed["fill"]["exit_median"],
            "on_bar_open": tradeio.on_bar_open(aligned, bars.index),
            "bar_cap": float((aligned["Close type"] == "Exit After X Bars").mean()),
            "hold_median": float(held["hold"].median()),
            "cost_rate": fixed["cost"],
            "point_value": fixed["point_value"],
            "calendar_kept": float(np.mean(clock[entries] == clock[held["entry"].to_numpy()])),
            "atr_ratio": float(np.nanmean(entry_atr) / np.nanmean(pricing.atr(bars)))}


def run(trades: pd.DataFrame, bars: pd.DataFrame, draws: int, model: str) -> dict:
    """The real run and `draws` random ones on one market, all priced identically.

    Args:
        trades: One market's real trades.
        bars: That market's bars.
        draws: How many random runs.
        model: A key of trade_models.MODELS, which decides what is randomised.

    Returns:
        Keys real, null and the diagnostics, all in the market's own scale so markets compare.
        No p-value: judging these numbers is inference's job, and keeping the two apart is what
        lets the same runs be re-judged, or the same judgement re-run under another model.
    """
    fixed = setting(trades, bars)
    rng = np.random.default_rng(SEED)
    entries, holds = trade_models.MODELS[model](fixed["held"], fixed["market"], draws, rng)
    real = float(np.mean(pricing.realised(bars, fixed["held"], fixed["fill"]["convention"])
                         - fixed["cost"]))
    null = score(entries, holds, fixed["enter_px"], fixed["leave_px"], fixed["cost"])
    return {"model": model, "real": real / fixed["scale"], "null": null / fixed["scale"],
            **diagnostics(fixed, bars, entries),
            **trade_models.goodness(fixed["held"], fixed["market"]["gaps"])}
