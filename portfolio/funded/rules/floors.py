"""One pure function per prop-firm rule: the daily floor, the max-loss floor, target, days, consistency."""

import numpy as np


def daily_floor(b0: float, e0: float, size: float, pct: float, basis: str) -> float:
    """The day's equity floor for the daily-loss rule.

    Args:
        b0: Balance at the day's start.
        e0: Equity at the day's start (balance plus floating carried overnight).
        size: The account's starting balance.
        pct: Daily-loss percentage, as a fraction.
        basis: "balance" (FTMO: `b0 - pct*size`) or "max_be" (Hantec, unconfirmed:
            `max(b0, e0)*(1-pct)`).

    Returns:
        Equity strictly below this fails the daily-loss rule.
    """
    if basis == "balance":
        return b0 - pct * size
    return max(b0, e0) * (1 - pct)


def max_floor(mode: str, size: float, pct: float, hw: float, eod: float) -> float:
    """The account's equity floor for the max-loss rule.

    Args:
        mode: "static" (`size*(1-pct)`), "trailing" (Hantec: `min(hw - pct*size, size)`, locks at
            `size` once the high-water mark clears it) or "eod_trailing" (FTMO 1-step:
            `min(eod - pct*size, size)`).
        size: The account's starting balance.
        pct: Max-loss percentage, as a fraction.
        hw: Highest intraday equity reached so far in this stage.
        eod: Highest end-of-day balance reached so far in this stage.

    Returns:
        Equity strictly below this fails the max-loss rule.
    """
    if mode == "static":
        return size * (1 - pct)
    if mode == "trailing":
        return min(hw - pct * size, size)
    return min(eod - pct * size, size)


def target_met(balance: float, size: float, pct: float) -> bool:
    """Whether the closed balance has reached the stage's profit target.

    Args:
        balance: Closed balance at the day's end.
        size: The account's starting balance.
        pct: Profit target, as a fraction of `size`.
    """
    return balance - size >= pct * size


def days_ok(stats: dict, stage: dict) -> bool:
    """Whether a stage's minimum-days rule is satisfied.

    Args:
        stats: `trading_days`, `profitable_days` — counts accumulated so far in this stage.
        stage: A stage dict from `catalog.plan` (`min_days`, `min_days_kind`).

    Returns:
        True when no minimum is set or it has been reached.
    """
    md = stage["min_days"]
    if md is None:
        raise NotImplementedError(f"stage {stage['stage']}: min_days unknown, no catalogue value")
    if md == 0:
        return True
    if stage["min_days_kind"] == "profitable":
        return stats["profitable_days"] >= md
    return stats["trading_days"] >= md


def consistency_ok(profits: np.ndarray, stage: dict) -> bool:
    """Whether a stage's consistency rule is satisfied over the days seen so far.

    Args:
        profits: Each day's closed P&L so far this stage, at the stage's risk.
        stage: A stage dict from `catalog.plan` (`consistency`, `consistency_kind`).

    Returns:
        True when no consistency rule is set or it holds.
    """
    c = stage["consistency"]
    if not c:
        return True
    if stage["consistency_kind"] == "best_over_total":
        return profits.max() / profits.sum() <= c
    positive = profits[profits > 0].sum()
    return profits.max() <= c * positive
