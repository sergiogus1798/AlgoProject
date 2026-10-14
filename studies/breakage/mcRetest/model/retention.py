"""What the re-runs keep of the original's total: retention at the median and the 5th percentile."""

from typing import TypedDict

import numpy as np


class Retention(TypedDict):
    """What the re-runs keep of the original's total: median and 5th-percentile retention, share positive, count."""

    ret_med: float
    ret_p5: float
    f_pos: float
    n: int


def retention(runs: np.ndarray, original: float) -> Retention:
    """Retention of a total across re-runs, as a share of the unperturbed strategy's own total.

    Args:
        runs: One total per re-run (excess or profit, any unit).
        original: The same total for the unperturbed strategy, same unit.

    Returns:
        ret_med (median of the runs over the original), ret_p5 (their 5th percentile over the
        original), f_pos (share of runs above zero) and n. With an original at or below zero, or no
        runs, both retentions are NaN — a share of nothing is not a number; f_pos is NaN only when
        there are no runs.
    """
    runs = np.asarray(runs, dtype=np.float64)
    n = int(runs.size)
    ok = n > 0 and original > 0
    return {"ret_med": float(np.median(runs) / original) if ok else float("nan"),
            "ret_p5": float(np.percentile(runs, 5) / original) if ok else float("nan"),
            "f_pos": float((runs > 0).mean()) if n else float("nan"),
            "n": n}
