"""Cost and execution robustness: how much of the edge survives worse fills or a bigger spread."""

import numpy as np
import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import equity, metrics, pricing

DEFAULT_MULTIPLES = [1.0, 1.5, 2.0, 2.5, 3.0]


def degraded(fixed: dict, cfg: dict, rng: np.random.Generator) -> tuple[np.ndarray, ...]:
    """The real trades run again under worse execution, many times over.

    Args:
        fixed: What backtest.setting() returned.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        (pnl, live): USD per trade and which trades happened, one row per run. Three things
        go wrong at once and each is drawn independently per run: a share of trades is simply
        missed, the whole run's cost is scaled by a multiple drawn from a range, and a share
        of trades gives back part of its own adverse excursion. Unlike the null models this
        keeps the real entries — it asks what the same trades are worth under a worse broker,
        not whether the entries were any good.
    """
    s, sims = cfg["stress"], cfg["stress"]["sims"]
    base, charged = fixed["pnl"], fixed["charged"]
    mae = tradeio.excursions(fixed["aligned"], fixed["point_value"])["mae"].to_numpy()
    mae_usd = np.abs(mae) * fixed["size"]
    shock = rng.uniform(*s["cost_shock"], size=(sims, 1))
    live = rng.random((sims, base.size)) >= s["p_skip"]
    worse = rng.random((sims, base.size)) < s["fill_frac"]
    pnl = base + charged - shock * charged - np.where(worse, s["fill_depth"] * mae_usd, 0.0)
    return np.where(live, pnl, 0.0), live


def simulate(fixed: dict, bars: pd.DataFrame, cfg: dict) -> dict:
    """Every statistic and the equity cone of the execution stress.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        cfg: What config.load() returned.

    Returns:
        The same table, shapes and cone shape backtest.run() returns, so the panel draws
        both with one renderer. The question is different: the cone here is what a worse
        broker can do to the same trades, not what random timing can.
    """
    e = cfg["equity"]
    rng = np.random.default_rng(cfg["nulls"]["seed"])
    pnl, live = degraded(fixed, cfg, rng)
    seen = metrics.observed(fixed["pnl"], e["starting"])
    stats = metrics.paths(pnl, live, e["starting"])
    closed = np.repeat(fixed["held"]["exit"].to_numpy()[None, :], pnl.shape[0], axis=0)
    curves = equity.path(pnl, closed, fixed["market"]["n_bars"], e["steps"], e["starting"])
    observed = equity.path(fixed["pnl"][None, :], closed[:1], fixed["market"]["n_bars"],
                           e["steps"], e["starting"])[0]
    return {"table": metrics.table(stats, seen, e["percentiles"]),
            "shapes": metrics.shapes(stats, seen),
            "cone": {"bands": equity.bands(curves, e["bands"]),
                     "observed": observed.tolist(), "dates": equity.dates(bars, e["steps"])}}


def cost_gradient(fixed: dict, bars: pd.DataFrame, multiples: list[float] = DEFAULT_MULTIPLES
                  ) -> pd.DataFrame:
    """Mean net return at each cost multiple.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        multiples: Cost multipliers to evaluate.

    Returns:
        Columns multiple and mean_return. Linear in the multiple, since gross return per
        trade does not depend on the cost assumption.
    """
    gross = pricing.realised(bars, fixed["held"], fixed["fill"]["convention"])
    mean_gross = float(gross.mean())
    return pd.DataFrame({"multiple": multiples,
                         "mean_return": [mean_gross - m * fixed["cost"] for m in multiples]})


def breakeven_multiple(fixed: dict, bars: pd.DataFrame) -> float:
    """The cost multiple at which the mean net return crosses zero.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.

    Returns:
        mean(gross) / cost. Closed form because the net return is linear in the multiple.
        The PDF's gate requires this at or above 2x.
    """
    gross = pricing.realised(bars, fixed["held"], fixed["fill"]["convention"])
    return float(gross.mean() / fixed["cost"])


def bar_shift_stress(fixed: dict, bars: pd.DataFrame, shift: int) -> float:
    """Decay in mean return when entry and exit are moved by a fixed number of bars.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        shift: Bars to move both entry and exit by.

    Returns:
        Fractional change in mean net return versus the real trades: negative means decay.
        Trades whose shifted entry or exit would fall outside the bar file are dropped.
    """
    held = fixed["held"]
    entry, exit_ = held["entry"].to_numpy() + shift, held["exit"].to_numpy() + shift
    keep = (entry >= 0) & (exit_ < len(bars))
    enter_col, leave_col = pricing.CONVENTIONS[fixed["fill"]["convention"]]
    shifted = (np.log(bars[leave_col].to_numpy()[exit_[keep]]
                      / bars[enter_col].to_numpy()[entry[keep]]) - fixed["cost"])
    real = pricing.realised(bars, held, fixed["fill"]["convention"])[keep] - fixed["cost"]
    return float(shifted.mean() / real.mean() - 1)


def range_slippage_stress(fixed: dict, bars: pd.DataFrame, fraction: float) -> float:
    """Decay in mean return when entries and exits slip against the position.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        fraction: Share of the bar's High-Low range added against the trade at both ends.

    Returns:
        Fractional change in mean net return versus the real trades. Long-only: entry moves
        up by fraction * range, exit moves down by fraction * range of its own bar.
    """
    held = fixed["held"]
    entry_range = (bars["High"] - bars["Low"]).to_numpy()[held["entry"].to_numpy()]
    exit_range = (bars["High"] - bars["Low"]).to_numpy()[held["exit"].to_numpy()]
    enter_col, leave_col = pricing.CONVENTIONS[fixed["fill"]["convention"]]
    enter_px = bars[enter_col].to_numpy()[held["entry"].to_numpy()] + fraction * entry_range
    leave_px = bars[leave_col].to_numpy()[held["exit"].to_numpy()] - fraction * exit_range
    slipped = np.log(leave_px / enter_px) - fixed["cost"]
    real = pricing.realised(bars, held, fixed["fill"]["convention"]) - fixed["cost"]
    return float(slipped.mean() / real.mean() - 1)
