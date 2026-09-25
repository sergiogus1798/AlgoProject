"""What a run is worth, for the real one and for thousands of null ones at once.

Each statistic carries the side of it that counts as good, because half of them read the other
way: a small drawdown is a better drawdown, and comparing it the common way makes the real run
look worse than chance exactly when it suffered less."""

import numpy as np

# True when a larger value is the better one. `dd` is the trap the direction exists for.
GOOD_HIGH = {"net": True, "sharpe": True, "pf": True, "retdd": True, "dd": False}


def drawdown(pnl: np.ndarray) -> np.ndarray:
    """Deepest fall of the cumulative P&L of every run.

    Args:
        pnl: One row per run, one column per trade.

    Returns:
        One positive value per run, in account currency. Additive on the P/L rather than
        compounded on an equity curve, which is the convention the rest of this module and
        the sizing rule already sit in: the sizing does not compound on the balance either
        (measured 2026-09-22 across the XAUUSD corpus).
    """
    curve = np.cumsum(pnl, axis=1)
    return (np.maximum.accumulate(curve, axis=1) - curve).max(axis=1)


def profit_factor(pnl: np.ndarray) -> np.ndarray:
    """Gross gain over gross loss of every run.

    Args:
        pnl: One row per run, one column per trade.

    Returns:
        One ratio per run; infinite for a run with no losing trade, which is a real
        statement about that run and not a value to clip.
    """
    gain = np.where(pnl > 0, pnl, 0.0).sum(axis=1)
    loss = -np.where(pnl < 0, pnl, 0.0).sum(axis=1)
    return np.divide(gain, loss, out=np.full_like(gain, np.inf), where=loss > 0)


def measure(pnl: np.ndarray, names: list[str]) -> dict:
    """Every requested statistic, for every run.

    Args:
        pnl: One row per run, one column per trade. A single run is passed as one row.
        names: Keys of GOOD_HIGH, from statistics.report.

    Returns:
        One array per name, each of length `runs`. Only what is asked for is built: the
        drawdown scan and the profit factor are each about a fifth of a null run, and a
        caller that reads one statistic -- the gate reads `sharpe` alone -- paid for five.
        Measured on 2,000 runs x 570 trades: 22.5 ms for the five, 1.75 ms for `sharpe`.

        The choice of name moves the verdict more
        than the choice of null does -- 51.0% of the corpus beat the null on `sharpe` and
        21.5% on `net`, from one simulation -- because `sharpe` is scale-free and divides
        out the very thing that separates a strategy's trades from random ones: the real
        ones are 36% less volatile.
    """
    wanted = set(names)
    net = pnl.sum(axis=1) if wanted & {"net", "retdd"} else None
    fall = drawdown(pnl) if wanted & {"dd", "retdd"} else None
    build = {"net": lambda: net,
             "sharpe": lambda: pnl.mean(axis=1) / pnl.std(axis=1, ddof=1),
             "pf": lambda: profit_factor(pnl),
             "dd": lambda: fall,
             "retdd": lambda: np.divide(net, fall, out=np.zeros_like(net), where=fall > 0)}
    return {name: build[name]() for name in names}
