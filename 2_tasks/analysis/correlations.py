"""Correlate in-sample metrics against out-of-sample outcomes, and say which results survive."""

import numpy as np
from scipy import stats


def correlate(x: np.ndarray, y: np.ndarray) -> dict:
    """Pearson and Spearman correlation between two metric columns.

    Args:
        x, y: One value per strategy, same length.

    Returns:
        Keys pearson, spearman, p and n, where p is the Spearman two-tailed p-value.
        Spearman is the one to trust here: these metrics are heavy-tailed and a single
        blow-up strategy dominates Pearson.
    """
    spearman = stats.spearmanr(x, y)
    return {"pearson": float(stats.pearsonr(x, y).statistic),
            "spearman": float(spearman.statistic),
            "p": float(spearman.pvalue),
            "n": int(len(x))}


def critical_r(n: int, alpha: float = 0.05) -> float:
    """Smallest |r| that is significant on its own at the given level.

    Args:
        n: Sample size.
        alpha: Two-tailed significance level.

    Returns:
        The critical correlation. At n=10,000 it is around 0.02, which is why passing it
        means almost nothing here and discoveries() is the threshold that matters.
    """
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    return float(t / np.sqrt(n - 2 + t ** 2))


def discoveries(rows: list[dict], alpha: float = 0.05) -> set[str]:
    """Which of a family of tests survive Benjamini-Hochberg control of the FDR.

    Args:
        rows: One dict per test, each carrying "metric" and "p".
        alpha: False discovery rate to hold across the whole family.

    Returns:
        The metric names that survive. Every in-sample metric is tested against the same
        outcome at once, so the plain 5% level would be expected to hand back one false
        positive in every twenty metrics tested.
    """
    ordered = sorted(rows, key=lambda r: r["p"])
    below = [i for i, r in enumerate(ordered, 1) if r["p"] <= i / len(rows) * alpha]
    return {r["metric"] for r in ordered[: max(below, default=0)]}


def persistence(columns: dict[str, np.ndarray], names: list[str]) -> list[dict]:
    """How well each metric keeps its own value from in-sample to out-of-sample.

    Args:
        columns: Numeric columns from analysis.metrics.load.
        names: Bare metric names present at both sample types.

    Returns:
        One dict per metric with metric, is_mean, oos_mean and decay (OOS mean over IS
        mean) plus the keys from correlate, sorted by descending absolute Spearman.
    """
    rows = []
    for m in names:
        x, y = columns[f"{m} (IS)"], columns[f"{m} (OOS)"]
        row = {"metric": m, "is_mean": float(x.mean()), "oos_mean": float(y.mean()),
               "decay": float(y.mean() / x.mean())}
        row.update(correlate(x, y))
        rows.append(row)
    return sorted(rows, key=lambda r: -abs(r["spearman"]))


def predictors(columns: dict[str, np.ndarray], target: str,
               sources: list[str]) -> list[dict]:
    """Rank every in-sample metric by how well it predicts one out-of-sample outcome.

    Args:
        columns: Numeric columns from analysis.metrics.load.
        target: Full name of the OOS column to predict, e.g. "Profit factor (OOS)".
        sources: Full names of the IS columns to test against it.

    Returns:
        One dict per metric with metric plus the keys from correlate, sorted by
        descending absolute Spearman.
    """
    y = columns[target]
    rows = [dict(metric=m, **correlate(columns[m], y)) for m in sources]
    return sorted(rows, key=lambda r: -abs(r["spearman"]))
