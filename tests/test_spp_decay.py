#!/usr/bin/env python3
"""Known-answer test for studies.breakage.spp.model.decay: the SPP's criteria metrics, from
their definitions — the distance of the original to its grid's median, the ratio of medians
and its floor, Vargha–Delaney's A, W1/IQR, and the zero-edge null of an OOS1 grid."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.spp.model import decay


def close(got: float, want: float, tol: float = 1e-9) -> bool:
    """Whether two numbers agree."""
    return abs(got - want) <= tol


def main() -> None:
    """Fail loudly if a metric stops matching the number its definition gives."""
    rng = np.random.default_rng(7)
    grid = np.arange(101.0)  # median 50, IQR 50, p5 = 5, p95 = 95

    d = decay.distance(grid, 75.0, 0.25)
    assert close(d["rel"], 50.0) and close(d["iqr"], 0.5), d  # +50 % of 50, half an IQR
    assert close(d["null"][0], -0.9) and close(d["null"][1], 0.9), d
    assert (
        decay.distance(grid - 50.0, 25.0, 0.25)["rel"] is None
    )  # median 0: no share of it
    assert close(decay.distance(grid - 50.0, 25.0, 0.25)["iqr"], 0.5)

    a = rng.normal(0.0, 1.0, 4001)
    assert close(decay.superiority(a, a), 0.5)  # identical samples
    assert close(decay.superiority(a, a + 100.0), 1.0)  # every OOS beats every IS
    assert close(decay.superiority(a, a - 100.0), 0.0)
    assert close(
        decay.superiority(np.array([1.0, 2.0]), np.array([2.0, 3.0])), 0.875
    )  # (3 + ½)/4

    q1, q3 = np.percentile(a, [25, 75])
    assert close(
        decay.wasserstein(a, a + 0.3), 0.3 / (q3 - q1)
    )  # a pure shift, in IQRs
    assert close(decay.wasserstein(a, a), 0.0)

    assert close(
        decay.ratio(np.array([1.0, 2.0, 3.0]), np.array([0.5, 1.0, 1.5]), 0.1), 0.5
    )
    assert (
        decay.ratio(np.array([-1.0, 0.05, 1.0]), np.array([1.0, 1.0, 1.0]), 0.1) is None
    )

    assert close(float(decay.profit_factor(np.array([0.0]))[0]), 1.0)  # no mean, PF 1

    # A family that does not decay (IS and OOS1 the same Sharpe 0.7) against its zero-edge null:
    # the null's median is the OOS1 grid recentred on 0, and its width is 1/sqrt(years).
    is_ = rng.normal(0.7, 0.3, 4000)
    oos = pd.DataFrame(
        {
            "SharpeRatio": rng.normal(0.7, 0.3, 4000),
            "SortinoRatio": rng.normal(1.2, 0.6, 4000),
            "ProfitFactor": rng.normal(1.5, 0.2, 4000),
            "NumberOfTrades": 150.0,
        }
    )
    b = oos["SharpeRatio"].to_numpy()
    wide, narrow = (
        decay.compare(is_, b, 0.1, decay.zero_edge(oos, years)["SharpeRatio"])
        for years in (4.0, 400.0)
    )
    assert abs(wide["a"] - 0.5) < 0.02 and abs(wide["ratio"] - 1.0) < 0.03, wide
    assert close(narrow["null"]["a"][2], decay.superiority(is_, b - np.median(b)), 0.01)
    assert abs(narrow["null"]["ratio"][2]) < 1e-3  # a zero-edge median is 0
    assert narrow["a"] > narrow["null"]["a"][4]  # 400 years: the null is far below
    assert (
        wide["null"]["a"][4] > 0.5 > wide["null"]["a"][0]
    )  # 4 years: it covers no decay
    spread = wide["null"]["ratio"][4] - wide["null"]["ratio"][0]
    assert abs(spread - 2 * 1.645 / np.sqrt(4.0) / np.median(is_)) < 0.1, spread
    pf = decay.zero_edge(oos, 4.0)["ProfitFactor"]
    assert abs(np.median([np.median(m) for m in pf]) - 1.0) < 1e-4  # centred on PF 1
    assert decay.compare(is_, b, 0.1, None)["null"] is None  # no model, no null
    print("ok")


if __name__ == "__main__":
    main()
