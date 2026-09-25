"""Cost and execution robustness: how much of the edge survives worse fills or a bigger spread."""

from collections.abc import Iterator

import numpy as np
import pandas as pd

from core import trades as tradeio
from studies.transfer.crossmarket.mechanics import equity, pricing
from studies.transfer.crossmarket.simulate import metrics

DEFAULT_MULTIPLES = [1.0, 1.5, 2.0, 2.5, 3.0]
# Runs priced per batch, for the same reason `nulls.chunk` exists: memory, not statistics.
# Unbatched, one market of 600 trades at the shipped 25,000 sims allocated 258 MB in this
# function alone, and the ninety-six workers of a population run do not fit in 125 GB.
CHUNK = 500


def degraded(fixed: dict, s: dict, rng: np.random.Generator
              ) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """The real trades run again under worse execution, many times over, in batches.

    Args:
        fixed: What backtest.setting() returned.
        s: What execution.settings() returned -- config.yaml's stress block, with cost_shock
            and fill_depth calibrated from execution.yaml where that feed is declared.
        rng: Seeded generator.

    Yields:
        (pnl, live) for CHUNK runs at a time: USD per trade and which trades happened, one
        row per run. Three things go wrong at once and each is drawn independently per run:
        a share of trades is simply missed, the whole run's cost is scaled by a multiple
        drawn from a range, and a share of trades gives back part of its own adverse
        excursion. Unlike the null models this keeps the real entries -- it asks what the
        same trades are worth under a worse broker, not whether the entries were any good.

    The three draws are taken whole and in the order they were always taken, so the numbers
    are the ones the unbatched version produced; only the pricing is batched. `live` and
    `worse` are stored as the booleans they are rather than as the float64 they are drawn
    from, which is where eight ninths of this function's memory went.
    """
    sims = s["sims"]
    base, charged = fixed["pnl"], fixed["charged"]
    mae = tradeio.excursions(fixed["aligned"], fixed["point_value"])["mae"].to_numpy()
    mae_usd = np.abs(mae) * fixed["size"]
    shock = rng.uniform(*s["cost_shock"], size=(sims, 1))
    live = np.empty((sims, base.size), dtype=bool)
    worse = np.empty((sims, base.size), dtype=bool)
    for a in range(0, sims, CHUNK):
        b = min(a + CHUNK, sims)
        np.greater_equal(rng.random((b - a, base.size)), s["p_skip"], out=live[a:b])
    for a in range(0, sims, CHUNK):
        b = min(a + CHUNK, sims)
        np.less(rng.random((b - a, base.size)), s["fill_frac"], out=worse[a:b])
    gross = base + charged
    for a in range(0, sims, CHUNK):
        b = min(a + CHUNK, sims)
        pnl = shock[a:b] * charged
        np.subtract(gross, pnl, out=pnl)
        np.subtract(pnl, s["fill_depth"] * mae_usd, out=pnl, where=worse[a:b])
        np.copyto(pnl, 0.0, where=~live[a:b])
        yield pnl, live[a:b]


def simulate(fixed: dict, bars: pd.DataFrame, cfg: dict, s: dict) -> dict:
    """Every statistic and the equity cone of the execution stress.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        cfg: What config.load() returned.
        s: What execution.settings() returned for this market.

    Returns:
        The same table, shapes and cone shape backtest.run() returns, so the panel draws
        both with one renderer. The question is different: the cone here is what a worse
        broker can do to the same trades, not what random timing can.

        Accumulated batch by batch: every statistic here is a function of one run's own row,
        so a batch of rows gives the same numbers a whole matrix of them does.
    """
    e = cfg["equity"]
    rng = np.random.default_rng(cfg["nulls"]["seed"])
    seen = metrics.observed(fixed["pnl"], e["starting"])
    exits = fixed["held"]["exit"].to_numpy()
    parts, cones = [], []
    for pnl, live in degraded(fixed, s, rng):
        closed = np.repeat(exits[None, :], pnl.shape[0], axis=0)
        parts.append(metrics.paths(pnl, live, e["starting"]))
        cones.append(equity.path(pnl, closed, fixed["market"]["n_bars"], e["steps"],
                                 e["starting"]))
    stats = {name: np.concatenate([p[name] for p in parts]) for name in parts[0]}
    curves = np.concatenate(cones)
    observed = equity.path(fixed["pnl"][None, :], exits[None, :],
                           fixed["market"]["n_bars"], e["steps"], e["starting"])[0]
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
