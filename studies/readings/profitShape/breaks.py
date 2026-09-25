"""Item 7: whether the mean result changed somewhere, and where."""

import numpy as np
import pandas as pd

from core.significance import moments, variance_factor

CRITICAL = 1.36     # 5% two-sided for the supremum of a Brownian bridge


def cusum(x: np.ndarray) -> dict:
    """OLS-CUSUM on a series whose mean is assumed constant.

    Args:
        x: Net P&L per trade in trade order, or per period in calendar time.

    Returns:
        The path, its supremum, where that falls, and whether stability is rejected at 5%.
        Under a constant mean the standardised partial sums behave like a Brownian bridge,
        whose supremum clears 1.36 five per cent of the time. The argmax is the most likely
        break, and it is a **location, not a date the strategy knew about**: nothing stops
        it landing where the market changed rather than where the strategy did.
    """
    n = x.size
    path = np.cumsum(x - x.mean()) / (x.std(ddof=1) * np.sqrt(n))
    peak = int(np.argmax(np.abs(path)))
    return {"path": path, "sup": float(np.abs(path).max()), "at": peak,
            "share": peak / n, "rejects": bool(np.abs(path).max() > CRITICAL)}


def either_side(x: np.ndarray, at: int) -> pd.DataFrame:
    """What the series looked like before and after a candidate break.

    Args:
        x: The same series `cusum` read.
        at: The index the break is placed at.

    Returns:
        Two rows: count, mean, and per-observation Sharpe. The post-break half is the one
        that describes the strategy now; reporting only the pooled number hides exactly
        the thing a break test was run to find.
    """
    parts = {"before": x[:at + 1], "after": x[at + 1:]}
    return pd.DataFrame([{"segment": k, "n": v.size, "mean": float(v.mean()),
                          "sharpe": float(v.mean() / v.std(ddof=1))}
                         for k, v in parts.items()]).set_index("segment")


def sharpe_error(window: np.ndarray) -> float:
    """The standard error of a Sharpe that does not assume normal returns.

    Args:
        window: One observation per trade or per period.

    Returns:
        The non-normal standard error, the same skew and kurtosis correction the PSR and
        the minimum track record already use -- `core.significance.variance_factor`, so
        the two cannot drift apart. It is wider than 1/sqrt(n) exactly when the returns
        are skewed or fat-tailed, which is when a rolling Sharpe most needs the width.
    """
    sharpe, skew, kurtosis = moments(window)
    return float(np.sqrt(variance_factor(sharpe, skew, kurtosis) / (window.size - 1)))


def rolling(x: np.ndarray, window: int) -> pd.DataFrame:
    """Sharpe over a moving window, with a band that does not assume normality.

    Args:
        x: The series.
        window: Observations per window.

    Returns:
        One row per window end: the Sharpe and its 95% band. Overlapping windows are not
        independent readings, so the band says how uncertain **one** window is and never
        how many of them may sit below zero by chance.
    """
    rows = []
    for end in range(window, x.size + 1):
        chunk = x[end - window:end]
        sharpe = float(chunk.mean() / chunk.std(ddof=1))
        error = sharpe_error(chunk)
        rows.append({"end": end, "sharpe": sharpe, "low": sharpe - 1.96 * error,
                     "high": sharpe + 1.96 * error})
    return pd.DataFrame(rows).set_index("end")
