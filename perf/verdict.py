"""What counts as a regression. Reads the catalogue, judges it, and computes nothing itself."""

import pandas as pd

REGRESSION, IMPROVEMENT, STEADY, NOISY, FIRST = (
    "regression", "improvement", "steady", "noisy", "first")
# Rows written before the budget column existed were all taken at the config default, so
# that is what a blank means. It is an interpretation of old rows, never a rewrite of them.
DEFAULT_BUDGET = 5000


def _call(change: float, spread: float, limit: float) -> str:
    """Name one change.

    Args:
        change: Percent difference from the previous measurement, positive being slower.
        spread: How far this measurement's own repeats sat apart, in percent.
        limit: The threshold from config.

    Returns:
        One of the five verdicts. A change smaller than the run's own spread is called
        noisy rather than steady: the measurement cannot see a difference that size, and
        saying "steady" would claim knowledge it does not have.
    """
    if abs(change) < limit:
        return STEADY if abs(change) >= spread else NOISY
    return REGRESSION if change > 0 else IMPROVEMENT


def compare(frame: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Every target's latest measurement against the one before it.

    Args:
        frame: What store.history() returned.
        cfg: What config.load() returned.

    Returns:
        One row per target: the two times, the change in percent, the change in peak memory
        and the verdict. Times are compared **per unit of work**, so an export that grew
        from 500 to 3,000 trades does not read as code that got six times slower.

        Only rows measured at the same simulation budget are compared. `--set
        sample.n_sims=...` changes how much work a target does without changing its scale,
        and comparing across budgets reported a five-fold rise in cost as a regression.
    """
    rows = []
    for target, group in frame.groupby("target", sort=False):
        last = group.iloc[-1]
        group = group[group["budget"].fillna(DEFAULT_BUDGET)
                      == (last["budget"] if last["budget"] == last["budget"] else DEFAULT_BUDGET)]
        if len(group) < 2:
            rows.append({"target": target, "wall_s": last["wall_s"], "verdict": FIRST,
                         "wall_pct": 0.0, "rss_pct": 0.0, "prev_wall_s": float("nan")})
            continue
        prev = group.iloc[-2]
        per_now, per_was = last["wall_s"] / last["scale"], prev["wall_s"] / prev["scale"]
        change = (per_now / per_was - 1) * 100
        rss = (last["rss_peak_mb"] / prev["rss_peak_mb"] - 1) * 100
        verdict = (NOISY if last["wall_s"] < cfg["regression"]["min_wall_s"]
                   else _call(change, last["wall_spread_pct"], cfg["regression"]["wall_pct"]))
        if verdict in (STEADY, NOISY) and rss > cfg["regression"]["rss_pct"]:
            verdict = REGRESSION
        rows.append({"target": target, "wall_s": last["wall_s"], "prev_wall_s": prev["wall_s"],
                     "wall_pct": change, "rss_pct": rss, "verdict": verdict})
    return pd.DataFrame(rows)


def failing(judged: pd.DataFrame) -> pd.DataFrame:
    """Only what got worse.

    Args:
        judged: What compare() returned.

    Returns:
        The regressions, worst first. This is what a caller exits non-zero on.
    """
    return judged[judged["verdict"] == REGRESSION].sort_values("wall_pct", ascending=False)
