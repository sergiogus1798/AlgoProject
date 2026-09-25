"""What the number of independent trials does to the best Sharpe."""

import pandas as pd

from core import significance
from core.surface import plateau
from studies.optimisation.cscv.measure import cscv


def deflated(window: pd.DataFrame, pick: int, n_eff: int) -> dict:
    """Is the best variant's Sharpe real, given how many were tried to find it?

    Args:
        window: The in-sample panel.
        pick: Position of the variant being judged.
        n_eff: Independent trials, from `independent`.

    Returns:
        What `core.surface.plateau.deflated_sharpe` returns.

        ⚠️ **This is a Sharpe whatever `cscv.score` the study ranks by.** The deflated
        Sharpe is defined against the expected maximum of n_eff draws of a Sharpe, so a
        Sortino here would be compared against the wrong benchmark. Ranking picks the
        variant; the DSR then judges that variant on its Sharpe.

        **Every Sharpe here is per period**, the unit that function's docstring insists
        on: the returns, the spread across trials and the benchmark are all computed off
        the same weekly panel, so nothing is annualised on one side of the comparison and
        not the other.
    """
    returns = window.to_numpy()[:, pick]
    observed, skew, kurtosis = significance.moments(returns)
    spread = float(cscv.sharpe(window.to_numpy()).std(ddof=1))
    return plateau.deflated_sharpe(observed, spread, n_eff, len(returns), skew, kurtosis)
