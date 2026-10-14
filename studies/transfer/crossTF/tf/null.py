"""The joint random runs of one mother and her siblings in one window, and the three measures read off them: e, z of a total, z of the difference."""

from typing import cast

import numpy as np
import pandas as pd

from engines.market import reprice
from studies.transfer.crossmarket.travel import cells, shift, stat, tensor


def calendar(
    first: pd.Timestamp, last: pd.Timestamp, cuts: dict, null: dict
) -> tuple[pd.DataFrame, np.ndarray]:
    """The calendar cells and every run's shift of each, drawn once for a whole batch.

    Args:
        first, last: The earliest and the latest bar read.
        cuts: `build`, `oos1` and `end`, as travel's `cells.cuts` returns them: a cell is split
            there, so no shift crosses from one window to the other and 2011 starts at `build`.
        null: tf.runs of config.yaml.

    Returns:
        (cells, shifts): travel's cells table and its (runs, cells) whole steps. The draw is
        keyed by the cell's date and the seed, never by a strategy or a timeframe: run b moves
        2014 by the same weeks for the mother and every sibling of every mother.
    """
    cal = cells.table(first, last, cuts, null["shift_unit"], null["shift_step"])
    return cal, shift.draws(cal, null["seed"], null["draws"])


def grids(
    bars: dict[str, pd.DataFrame],
    costs: reprice.Costs,
    params: dict,
    cal: pd.DataFrame,
    shifts: np.ndarray,
    span: tuple[pd.Timestamp, pd.Timestamp],
    null: dict,
) -> dict[str, tensor.Market]:
    """What pricing needs of every timeframe inside one window, shared by every mother.

    Args:
        bars: {timeframe: the asset's bars}, indexed by bar open time.
        costs: The asset's costs at that window's segment, as `reprice.costs` returns them.
        params: The doctrine's money management (`Amount`, `ATRPeriod`, `ATRMult`).
        cal, shifts: As calendar() returns them.
        span: The window, [start, end).
        null: tf.runs.

    Returns:
        {timeframe: travel's `tensor.market`} on the bars cut to the window, so no moved trade
        opens or closes outside it. A calendar cell with a hole in the data in ANY timeframe
        (`tensor.exclude`) is left out of all of them: a mother and her sibling are only ever
        compared over the same years.
    """
    with np.errstate(
        divide="ignore"
    ):  # lots on a flat bar are inf: `usable` never sizes there
        out = {
            tf: tensor.market(
                cast(pd.DataFrame, b[(b.index >= span[0]) & (b.index < span[1])]),
                costs,
                params,
                cal,
                null["flat_atr_fraction"],
            )
            for tf, b in bars.items()
        }
    gone = np.any(
        [
            tensor.exclude(
                m, cal, shifts, null["shift_step"], null["max_displaced_share"]
            )
            for m in out.values()
        ],
        axis=0,
    )
    for m in out.values():
        m["data"] = m["data"] & ~gone
    return out


def runs(
    trades: dict[str, pd.DataFrame],
    grid: dict[str, tensor.Market],
    cal: pd.DataFrame,
    shifts: np.ndarray,
    null: dict,
) -> dict[str, dict]:
    """One mother and her siblings through the same random runs, in one window.

    Args:
        trades: {timeframe: that member's trades}, SQX's `Open time`, `Close time`, `Type`;
            the mother under her own timeframe. SQX's sizes and P/L are not read.
        grid: As grids() returns it; only the timeframes in `trades` are priced.
        cal, shifts: As calendar() returns them.
        null: tf.runs; `judge_on` picks what `real` and `null` hold.

    Returns:
        {timeframe: cell}, a cell being `n` (real trades closed in the window), `real` and
        `null` (the total in R and one total per run, on the judged quantity) and `real_net`,
        `null_net` (the same on net R). Row b of every timeframe's `null` is the SAME run.
    """
    one = tensor.build(
        trades,
        {tf: grid[tf] for tf in trades},
        cal,
        shifts,
        null["shift_step"],
        null["judge_on"],
    )
    return {
        tf: {
            "n": float(stat.total(one["trades"], [j])),
            **{
                k: stat.total(one[k], [j])
                for k in ("real", "null", "real_net", "null_net")
            },
        }
        for j, tf in enumerate(one["markets"])
    }


def edge(cell: dict) -> float:
    """e: what a trade earns over the same trades entered at random, in net R per trade.

    Args:
        cell: One timeframe's entry of runs().

    Returns:
        (T_real - mean T_random) / n; NaN when the cell has no trade.
    """
    return (
        float((cell["real_net"] - np.mean(cell["null_net"])) / cell["n"])
        if cell["n"] > 0
        else np.nan
    )


def z_total(cell: dict) -> float:
    """z of the cell's total against its random runs (z_build when the window is the build)."""
    return stat.z(float(cell["real"]), cell["null"])["z"] if cell["n"] > 0 else np.nan


def delta(mother: dict, sibling: dict) -> tuple[float, np.ndarray] | None:
    """delta = e_mother - e_sibling, per trade on the judged quantity: the real one and every run's.

    Args:
        mother, sibling: Their entries of ONE runs() call, so the runs are paired.

    Returns:
        (real, one per run); None when either has no trade.
    """
    if not (mother["n"] > 0 and sibling["n"] > 0):
        return None
    per_trade = lambda key: mother[key] / mother["n"] - sibling[key] / sibling["n"]
    return float(per_trade("real")), per_trade("null")


def z_delta(mother: dict, sibling: dict) -> float:
    """z of delta = e_mother - e_sibling against the same difference in every joint run.

    Args:
        mother, sibling: Their entries of ONE runs() call, so the runs are paired.

    Returns:
        (delta_real - mean delta_random) / sd(delta_random), on the judged quantity: the
        correlation between the two is inside the sd, nothing is estimated apart. NaN when
        either has no trade or the difference does not vary.
    """
    got = delta(mother, sibling)
    if got is None:
        return np.nan
    real, runs = got
    if real == 0 and not runs.any():
        return 0.0  # the sibling IS her mother: no difference in any run, not «no data»
    return stat.z(real, runs)["z"]
