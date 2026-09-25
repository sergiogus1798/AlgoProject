"""Does in-sample performance predict out-of-sample performance across the parameter grid?"""

import numpy as np
import pandas as pd

# The two readings of one batch, and the difference is what `oos2` is kept on a pedestal
# for (owner, 2026-09-24). `oos1_oos2` asks the ordinary question — does the build predict
# everything after it. `oos2_only` asks the strict one: with build AND oos1 both treated as
# in sample, does the segment nothing has ever looked at still come back. The batch is
# retested once and carries both, so switching reading re-runs the verdict and nothing else.
MODES = {"oos1_oos2": ("build", "oos1+oos2"), "oos2_only": ("build+oos1", "oos2")}


def columns(mode: str) -> dict:
    """The four C3 columns one reading of the split is measured on.

    Args:
        mode: A key of `MODES`.

    Returns:
        The in-sample and out-of-sample net-profit and trade-count column names, plus the
        two segment labels for the figure. `sqx.variants.collect` writes a column per
        segment and per union, so a mode is a choice of columns and never a recomputation.
    """
    inside, outside = MODES[mode]
    return {"is": f"NetProfit ({inside})", "oos": f"NetProfit ({outside})",
            "trades_is": f"NumberOfTrades ({inside})",
            "trades_oos": f"NumberOfTrades ({outside})",
            "is_label": inside, "oos_label": outside}


def points(metrics: pd.DataFrame, min_trades: int, cols: dict) -> pd.DataFrame:
    """The tuples that produced a real backtest on both sides of the split.

    Args:
        metrics: Contract C3, the manifest joined to the retested panel.
        min_trades: A tuple with fewer trades than this in either sample is dropped.
        cols: What `columns` returned — which reading of the split is being measured.

    Returns:
        One row per usable tuple. **The filter is not tidying, it is the measurement.** A
        parameter setting that barely trades produces a net profit that is one or two
        trades wide; left in, a handful of them dominate a correlation computed over a
        dozen points and the answer becomes an artefact of the degenerate corners rather
        than a statement about the surface.
    """
    kept = metrics.dropna(subset=[cols["is"], cols["oos"]])
    return kept[(kept[cols["trades_is"]] >= min_trades)
                & (kept[cols["trades_oos"]] >= min_trades)]


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Rank correlation, without pulling in scipy for one number.

    Args:
        a: First series.
        b: Second series.

    Returns:
        Pearson's r computed on the ranks, which is Spearman's rho. Ranks are used because
        one runaway parameter setting should not be able to decide the answer, and net
        profit across a grid is exactly the kind of series that has one.
    """
    ra, rb = pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def correlation(kept: pd.DataFrame, cols: dict) -> dict:
    """The walk-forward correlation and what it is allowed to claim.

    Args:
        kept: What `points` returned.
        cols: What `columns` returned.

    Returns:
        The statistic, the sample size, and the width of the band inside which the
        statistic says nothing. With a dozen points the sampling error on a correlation is
        enormous: `ci95` is the Fisher-z interval, and when it spans zero the honest
        reading is "this grid cannot tell", not "there is no relationship".
    """
    n = len(kept)
    rho = _spearman(kept[cols["is"]].to_numpy(), kept[cols["oos"]].to_numpy())
    if n < 4 or np.isnan(rho):
        return {"n": n, "rho": rho, "ci95": (float("nan"), float("nan")),
                "pearson": float("nan")}
    z = np.arctanh(np.clip(rho, -0.999999, 0.999999))
    half = 1.959964 / np.sqrt(n - 3)
    return {"n": n, "rho": rho,
            "ci95": (float(np.tanh(z - half)), float(np.tanh(z + half))),
            "pearson": float(np.corrcoef(kept[cols["is"]], kept[cols["oos"]])[0, 1])}


def verdict(found: dict, floor: float) -> dict:
    """Turn the correlation into the decision it is there to inform.

    Args:
        found: What `correlation` returned.
        floor: The rho below which in-sample ranking is not worth trusting.

    Returns:
        A call and the sentence behind it. Three outcomes, and the middle one is the
        common one: the interval spans the floor, so the grid is too small to decide and
        the answer is more points, not a different threshold.
    """
    lo, hi = found["ci95"]
    if np.isnan(found["rho"]):
        return {"call": "sin_dato",
                "why": f"solo {found['n']} puntos utilizables, o todos con el mismo valor"}
    if lo > floor:
        return {"call": "fiable",
                "why": f"rho {found['rho']:.2f}, intervalo [{lo:.2f}, {hi:.2f}] entero por "
                       f"encima de {floor}: el ranking en IS predice el de OOS"}
    if hi < floor:
        return {"call": "no_fiable",
                "why": f"rho {found['rho']:.2f}, intervalo [{lo:.2f}, {hi:.2f}] entero por "
                       f"debajo de {floor}: optimizar en IS no compra nada fuera"}
    return {"call": "indeciso",
            "why": f"rho {found['rho']:.2f}, pero el intervalo [{lo:.2f}, {hi:.2f}] cruza "
                   f"{floor}. Con {found['n']} puntos no se puede decidir: hacen falta mas"}
