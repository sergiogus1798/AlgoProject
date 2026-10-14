"""Where the original backtest sits among its own re-runs: its percentile and the median's gap."""

from typing import TypedDict

import numpy as np


class Place(TypedDict):
    """Where the original sits among its re-runs: percentile, gap in percent and in IQRs, the re-runs' own band."""

    percentile: float
    gap_pct: float | None
    gap_iqr: float | None
    own: list[float] | None


def place(sims: np.ndarray, real: float, floor: float) -> Place:
    """The criteria metrics of one task: is the original typical of what the task simulated?

    Args:
        sims: One metric over the task's re-runs.
        real: The same metric of the unperturbed backtest the task started from.
        floor: `gap_pct` is published only when |real| is at least this many IQRs of the
            re-runs: a share of an original near zero is an explosion, not a gap.

    Returns:
        `percentile` — share of re-runs below the original, half of the ties counted, in
        percent: 50 is an original in the middle of its re-runs, 100 one no re-run reached;
        `gap_pct` — (median − original) / |original| in percent, signed, None under the floor;
        `gap_iqr` — (original − median) in IQRs of the re-runs, None when they have no spread
        (a task whose perturbation changed nothing); `own` — the 5th and 95th percentile of
        that IQR distance over the re-runs themselves: what an original that were one more
        re-run would read.
    """
    q5, q1, median, q3, q95 = np.percentile(sims, [5, 25, 50, 75, 95])
    spread = float(q3 - q1)
    return {"percentile": float(100 * ((sims < real).sum() + 0.5 * (sims == real).sum())
                                / sims.size),
            "gap_pct": float(100 * (median - real) / abs(real))
            if abs(real) > 0 and abs(real) >= floor * spread else None,
            "gap_iqr": float((real - median) / spread) if spread > 0 else None,
            "own": [float((q5 - median) / spread), float((q95 - median) / spread)]
            if spread > 0 else None}
