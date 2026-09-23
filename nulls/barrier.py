"""The triple-barrier exit: where a trade leaves, given a stop, a target and a time limit.

Lopez de Prado's formulation, and the one shape that covers both what this corpus does today
and what it will do with a stop. `Exit After X Bars` is the vertical barrier alone, so a
strategy with no stop and no target is not a special case here -- it is the degenerate one,
and the same scan prices it."""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

FIRST = {"pessimistic": "sl", "optimistic": "tp"}


def vertical(entries: np.ndarray, holds: np.ndarray, leave_px: np.ndarray) -> tuple[np.ndarray, ...]:
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


def touched(entries: np.ndarray, holds: np.ndarray, low: np.ndarray, high: np.ndarray,
            stop: np.ndarray, target: np.ndarray, reach: int) -> tuple[np.ndarray, ...]:
    """The first bar of each trade's life on which a price barrier is reached.

    Args:
        entries: Entry bar index of each trade.
        holds: Bars until the vertical barrier.
        low, high: Extremes of every bar.
        stop, target: Price level of each trade's lower and upper barrier.
        reach: Bars scanned ahead, `holds.max()`.

    Returns:
        (offset of the first touch, whether the stop was touched there, whether the target
        was). An offset of 0 means neither was reached before the vertical barrier. The
        scan is one boolean matrix of shape (trades, reach + 1): `sliding_window_view` makes
        the windows a view, so only the comparison allocates, and the caller chunks to keep
        that allocation bounded.
    """
    window = np.arange(reach + 1)
    live = (window[None, :] >= 1) & (window[None, :] <= holds[:, None])
    hit_stop = (sliding_window_view(low, reach + 1)[entries] <= stop[:, None]) & live
    hit_target = (sliding_window_view(high, reach + 1)[entries] >= target[:, None]) & live
    either = hit_stop | hit_target
    offset = np.where(either.any(axis=1), either.argmax(axis=1), 0)
    rows = np.arange(len(entries))
    return offset, hit_stop[rows, offset], hit_target[rows, offset]


def exits(entries: np.ndarray, holds: np.ndarray, bars: dict, levels: dict,
          intrabar: str) -> tuple[np.ndarray, ...]:
    """Where every trade leaves, and at what price.

    Args:
        entries: Entry bar index of each trade.
        holds: Bars until the vertical barrier.
        bars: Keys `low`, `high`, `enter_px`, `leave_px`, one array per bar. The two
            price arrays come from `calibrate.convention()`, never assumed.
        levels: Keys `stop` and `target`, one price per trade, or empty when the strategy
            carries neither -- the degenerate case this corpus is in.
        intrabar: Which barrier wins when one bar's range touches both, a key of FIRST.
            Unreadable from OHLC, so it is a declared convention; `calibrate.convention()`
            is what settles it against SQX once a strategy actually carries barriers.

    Returns:
        (exit bar index, exit price). A trade that reaches neither barrier leaves on its
        vertical one at that bar's close; one that reaches a barrier leaves **at the
        barrier's own price**, which is what a resting order fills at.
    """
    if not levels:
        return vertical(entries, holds, bars["leave_px"])
    stop, target = levels["stop"], levels["target"]
    offset, on_stop, on_target = touched(entries, holds, bars["low"], bars["high"],
                                         stop, target, int(holds.max()))
    both = on_stop & on_target
    wins_stop = (on_stop & ~on_target) | (both & (FIRST[intrabar] == "sl"))
    leave = np.where(offset > 0, entries + offset, entries + holds)
    price = np.where(offset == 0, bars["leave_px"][leave], np.where(wins_stop, stop, target))
    return leave, price


def pnl(entries: np.ndarray, leave: np.ndarray, price: np.ndarray, sizes: np.ndarray,
        enter_px: np.ndarray, cost: np.ndarray, value: float) -> np.ndarray:
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
