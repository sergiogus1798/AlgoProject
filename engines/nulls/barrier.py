"""The triple-barrier exit: where a trade leaves, given a stop, a target and a time limit.

Lopez de Prado's formulation, and the one shape that covers both what this corpus does today
and what it will do with a stop. `Exit After X Bars` is the vertical barrier alone, so a
strategy with no stop and no target is not a special case here -- it is the degenerate one,
and the same scan prices it."""

import numpy as np


def vertical(
    entries: np.ndarray, holds: np.ndarray, leave_px: np.ndarray
) -> tuple[np.ndarray, ...]:
    """Exit purely on time, with no price barrier in the way.

    Args:
        entries: Entry bar index of each trade.
        holds: How many bars each is held.
        leave_px: The bar price an exit fills at, one per bar, from the calibrated fill.

    Returns:
        (exit bar index, exit price). The fast path: with no barriers there is nothing to
        scan, and the whole XAUUSD corpus of 2026-09 takes it.
    """
    leave = entries + holds
    return leave, leave_px[leave]


def pnl(
    entries: np.ndarray,
    leave: np.ndarray,
    price: np.ndarray,
    sizes: np.ndarray,
    enter_px: np.ndarray,
    cost: np.ndarray,
    value: float,
) -> np.ndarray:
    """What each trade was worth, in account currency.

    Args:
        entries: Entry bar index of each trade.
        leave: Exit bar index, unused except to keep the call honest about what was priced.
        price: Exit price of each trade.
        sizes: Lots.
        enter_px: The bar price an entry fills at, one per bar, from the calibrated fill.
        cost: What this trade is charged, recovered from the real trade it reuses.
        value: Account currency per 1.0 of price per lot.

    Returns:
        One net P/L per trade. The real run and every null run pass through this one
        function, so a null run is the same money at risk paying the same broker.
    """
    return value * sizes * (price - enter_px[entries]) - cost
