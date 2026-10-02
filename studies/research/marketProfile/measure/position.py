"""One position at a time: a rule's entry and exit bars when the exit is a condition, not a count."""

import numpy as np
from numba import njit


@njit(cache=True)
def walk(enter: np.ndarray, leave: np.ndarray, cap: int, trail: float, close: np.ndarray,
         ruler: np.ndarray, stop: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """Entry and exit bars of a rule that holds one position at a time.

    Args:
        enter: True on the bars whose CLOSE gives the entry signal.
        leave: True on the bars whose close gives the exit signal.
        cap: Most bars a trade is held; 0 for no limit.
        trail: Trailing exit: leave when the close falls this many `ruler` below the highest
            close since the signal; 0 for none.
        close: Log closes.
        ruler: The distance unit of the trailing exit and of the stop, per bar (an ATR, in logs).
        stop: Protective stop: leave when the close falls this many `ruler` (as it stood on
            the signal bar) below the signal bar's close; 0 for none.

    Returns:
        (entry, exit) bar indices, both fills at the OPEN of the bar after the signal — the
        open-to-open convention of `trades.after`. A signal while a position is open is
        ignored; the exit bar's own close may signal the next entry. A trade the series ends
        before closing is dropped.
    """
    n = close.size
    entry, out = np.empty(n, np.int64), np.empty(n, np.int64)
    count, i = 0, 0
    while i < n - 2:
        if not enter[i]:
            i += 1
            continue
        top, j, done = close[i], i + 1, False
        floor = close[i] - stop * ruler[i]
        while j < n - 1:
            if close[j] > top:
                top = close[j]
            if (leave[j] or (cap > 0 and j - i >= cap)
                    or (trail > 0 and close[j] < top - trail * ruler[j])
                    or (stop > 0 and close[j] < floor)):
                done = True
                break
            j += 1
        if not done:
            break
        entry[count], out[count] = i + 1, j + 1
        count += 1
        i = j
    return entry[:count], out[:count]
