"""Does in-sample performance predict out-of-sample performance across the parameter grid?"""

import numpy as np
import pandas as pd

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
        enormous: `ci95` is the Fisher-z interval with Spearman's variance 1.06/(n-3), and when it spans zero the honest
        reading is "this grid cannot tell", not "there is no relationship".
    """
    n = len(kept)
    rho = _spearman(kept[cols["is"]].to_numpy(), kept[cols["oos"]].to_numpy())
    if n < 4 or np.isnan(rho):
        return {"n": n, "rho": rho, "ci95": (float("nan"), float("nan")),
                "pearson": float("nan")}
    z = np.arctanh(np.clip(rho, -0.999999, 0.999999))
    half = 1.959964 * np.sqrt(1.06 / (n - 3))  # Spearman's z variance (Fieller), not Pearson's 1/(n-3)
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
    rho, fl = f"{found['rho']:.2f}".replace(".", ","), f"{floor:.2f}".replace(".", ",")
    if lo > floor:
        return {"call": "fiable",
                "why": f"Spearman {rho}, claramente por encima del mínimo de {fl}: el ranking "
                       "en IS predice el de OOS"}
    if hi < floor:
        return {"call": "no_fiable",
                "why": f"Spearman {rho}, claramente por debajo del mínimo de {fl}: optimizar "
                       "en IS no compra nada fuera"}
    return {"call": "indeciso",
            "why": f"Spearman {rho}, demasiado cerca del mínimo de {fl} para decidir con "
                   f"{found['n']} puntos: hacen falta más"}
