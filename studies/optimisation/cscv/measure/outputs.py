"""What the partitions of one CSCV say: the paper's four outputs, the haircut and who gets chosen."""

import numpy as np

HALF = 0.5          # omega at or under it is lambda <= 0: the pick landed in the worse half
EPS = 1e-12


def line(inside: np.ndarray, outside: np.ndarray) -> dict:
    """The paper's degradation line: the pick's Sharpe out on its Sharpe in, a point per partition.

    Returns:
        `beta`, `alfa` and `r2`, the R-squared adjusted for the one regressor. The two halves
        of a partition add up to the same whole, so on pure noise beta is negative by
        construction: it is read against its null, never against zero.
    """
    dx, dy = inside - inside.mean(), outside - outside.mean()
    sxx, syy, sxy = dx @ dx, dy @ dy, dx @ dy
    beta = sxy / sxx if sxx > 0 else np.nan
    r2 = sxy * sxy / (sxx * syy) if sxx > 0 and syy > 0 else np.nan
    count = len(inside)
    return {"beta": float(beta), "alfa": float(outside.mean() - beta * inside.mean()),
            "r2": float(1 - (1 - r2) * (count - 1) / (count - 2))}


def cdf(values: np.ndarray, found: dict) -> np.ndarray:
    """The share of `values` at or under each bin's right edge, on the bins of `found["hist"]`."""
    bins = len(found["hist"])
    cell = ((values - found["lo"]) * (bins / (found["hi"] - found["lo"]))).astype(np.int64)
    return np.bincount(np.clip(cell, 0, bins - 1), minlength=bins).cumsum() / len(values)


def dominance(values: np.ndarray, found: dict, tolerance: float) -> dict:
    """Whether a list of out-of-sample Sharpes dominates every variant's, picked at random.

    Args:
        values: One out-of-sample Sharpe per partition: the pick's, or the mother's.
        found: What `cscv.run` returned; its `hist` is the distribution of all variants.
        tolerance: How far the list's distribution function may rise above the other's and
            still count as first order. The list is a subset of all the values, so its top
            ends first and the strict inequality fails by construction just under the maximum.

    Returns:
        `primer_orden` (F_list <= F_all + tolerance at every bin), `segundo_orden` (the same
        on the running integrals, no tolerance) and `brecha`, the largest F_list - F_all.
    """
    gap = cdf(values, found) - found["hist"].cumsum() / found["hist"].sum()
    return {"primer_orden": bool(gap.max() <= tolerance),
            "segundo_orden": bool(gap.cumsum().max() <= EPS * len(gap)),
            "brecha": float(gap.max())}


def summary(found: dict, tolerance: float) -> dict:
    """The four outputs of one CSCV and the Sharpe haircut, as plain numbers.

    Args:
        found: What `cscv.run` returned.
        tolerance: As dominance().

    Returns:
        `pbo` (share of partitions with the pick in the worse half out of sample),
        `p_perdida` (share with the pick's Sharpe out at or under zero), `beta`, `alfa`, `r2`
        (line()), `hc` = 1 - median Sharpe out / median Sharpe in of the pick (NaN when the
        median in is not positive) and dominance()'s three.
    """
    inside, outside = found["sr_in"], found["sr_out"]
    middle = float(np.median(inside))
    return {"pbo": float((found["omega"] <= HALF).mean()),
            "p_perdida": float((outside <= 0).mean()),
            **line(inside, outside),
            "hc": float(1 - np.median(outside) / middle) if middle > 0 else np.nan,
            **dominance(outside, found, tolerance)}


def selection(pick: np.ndarray, names: np.ndarray) -> dict:
    """Who gets chosen across the partitions.

    Args:
        pick: The column chosen in each partition.
        names: The columns' variant identifiers.

    Returns:
        `distintas` (variants chosen at least once), `mas_elegida` and `peso` (the most
        chosen and its share of the partitions) and `tabla`, [(variant, share)] from the most
        chosen down.
    """
    count = np.bincount(pick, minlength=len(names))
    order = np.argsort(-count, kind="stable")
    order = order[count[order] > 0]
    return {"distintas": int(len(order)), "mas_elegida": str(names[order[0]]),
            "peso": float(count[order[0]] / len(pick)),
            "tabla": [(str(names[i]), float(count[i] / len(pick))) for i in order]}


def mother(found: dict, tolerance: float) -> dict:
    """The mother's own list: what she scored out of sample in every partition, against all.

    Returns:
        `puesto_mediano` (her median relative rank out of sample), `sobre_mediana` (share of
        partitions where she is above half the variants), `p_perdida` and dominance()'s three.
        She was chosen looking at `build`, which sits in sample in many partitions: annotated.
    """
    return {"puesto_mediano": float(np.median(found["track_omega"])),
            "sobre_mediana": float((found["track_omega"] > HALF).mean()),
            "p_perdida": float((found["track_out"] <= 0).mean()),
            **dominance(found["track_out"], found, tolerance)}
