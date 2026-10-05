"""The oos2 reading (Q11 d): the chosen portfolio's daily Sharpe against the best that luck gives N trials."""

import numpy as np

from ledger import trials


def read(returns: np.ndarray, sigma: float, n: int) -> dict:
    """The deflated Sharpe of one daily P&L path, by `ledger.trials.deflated` — no second formula.

    «Deflated Sharpe > 0» is read as the Sharpe left after subtracting the expected maximum
    of `n` trials of spread `sigma`: `excess` > 0, the same as a DSR above 0.5. The DSR itself
    is a probability, never below 0, so it cannot be what «> 0» judges; both are returned.

    Args:
        returns: The portfolio's daily P&L on the segment, any constant unit.
        sigma: The spread of the daily Sharpes it was chosen among.
        n: The trials it is deflated by.

    Returns:
        `sharpe` (per day), `benchmark` (the expected maximum Sharpe of `n` trials),
        `excess` (their difference), `dsr`, `n`, `sigma`, `n_days` and `state`: "pass" when
        `excess` > 0, else "fail".
    """
    got = trials.deflated(np.asarray(returns, dtype=float), sigma, n)
    excess = float(got["sharpe"] - got["benchmark"])
    return {"sharpe": float(got["sharpe"]), "benchmark": float(got["benchmark"]), "excess": excess,
            "dsr": float(got["dsr"]), "n": int(n), "sigma": float(sigma),
            "n_days": int(len(returns)), "state": "pass" if excess > 0 else "fail"}
