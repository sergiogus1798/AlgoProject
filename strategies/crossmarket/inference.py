"""Judge the runs: where the real one sits in its null, and what that is worth across markets."""

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.05        # per-market level; the majority rule is what carries the correction
MIN_TRADES = 30     # below this a market is not judged at all, it is reported as too small
MIN_ON_OPEN = 0.95  # below this the entries are pending-order fills the null cannot reproduce
MIN_MARKETS = 4     # fewer testable markets than this and a majority means nothing
CORRELATED = 0.5    # assumed pairwise correlation for the honest false-pass figure
VERDICTS = ("MANTENER", "DESCARTAR", "NO EVALUABLE")


def locate(real: float, null: np.ndarray) -> dict:
    """Where one real run sits in its own null distribution.

    Args:
        real: The real run's statistic.
        null: One statistic per random run.

    Returns:
        The p-value, the null's median, and the effect size. One is added to numerator and
        denominator so a run that beats every draw reports the resolution of the test rather
        than an impossible zero: with 5,000 draws the smallest p observable is 1/5001.
    """
    return {"p": float((1 + np.sum(null >= real)) / (1 + null.size)),
            "null_r": float(np.median(null)),
            "edge_r": real - float(np.median(null)),
            "resolution": 1.0 / (1 + null.size)}


def shape(real: float, null: np.ndarray, bins: int = 60) -> dict:
    """The null distribution reduced to something a chart can draw.

    Args:
        real: The real run's statistic.
        null: One statistic per random run.
        bins: Histogram bins.

    Returns:
        Bin counts, the range they cover, and the real value. Kept instead of the raw draws
        because a whole databank's draws are gigabytes and a histogram is a few hundred bytes;
        the range is widened to include the real value so it is always on the axis.
    """
    lo, hi = min(float(null.min()), real), max(float(null.max()), real)
    counts, edges = np.histogram(null, bins=bins, range=(lo, hi))
    return {"counts": counts.tolist(), "lo": float(edges[0]), "hi": float(edges[-1]),
            "real": real, "mean": float(null.mean())}


def testable(row: dict) -> bool:
    """Whether a market's row may enter the vote.

    Args:
        row: One (strategy, market) row.

    Returns:
        False when the market has too few trades to say anything, or when the entries did not
        land on bar opens. A pending order filled inside a bar is a price-conditional selection
        the null cannot reproduce, so testing it anyway flatters the strategy.
    """
    return row["trades"] >= MIN_TRADES and row["on_bar_open"] >= MIN_ON_OPEN


def family(rows: pd.DataFrame) -> str:
    """Which test a strategy's result actually is.

    Args:
        rows: That strategy's per-market rows.

    Returns:
        "entry" when every exit is the fixed bar cap, "entry+exit" otherwise. The models reuse
        the real holds without reproducing what set them, so for a strategy that exits on a
        rule the result is a joint test and must not be read as entry timing.
    """
    return "entry" if rows["bar_cap"].min() == 1.0 else "entry+exit"


def call(rows: pd.DataFrame) -> dict:
    """One strategy's verdict across its markets.

    Args:
        rows: That strategy's testable per-market rows.

    Returns:
        Markets judged, markets beaten and the verdict. A strict majority at ALPHA, which is
        the rule the owner chose; the base asset is excluded upstream because it is the market
        that was fitted and beats any null by construction.
    """
    beaten = int((rows["p"] <= ALPHA).sum())
    judged = len(rows)
    if judged < MIN_MARKETS:
        return {"markets": judged, "beaten": beaten, "verdict": VERDICTS[2]}
    return {"markets": judged, "beaten": beaten,
            "verdict": VERDICTS[0] if beaten > judged / 2 else VERDICTS[1]}


def false_passes(judged: int, strategies: int) -> dict:
    """How many strategies the majority rule lets through on luck alone.

    Args:
        judged: Markets each strategy is voted over.
        strategies: How many strategies were tested.

    Returns:
        Expected false passes under independent markets and under equicorrelated ones. The
        second is the honest one: eight markets driven by one dollar-and-risk factor behave
        like about two, so the vote is far weaker than the binomial suggests, and the
        strategies it lets through will look like a coherent family rather than like noise.
    """
    need = max(judged // 2 + 1, MIN_MARKETS // 2 + 1)
    independent = float(stats.binom.sf(need - 1, judged, ALPHA))
    common = np.linspace(-6, 6, 2001)
    conditional = stats.norm.sf((stats.norm.isf(ALPHA) - np.sqrt(CORRELATED) * common)
                                / np.sqrt(1 - CORRELATED))
    joint = float(np.trapezoid(stats.binom.sf(need - 1, judged, conditional)
                               * stats.norm.pdf(common), common))
    return {"independent": independent * strategies, "correlated": joint * strategies}


def table(per_market: pd.DataFrame) -> pd.DataFrame:
    """The verdict for every strategy.

    Args:
        per_market: Every (strategy, market) row, with a `testable` column.

    Returns:
        One row per strategy, best first. Ranked by markets beaten and then by the median
        effect, so the table reads as a shortlist rather than as a pass list.
    """
    rows = [{"strategy": name, "family": family(g), **call(g[g["testable"]]),
             "edge_r": float(g.loc[g["testable"], "edge_r"].median()),
             "p_median": float(g.loc[g["testable"], "p"].median())}
            for name, g in per_market.groupby("strategy", sort=False)]
    return (pd.DataFrame(rows).sort_values(["beaten", "edge_r"], ascending=False)
            .reset_index(drop=True))
