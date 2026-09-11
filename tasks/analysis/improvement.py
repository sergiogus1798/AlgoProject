"""What an in-sample filter buys out of sample, and how many strategies it costs to get it."""

import numpy as np

CUTS = (5, 10, 20, 30, 50)
MIN_SURVIVORS = 200
DRAWS = 2000
SEED = 20260904


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


def outcome(y: np.ndarray, level: float) -> dict:
    """How one set of strategies did out of sample.

    Args:
        y: The out-of-sample target, one value per strategy in the set.
        level: Break-even from breakeven().

    Returns:
        Keys n, median and hit, the share of the set strictly above break-even.
    """
    return {"n": int(y.size), "median": float(np.median(y)), "hit": float((y > level).mean())}


def lift(y: np.ndarray, mask: np.ndarray, level: float, draws: int = DRAWS) -> dict:
    """Bootstrap the improvement of the survivors over the whole population.

    Args:
        y: The out-of-sample target for every strategy.
        mask: Survivor mask from survivors().
        level: Break-even from breakeven().
        draws: Resamples of the survivors.

    Returns:
        d_median and d_hit, survivors minus population, each with a 95% interval as
        d_median_lo/hi and d_hit_lo/hi, plus p, the two-sided bootstrap p-value of d_median.

    The interval is on the difference, because two separate overlapping intervals would not
    mean the difference is indistinguishable from zero. Only the survivors are resampled: the
    population baseline is the whole export and its own sampling error is an order of
    magnitude smaller than that of any subset the sweep keeps.
    """
    rng = np.random.default_rng(SEED)
    kept = y[mask]
    base = outcome(y, level)
    draw = kept[rng.integers(0, kept.size, (draws, kept.size))]
    d_median = np.median(draw, axis=1) - base["median"]
    d_hit = (draw > level).mean(axis=1) - base["hit"]
    tail = min(float((d_median <= 0).mean()), float((d_median >= 0).mean()))
    return {"d_median": float(np.median(kept) - base["median"]),
            "d_median_lo": float(np.quantile(d_median, 0.025)),
            "d_median_hi": float(np.quantile(d_median, 0.975)),
            "d_hit": float((kept > level).mean() - base["hit"]),
            "d_hit_lo": float(np.quantile(d_hit, 0.025)),
            "d_hit_hi": float(np.quantile(d_hit, 0.975)),
            "p": max(2 * tail, 1 / draws)}


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
        label, unique so correlations.discoveries can key on it), column, side, cut, the keys
        from outcome() and those from lift(). Candidates leaving fewer than min_n survivors
        are dropped without being tested, so they never enter the family the correction covers.
    """
    y, level = columns[target], breakeven(target)
    rows = []
    for candidate in candidates(is_metrics):
        mask = survivors(columns[candidate["metric"]], candidate)
        if mask.sum() < min_n:
            continue
        row = {"metric": label(candidate), "column": candidate["metric"],
               "side": candidate["side"], "cut": candidate["cut"]}
        row.update(outcome(y[mask], level))
        row.update(lift(y, mask, level))
        rows.append(row)
    return sorted(rows, key=lambda r: -r["d_median"])
