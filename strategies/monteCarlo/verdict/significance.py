"""Family E: could this edge be zero, given how many trades there are and how they are shaped?"""

import numpy as np

from core.significance import psr

__all__ = ["psr", "crosscheck"]


def crosscheck(psr_value: float, bootstrap_sharpe: np.ndarray) -> dict:
    """The analytic answer against the resampled one.

    Args:
        psr_value: What psr() returned as "psr".
        bootstrap_sharpe: Sharpe of every Family B simulation.

    Returns:
        Both probabilities that the edge is above zero and the gap between them. They are
        two pictures of the same question under different assumptions: agreement means the
        conclusion does not depend on the normal approximation, and a wide gap means the
        trades are skewed or fat-tailed enough that it does — which is a finding, not an
        error in either number.
    """
    empirical = float(np.mean(bootstrap_sharpe > 0))
    return {"psr": psr_value, "bootstrap": empirical,
            "gap": abs(psr_value - empirical)}
