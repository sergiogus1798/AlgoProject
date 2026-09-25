"""The random-filter benchmark: is a filter better than dropping the same share at random?"""

import numpy as np
import pandas as pd

STATISTICS = {
    # Both are per trade on purpose. A filter changes the trade count, so total profit
    # compares two different sample sizes and always flatters the version that trades more.
    "expectancy": lambda pnl: pnl.mean(axis=-1),
    "sharpe": lambda pnl: pnl.mean(axis=-1) / pnl.std(axis=-1),
}


def kept_mask(full: pd.DataFrame, filtered: pd.DataFrame, column: str = "Open time"
              ) -> np.ndarray:
    """Which of the unfiltered trades the filtered version still takes.

    Args:
        full: The trades of the strategy without the condition.
        filtered: The trades of the strategy with it.
        column: The entry timestamp column both exports carry.

    Returns:
        One boolean per row of `full`. Matching is on entry time: a filter removes
        entries, it does not move them, so a filtered trade that has no twin in `full`
        means the two exports are not the same strategy and the count will say so.
    """
    return full[column].isin(set(filtered[column])).to_numpy()


def benchmark(pnl: np.ndarray, kept: np.ndarray, statistic: str, draws: int,
              seed: int) -> dict:
    """The filter against the same number of trades removed at random.

    Args:
        pnl: P&L per trade of the unfiltered strategy, in account currency.
        kept: What `kept_mask` returned.
        statistic: A key of STATISTICS.
        draws: How many random subsets to draw.
        seed: Seeded generator, so the p is reproducible.

    Returns:
        The filter's own statistic, the null distribution's mean, and the empirical p.

        A filter that keeps a share r of the trades is compared against keeping a random
        share r of the same trades — so the comparison holds the trade count fixed and
        asks only whether *which* trades were dropped carried information. A p near 0.5
        says the filter is cosmetic: it bought a smaller sample and nothing else.
    """
    score = STATISTICS[statistic]
    rng = np.random.default_rng(seed)
    n = int(kept.sum())
    picks = rng.permuted(np.tile(np.arange(pnl.size), (draws, 1)), axis=1)[:, :n]
    drawn = score(pnl[picks])
    observed = float(score(pnl[kept]))
    return {"statistic": statistic, "observed": observed, "null_mean": float(drawn.mean()),
            "p": float((1 + (drawn >= observed).sum()) / (draws + 1)),
            "n_kept": n, "n_total": int(pnl.size), "share": n / pnl.size}
