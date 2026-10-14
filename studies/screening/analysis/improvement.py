"""What an in-sample filter buys out of sample, and how many strategies it costs to get it."""

import os
from typing import TypedDict

import numpy as np

from core import fanout

CUTS = (5, 10, 20, 30, 50)
MIN_SURVIVORS = 200
DRAWS = 2000
ALPHA = 0.05
ROWS = 250      # resamples drawn at a time in _resampled: memory only, same draws
SEED = 20260904

# What the sweep's workers read, set before the fork.
_SHARED: dict = {}


def breakeven(target: str) -> float:
    """The value of an out-of-sample metric that separates a winning strategy from a losing one.

    Args:
        target: Full column name, e.g. "Sharpe Ratio (OOS)".

    Returns:
        1.0 for profit factor, which is a ratio of gains to losses; 0.0 for everything else
        here, since Sharpe, Ret/DD and net profit all go negative when a strategy loses.
    """
    return 1.0 if target.startswith("Profit factor") else 0.0


def candidates(is_metrics: list[str]) -> list[dict]:
    """Every filter the sweep tries.

    Args:
        is_metrics: Full names of the in-sample columns to cut on.

    Returns:
        One dict per candidate with metric, side ("top" keeps the highest values, "bottom" the
        lowest) and cut, the percent of the population kept. Both directions are always tried:
        the count of candidates is the search space the correction below has to cover.
    """
    return [{"metric": m, "side": s, "cut": c}
            for m in is_metrics for s in ("top", "bottom") for c in CUTS]


def label(candidate: dict) -> str:
    """Name of one candidate, unique within a sweep.

    Args:
        candidate: One entry from candidates().

    Returns:
        A string such as "Sharpe Ratio (IS) top 20%".
    """
    return f"{candidate['metric']} {candidate['side']} {candidate['cut']}%"


def survivors(column: np.ndarray, candidate: dict) -> np.ndarray:
    """Which strategies one candidate filter keeps.

    Args:
        column: The in-sample metric, one value per strategy.
        candidate: One entry from candidates().

    Returns:
        Boolean mask over the full population. The cut is a quantile of the whole population,
        never of some earlier filter's survivors.
    """
    if candidate["side"] == "top":
        return column >= np.quantile(column, 1 - candidate["cut"] / 100)
    return column <= np.quantile(column, candidate["cut"] / 100)


class Outcome(TypedDict):
    """How one set of strategies did out of sample: size, median and share above break-even."""
    n: int
    median: float
    hit: float


class Lift(TypedDict):
    """The bootstrapped improvement of the survivors over the population."""
    d_median: float
    d_median_lo: float
    d_median_hi: float
    d_hit: float
    d_hit_lo: float
    d_hit_hi: float
    p: float


class Judged(Outcome, Lift):
    """One candidate's outcome and lift."""


def outcome(y: np.ndarray, level: float) -> Outcome:
    """How one set of strategies did out of sample.

    Args:
        y: The out-of-sample target, one value per strategy in the set.
        level: Break-even from breakeven().

    Returns:
        Keys n, median and hit, the share of the set strictly above break-even.
    """
    return Outcome(n=int(y.size), median=float(np.median(y)), hit=float((y > level).mean()))


def reach(tests: int) -> int:
    """Resamples a filter needs before its p can go under Benjamini-Hochberg's first rung.

    Args:
        tests: Filters judged together, the family the correction covers.

    Returns:
        The first multiple of DRAWS strictly above tests / ALPHA: the bootstrap p cannot go
        below one over its resamples, and the lone best of the family is named only at
        p <= ALPHA / tests. 🔬 2026-10-04: at 2,000 resamples and 210 filters the floor
        (0.0005) sat above that rung (0.00024), so fewer than three filters on the floor
        were never named, however strong.
    """
    return DRAWS * (round(tests / ALPHA) // DRAWS + 1)


def _resampled(rng: np.random.Generator, kept: np.ndarray, level: float,
               draws: int) -> tuple[np.ndarray, np.ndarray]:
    """The median and the hit rate of `draws` resamples of the survivors, one block.

    Drawn ROWS resamples at a time: the generator hands out the same indices, and the
    draws x survivors matrix (660 MB at 2,000 x 10,000) is never whole.
    """
    median, hit = np.empty(draws), np.empty(draws)
    for done in range(0, draws, ROWS):
        rows = min(ROWS, draws - done)
        draw = kept[rng.integers(0, kept.size, (rows, kept.size))]
        median[done:done + rows] = np.median(draw, axis=1)
        hit[done:done + rows] = (draw > level).mean(axis=1)
    return median, hit


def lift(y: np.ndarray, mask: np.ndarray, level: float, draws: int = DRAWS,
         reach: int = DRAWS) -> Lift:
    """Bootstrap the improvement of the survivors over the whole population.

    Args:
        y: The out-of-sample target for every strategy.
        mask: Survivor mask from survivors().
        level: Break-even from breakeven().
        draws: Resamples of the survivors.
        reach: Resamples a filter is taken to, in blocks of `draws`, when none of its first
            `draws` puts the median on the other side of the population's: from reach().

    Returns:
        d_median and d_hit, survivors minus population, each with a 95% interval as
        d_median_lo/hi and d_hit_lo/hi, plus p, the two-sided bootstrap p-value of d_median,
        never below one over the resamples drawn. A filter that is not extended returns
        exactly what `draws` resamples give; an extended one reads interval and p off all.

    The interval is on the difference, because two separate overlapping intervals would not
    mean the difference is indistinguishable from zero. Only the survivors are resampled: the
    population baseline is the whole export and its own sampling error is an order of
    magnitude smaller than that of any subset the sweep keeps.
    """
    rng = np.random.default_rng(SEED)
    kept = y[mask]
    base = outcome(y, level)
    blocks = [_resampled(rng, kept, level, draws)]
    first = blocks[0][0] - base["median"]
    if not min((first <= 0).sum(), (first >= 0).sum()):
        blocks += [_resampled(rng, kept, level, draws) for _ in range(reach // draws - 1)]
    d_median = np.concatenate([b[0] for b in blocks]) - base["median"]
    d_hit = np.concatenate([b[1] for b in blocks]) - base["hit"]
    tail = min(float((d_median <= 0).mean()), float((d_median >= 0).mean()))
    return Lift(d_median=float(np.median(kept) - base["median"]),
                d_median_lo=float(np.quantile(d_median, 0.025)),
                d_median_hi=float(np.quantile(d_median, 0.975)),
                d_hit=float((kept > level).mean() - base["hit"]),
                d_hit_lo=float(np.quantile(d_hit, 0.025)),
                d_hit_hi=float(np.quantile(d_hit, 0.975)),
                p=max(2 * tail, 1 / d_median.size))


def _judged(i: int) -> Judged:
    """One candidate's outcome and lift, in a worker that inherited the columns by fork.

    Args:
        i: Its position in the judged list.

    Returns:
        The keys from outcome() and those from lift().
    """
    columns, y, level = _SHARED["columns"], _SHARED["y"], _SHARED["level"]
    candidate = _SHARED["judged"][i]
    mask = survivors(columns[candidate["metric"]], candidate)
    return Judged(**outcome(y[mask], level), **lift(y, mask, level, reach=reach(len(_SHARED["judged"]))))


def sweep(columns: dict[str, np.ndarray], is_metrics: list[str], target: str,
          min_n: int = MIN_SURVIVORS) -> list[dict]:
    """Measure every candidate filter against one out-of-sample outcome.

    Args:
        columns: Numeric columns from analysis.metrics.load.
        is_metrics: Full names of the in-sample columns to cut on.
        target: Full name of the out-of-sample column to improve.
        min_n: Survivors a candidate must leave to be judged at all.

    Returns:
        One row per judged candidate, sorted by descending d_median, carrying metric (the
        label, unique so engines.inference.fdr.discoveries can key on it), column, side, cut, the keys
        from outcome() and those from lift(). Candidates leaving fewer than min_n survivors
        are dropped without being tested, so they never enter the family the correction covers.
        A filter on the floor of its first DRAWS resamples is redrawn to reach(judged), so
        the rows are meant for fdr.discoveries at ALPHA.
    """
    y, level = columns[target], breakeven(target)
    judged = [c for c in candidates(is_metrics)
              if survivors(columns[c["metric"]], c).sum() >= min_n]
    _SHARED.update(columns=columns, y=y, level=level, judged=judged)
    # Every lift() reseeds its own generator, so a candidate's numbers do not depend on
    # which process ran it: the parallel sweep returns exactly the serial one's rows.
    got = dict(fanout.run(_judged, {i: int(survivors(columns[c["metric"]], c).sum())
                                    for i, c in enumerate(judged)}, os.cpu_count() or 1))
    for i, c in enumerate(judged):
        got[i] = {"metric": label(c), "column": c["metric"], "side": c["side"],
                  "cut": c["cut"], **got[i]}
    rows = [got[i] for i in range(len(judged))]
    return sorted(rows, key=lambda r: -r["d_median"])
