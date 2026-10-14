"""Correlate in-sample metrics against out-of-sample outcomes, and say which results survive."""

from typing import Any, TypedDict, cast

import numpy as np
from scipy import stats


class Correlation(TypedDict):
    """Pearson, Spearman, the Spearman p-value and the sample size of two columns."""
    pearson: float
    spearman: float
    p: float
    n: int


def correlate(x: np.ndarray, y: np.ndarray) -> Correlation:
    """Pearson and Spearman correlation between two metric columns.

    Args:
        x, y: One value per strategy, same length.

    Returns:
        Keys pearson, spearman, p and n, where p is the Spearman two-tailed p-value.
        Spearman is the one to trust here: these metrics are heavy-tailed and a single
        blow-up strategy dominates Pearson.
    """
    spearman, pearson = cast(Any, stats.spearmanr(x, y)), cast(Any, stats.pearsonr(x, y))  # scipy stubs lack .statistic
    return Correlation(pearson=float(pearson.statistic), spearman=float(spearman.statistic),
                       p=float(spearman.pvalue), n=int(len(x)))


class Persistence(Correlation):
    """A metric's in-sample and out-of-sample means, their ratio and the correlation."""
    metric: str
    is_mean: float
    oos_mean: float
    decay: float


class Predictor(Correlation):
    """A metric and how well it predicts one outcome."""
    metric: str


def critical_r(n: int, alpha: float = 0.05) -> float:
    """Smallest |r| that is significant on its own at the given level.

    Args:
        n: Sample size.
        alpha: Two-tailed significance level.

    Returns:
        The critical correlation. At n=10,000 it is around 0.02, which is why passing it
        means almost nothing here and engines.inference.fdr.discoveries() is the threshold that matters.
    """
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    return float(t / np.sqrt(n - 2 + t ** 2))


def persistence(columns: dict[str, np.ndarray], names: list[str]) -> list[Persistence]:
    """How well each metric keeps its own value from in-sample to out-of-sample.

    Args:
        columns: Numeric columns from analysis.metrics.load.
        names: Bare metric names present at both sample types.

    Returns:
        One dict per metric with metric, is_mean, oos_mean and decay (OOS mean over IS
        mean) plus the keys from correlate, sorted by descending absolute Spearman.
    """
    rows: list[Persistence] = []
    for m in names:
        x, y = columns[f"{m} (IS)"], columns[f"{m} (OOS)"]
        rows.append(Persistence(metric=m, is_mean=float(x.mean()), oos_mean=float(y.mean()),
                                decay=float(y.mean() / x.mean()), **correlate(x, y)))
    return sorted(rows, key=lambda r: -abs(r["spearman"]))


def predictors(columns: dict[str, np.ndarray], target: str,
               sources: list[str]) -> list[Predictor]:
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
    rows = [Predictor(metric=m, **correlate(columns[m], y)) for m in sources]
    return sorted(rows, key=lambda r: -abs(r["spearman"]))
