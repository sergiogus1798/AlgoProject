"""§2.3 — does the IS X transfer to oos1 and oos2? Described, never recomputed out of sample."""

import warnings

import numpy as np
import pandas as pd
from scipy.stats import anderson_ksamp, ks_2samp


def effective(xs: pd.DataFrame, mae_oos: np.ndarray, cfg: dict) -> pd.DataFrame:
    """Which percentile of the out-of-sample winners each IS X turns out to be.

    Args:
        xs: What `threshold.x_values` returned.
        mae_oos: MAE in ATR of one window's winners.
        cfg: The study's config.

    Returns:
        One row per percentile: `effective` (share of those winners with MAE at or below X,
        in percent), `gap` (effective minus intended, in points: negative means the stop
        would cut more winners there than in IS) and `transfers` — within `transfer.tolerance`,
        or None when the window has fewer than `transfer.min_winners` winners to say it.
    """
    enough = len(mae_oos) >= cfg["transfer"]["min_winners"]
    rows = []
    for r in xs.itertuples():
        eff = 100 * float((mae_oos <= r.x).mean()) if len(mae_oos) else np.nan
        gap = eff - r.percentile
        rows.append({"percentile": r.percentile, "effective": eff, "gap": gap,
                     "transfers": bool(abs(gap) <= cfg["transfer"]["tolerance"]) if enough
                     else None})
    return pd.DataFrame(rows)


def shape(mae_is: np.ndarray, mae_oos: np.ndarray) -> dict:
    """The whole distribution of IS winners against one window's, with the size of the gap.

    Args:
        mae_is: MAE in ATR of the in-sample winners.
        mae_oos: The same for one out-of-sample window.

    Returns:
        `ks_d` and `ks_p` (Kolmogorov-Smirnov: the largest vertical gap between the two
        cumulative curves, and its p), `ad` and `ad_p` (Anderson-Darling k-sample, which
        weighs the tails more — its p is clipped by scipy to 0.001..0.25) and
        `median_ratio` (OOS median over IS median: above 1, the OOS winners needed more air).
    """
    ks = ks_2samp(mae_is, mae_oos)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")        # scipy warns every time it clips the p
        ad = anderson_ksamp([mae_is, mae_oos])
    return {"n_is": len(mae_is), "n_oos": len(mae_oos), "ks_d": float(ks.statistic),
            "ks_p": float(ks.pvalue), "ad": float(ad.statistic),
            "ad_p": float(ad.significance_level),
            "median_ratio": float(np.median(mae_oos) / np.median(mae_is))}
