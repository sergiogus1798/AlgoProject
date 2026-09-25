"""Every drawdown metric, and the account-capital convention the four of them share.

SQX measures a drawdown against the account, not against the profit curve: the denominator is
the initial capital plus the equity peak in force, never the peak alone. Reconstructed against
its stored tables the difference is not subtle -- 5.52% versus 195%.
"""

import numpy as np


def _paths(p: dict) -> tuple[np.ndarray, np.ndarray]:
    """The drawdown of every trade, absolute and relative to the account.

    Args:
        p: What recon.parts() returned.

    Returns:
        (absolute USD, fraction of capital + running peak), both flat and aligned with
        p["pnl"]. Path-dependent, so this is the one place a per-simulation loop is
        unavoidable: a running maximum does not reset at a segment boundary on its own.
    """
    pnl, offsets, capital = p["pnl"], p["offsets"], p["capital"]
    absolute, relative = np.empty(pnl.size), np.empty(pnl.size)
    for start, stop in zip(offsets[:-1], offsets[1:]):
        equity = np.cumsum(pnl[start:stop])
        peak = np.maximum.accumulate(np.concatenate([[0.0], equity]))[1:]
        absolute[start:stop] = peak - equity
        relative[start:stop] = (peak - equity) / (capital + peak)
    return absolute, relative


def prepare(p: dict) -> dict:
    """Add the drawdown paths to the shared parts, once.

    Args:
        p: What recon.parts() returned.

    Returns:
        The same dict with "dd" and "dd_rel" added. Called by recon.parts(); the four
        metrics below then cost a reduction each instead of a pass over the paths each.
    """
    p["dd"], p["dd_rel"] = _paths(p)
    return p


def _reduce(values: np.ndarray, p: dict, how: np.ufunc) -> np.ndarray:
    """Reduce a flat per-trade array to one value per simulation.

    Args:
        values: A flat array aligned with p["pnl"].
        p: What recon.parts() returned.
        how: np.maximum or np.add.

    Returns:
        One value per simulation.
    """
    return how.reduceat(values, p["offsets"][:-1])


def max_drawdown(p: dict) -> np.ndarray:
    """Deepest peak-to-valley fall of each simulation.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation.
    """
    return _reduce(p["dd"], p, np.maximum)


def drawdown_pct(p: dict) -> np.ndarray:
    """The same fall as a share of the account it happened to.

    Args:
        p: What recon.parts() returned.

    Returns:
        Percent per simulation, against capital plus the peak in force at that moment.
    """
    return 100.0 * _reduce(p["dd_rel"], p, np.maximum)


def avg_drawdown(p: dict) -> np.ndarray:
    """Mean drawdown across every trade of a simulation.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation. Averaged over **every** trade, zeros included -- averaging only
        the trades in drawdown is wrong by 11%, averaging episode maxima by 67%.
    """
    return _reduce(p["dd"], p, np.add) / p["n"]


def avg_pct_drawdown(p: dict) -> np.ndarray:
    """The same mean, relative to the account.

    Args:
        p: What recon.parts() returned.

    Returns:
        Percent per simulation, zeros included as above.
    """
    return 100.0 * _reduce(p["dd_rel"], p, np.add) / p["n"]


def return_dd_ratio(p: dict) -> np.ndarray:
    """Net profit per unit of absolute drawdown.

    Args:
        p: What recon.parts() returned.

    Returns:
        A ratio per simulation.
    """
    dd = max_drawdown(p)
    return np.divide(p["total"], dd, out=np.full_like(p["total"], np.inf), where=dd > 0)


def recovery_factor(p: dict) -> np.ndarray:
    """Net profit per unit of drawdown measured against the account.

    Args:
        p: What recon.parts() returned.

    Returns:
        A ratio per simulation. **Not a synonym of ReturnDDRatio**: that one divides by the
        absolute fall, this one by the capital-relative fall, and on the calibration
        strategy they are 3.86 and 4.40.
    """
    dd = drawdown_pct(p) / 100.0 * p["capital"]
    return np.divide(p["total"], dd, out=np.full_like(p["total"], np.inf), where=dd > 0)
