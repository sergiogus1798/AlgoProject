"""What is left of the in-sample order out of sample once a shared control is taken out: the partial rho."""

import numpy as np
from scipy.stats import rankdata


def partial(inside: np.ndarray, outside: np.ndarray, controls: np.ndarray) -> float:
    """Spearman's rho of the two sides once the controls' ranks are taken out of both.

    Args:
        inside, outside: One value per variant.
        controls: variants x controls, e.g. each variant's number of trades.

    Returns:
        The correlation of the two rank residuals: what is left of the order when the
        variants that agree only because they share a control are not counted.
    """
    z = np.column_stack([np.ones(len(inside)), rankdata(controls, axis=0)])
    x, y = (r - z @ np.linalg.lstsq(z, r, rcond=None)[0]
            for r in (rankdata(inside), rankdata(outside)))
    return float(x @ y / np.sqrt((x @ x) * (y @ y)))
