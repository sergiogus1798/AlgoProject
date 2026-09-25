"""Does the best point of this grid beat what searching pure noise would have produced?"""

import numpy as np
import pandas as pd

from core.surface import dedupe, plateau

PROCEED, NOISE = "proceed", "noise"


def noise_check(frame: pd.DataFrame, metric: str, margin: float = 1.0) -> dict:
    """Compare the grid's best point against the maximum a null grid would reach.

    Args:
        frame: A grid, already stripped of sentinels.
        metric: The column the verdict is read on. Named in the report, never implicit.
        margin: How far above the null maximum the observed one must sit, as a multiple.

    Returns:
        The effective n, the dispersion, both maxima, their ratio and the call.

        Under the hypothesis that no parameter does anything, the best of N draws with
        dispersion sigma still lands near sigma * sqrt(2 ln N). A grid whose best point
        does not clear that has found nothing, and neither the saturated phase nor the
        5,000 variants are worth running. **n_eff, not the row count**: inert parameters
        duplicate points and feeding rows would raise the bar against a grid that is
        smaller than it looks.
    """
    distinct = dedupe.distinct(frame)
    values = pd.to_numeric(distinct[metric], errors="coerce").dropna().to_numpy()
    n_eff = int(values.size)
    threshold = plateau.expected_max(float(values.std()), n_eff)
    observed = float(values.max())
    return {"metric": metric, "n_rows": int(len(frame)), "n_eff": n_eff,
            "sigma": float(values.std()), "observed_max": observed,
            "noise_max": threshold, "ratio": observed / threshold,
            "plateau_area": plateau.plateau_area(values),
            "above_half_max": plateau.above_half_max(values),
            "verdict": PROCEED if observed > threshold * margin else NOISE}


def shape(frame: pd.DataFrame, metric: str) -> dict:
    """How peaked the surface is, beyond where its maximum sits.

    Args:
        frame: A grid, already stripped of sentinels.
        metric: The column to describe.

    Returns:
        Kurtosis and (max - median) / IQR. A high spike ratio on a grid whose plateau area
        is small says the result lives at one point, which is the shape that does not
        survive: the two numbers are read together or neither means much.
    """
    values = pd.to_numeric(dedupe.distinct(frame)[metric], errors="coerce").dropna()
    iqr = float(values.quantile(0.75) - values.quantile(0.25))
    return {"kurtosis": float(values.kurtosis()),
            "spike_ratio": float((values.max() - values.median()) / iqr),
            "median": float(values.median()), "max": float(values.max())}
