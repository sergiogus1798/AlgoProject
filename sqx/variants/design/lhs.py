"""The design: a Latin hypercube over the live parameters, inside their in-sample plateau."""

import numpy as np
from scipy.stats import qmc

DECIMALS = 3


def draw(live: dict[str, list[float]], kept: dict[str, list[float]], n: int,
         seed: int) -> list[dict[str, float]]:
    """N tuples spread uniformly over the box, one stratum per parameter and per draw.

    Args:
        live: `levels.live`: the box, as every level of each live parameter.
        kept: The same lists after the pilot dropped its thin levels (`live` when none).
        n: How many points.
        seed: The design's seed.

    Returns:
        One dict per point. An integer parameter is the nearest integer (the box is widened
        half a step each side so the end values weigh as much as the middle); a decimal one
        is rounded to `DECIMALS`. A value whose nearest level the pilot dropped moves to the
        nearest kept level. Duplicates are NOT removed here: `plan.build` does it.
    """
    names = sorted(live)
    unit = qmc.LatinHypercube(d=len(names), seed=seed).random(n)
    columns = []
    for i, name in enumerate(names):
        levels = np.array(live[name])
        whole = all(float(v).is_integer() for v in levels)
        lo, hi = levels.min() - whole / 2, levels.max() + whole / 2
        values = lo + unit[:, i] * (hi - lo)
        values = np.round(values) if whole else np.round(values, DECIMALS)
        values = np.clip(values, levels.min(), levels.max())
        gone = set(live[name]) - set(kept[name])
        if gone:
            near = levels[np.abs(levels[None, :] - values[:, None]).argmin(axis=1)]
            keep = np.array(kept[name])
            moved = keep[np.abs(keep[None, :] - values[:, None]).argmin(axis=1)]
            values = np.where(np.isin(near, list(gone)), moved, values)
        columns.append(values)
    return [{n_: float(c[j]) for n_, c in zip(names, columns)} for j in range(n)]
