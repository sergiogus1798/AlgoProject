"""The simulated distributions behind a strategy's travel columns, as `core.study.draws` rows."""

from typing import Any, cast

import numpy as np

from core.study import draws
from studies.transfer.crossmarket.travel import rules, stat, tensor

TEST = "crossmarket.travel"
JOINT = (("z_conj", "all"), ("z_conj_v0", "V0"), ("z_conj_v1", "V1"), ("z_conj_v2", "V2"),
         ("z_conj_v0v2", "V0V2"))


def rows(one: tensor.Built, mask: dict, got: rules.Evaluated, name: str, identity: str, seed: int) -> list[dict]:
    """Every distribution one strategy's verdict columns and `markets.parquet` z are made of.

    Args:
        one: The strategy's tensor, as `tensor.build()` returns it.
        mask: `rules.windows(cal)`.
        got: What `rules.evaluate` returned (its `verdict` and `beta` draws).
        name, identity: The strategy.
        seed: travel.seed.

    Returns:
        Raw rows, observed on the scale of the draws (total R; `p_breadth` counts markets,
        `z_beta` is a slope), so z = (observed - mean) / sd. Then one row per market for the
        `z` of `markets.parquet`, histogram only (raw=False).
    """
    who: dict[str, Any] = dict(strategy=name, seed=seed)
    out = [draws.record(TEST, col, cast(float, stat.total(one["real"], cells=mask[k])),
                        stat.total(one["null"], cells=mask[k]), identity, **who)
           for col, k in JOINT]
    every, whole = range(len(one["markets"])), mask["all"]
    left = one["markets"].index(got["verdict"]["minus_market"]) if got["verdict"]["minus_market"] else None
    if left is not None:
        keep = [k for k in every if k != left]
        out.append(draws.record(TEST, "z_minus_market", cast(float, stat.total(one["real"], keep, whole)),
                                stat.total(one["null"], keep, whole), identity,
                                minus_market=one["markets"][left], **who))
    real = np.array([stat.total(one["real"], [j], whole) for j in every])
    null = np.stack([stat.total(one["null"], [j], whole) for j in every], 1)
    out.append(draws.record(TEST, "p_breadth", int((real > np.nanmedian(null, 0)).sum()),
                            (null > np.nanmedian(null, 0)).sum(1), identity, **who))
    if got["beta"] is not None:
        out.append(draws.record(TEST, "z_beta", *cast(tuple[float, np.ndarray], got["beta"]), identity, **who))
    return out + [draws.record(TEST, "z", real[j], null[:, j], identity, raw=False,
                               market=name_j, **who)
                  for j, name_j in enumerate(one["markets"])]
