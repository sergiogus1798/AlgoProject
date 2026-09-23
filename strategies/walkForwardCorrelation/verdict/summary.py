"""The four things a run of partitions says about a selection rule."""

import numpy as np
import pandas as pd

GRID = 200           # points the two distributions are compared on
TOL = 1e-9


def pbo(records: pd.DataFrame) -> float:
    """Probability that the rule's pick turns out below average.

    Args:
        records: What `cscv.run` returned.

    Returns:
        The fraction of partitions where the chosen variant landed in the bottom half out
        of sample. At 0.5 the rule is worth exactly what picking at random is worth;
        above it, optimising is actively choosing the configurations that will disappoint.
    """
    return float((records["lam"] <= 0).mean())


def degradation(records: pd.DataFrame) -> dict:
    """How much of the in-sample ordering survives, averaged over the partitions.

    Args:
        records: What `cscv.run` returned.

    Returns:
        The mean slope and mean R-squared of `cscv.carry`, which fits across **all** the
        variants of each partition.

        A slope near one means the in-sample score carried over intact, zero means it
        told you nothing, and negative means it told you the opposite. Measured against a
        null of pure noise this reads zero, which is what makes it worth reading -- the
        same regression restricted to the chosen variant reads -0.57 on that same null,
        for a mechanical reason that has nothing to do with the strategy.
    """
    return {"slope": float(records["slope"].mean()), "r2": float(records["r2"].mean()),
            "slope_sd": float(records["slope"].std())}


def prob_loss(records: pd.DataFrame) -> float:
    """How often the rule's pick actually loses money out of sample.

    Args:
        records: What `cscv.run` returned.

    Returns:
        The fraction of partitions whose chosen variant finished the held-out half under
        water. The PBO is about rank and is blind to level: a surface where everything
        works can have a high PBO and never lose, and one where nothing works can have a
        low PBO. This is the number that says which of the two you are looking at.
    """
    return float((records["oos_pnl"] < 0).mean())


def dominance(records: pd.DataFrame) -> str:
    """Whether choosing by the rule beats settling for the middle of the surface.

    Args:
        records: What `cscv.run` returned.

    Returns:
        `primer_orden` when the rule's out-of-sample score is better at every threshold,
        `segundo_orden` when it is better on the accumulated distribution but crosses
        somewhere, and `ninguna` when the middle of the surface does as well.

        The comparison is paired -- the rule's pick against the median variant of the
        **same** partition -- so it asks whether the choosing was worth doing on each
        history rather than comparing two pools that never met.
    """
    chosen, middle = records["oos_score"].to_numpy(), records["oos_median"].to_numpy()
    line = np.linspace(min(chosen.min(), middle.min()),
                       max(chosen.max(), middle.max()), GRID)
    below_chosen = (chosen[:, None] <= line).mean(axis=0)
    below_middle = (middle[:, None] <= line).mean(axis=0)
    if np.all(below_chosen <= below_middle + TOL):
        return "primer_orden"
    if np.all(np.cumsum(below_chosen) <= np.cumsum(below_middle) + TOL):
        return "segundo_orden"
    return "ninguna"


def everything(records: pd.DataFrame) -> dict:
    """The four outputs of one rule's run, in one flat dictionary.

    Args:
        records: What `cscv.run` returned.

    Returns:
        `pbo`, `prob_loss`, `dominance`, the regression, and the median relative rank.
    """
    return {"pbo": pbo(records), "prob_loss": prob_loss(records),
            "dominance": dominance(records), "median_omega": float(records["omega"].median()),
            "partitions": len(records), **degradation(records)}
