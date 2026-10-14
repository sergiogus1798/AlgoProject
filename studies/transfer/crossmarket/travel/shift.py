"""The joint draw: one whole-step displacement per calendar cell and run, the same in every market."""

import numpy as np
import pandas as pd

from engines.nulls.placement.trade_models import semester_shift

DAY, WEEK = 86400, 7 * 86400
MONDAY = -3 * DAY  # 1969-12-29 00:00, the Monday weeks are counted from
EPOCH = np.datetime64("1970-01-01")


def draws(cells: pd.DataFrame, seed: int, count: int) -> np.ndarray:
    """The displacement of every cell in every run.

    Args:
        cells: As cells.table() returns it.
        seed: travel.seed.
        count: travel.draws.

    Returns:
        (count, cells) whole steps, each in 0..steps-1 of its cell. The generator is keyed by
        the cell's own start date (engines' `semester_shift`), never by a market, so run b
        moves 2014 by the same weeks everywhere: that is what makes the null joint.
    """
    keys = cells["start"].to_numpy("datetime64[D]").astype(np.int64)
    return np.column_stack(
        [
            (semester_shift(seed, int(key), count, 0)[:, 0] * steps).astype(np.int64)
            for key, steps in zip(keys, cells["steps"])
        ]
    )


def _slot(seconds: np.ndarray, step: str) -> tuple[np.ndarray, np.ndarray]:
    """A stamp as (which step it is in, where inside the step): the week and the weekday-hour,
    or the business day and the hour."""
    if step == "week":
        return (seconds - MONDAY) // WEEK, (seconds - MONDAY) % WEEK
    # ponytail: a Saturday or Sunday bar counts as the following Monday under `day`; no feed
    # carries weekend bars today. Count calendar days for a market that trades weekends.
    return np.busday_count(
        EPOCH, (seconds // DAY).astype("datetime64[D]")
    ), seconds % DAY


def _stamp(ordinal: np.ndarray, offset: np.ndarray, step: str) -> np.ndarray:
    """The inverse of _slot: epoch seconds."""
    if step == "week":
        return MONDAY + ordinal * WEEK + offset
    return np.busday_offset(EPOCH, ordinal).astype(np.int64) * DAY + offset


def entries(
    seconds: np.ndarray,
    entry: np.ndarray,
    cell: np.ndarray,
    cells: pd.DataFrame,
    shifts: np.ndarray,
    step: str,
) -> np.ndarray:
    """Where each real entry lands in each run: moved rigidly inside its cell, wrapping round.

    The move is calendar arithmetic, not a count of this market's bars, so the same shift is
    the same instant in every market; a stamp with no bar (a holiday) takes the next bar.

    Args:
        seconds: One market's bar open times, epoch seconds, ascending.
        entry: Bar position of each real entry.
        cell: The cell of each of those entries.
        cells: As cells.table() returns it.
        shifts: (runs, cells) whole steps, from draws().
        step: travel.shift_step.

    Returns:
        (runs, trades) bar positions; a position equal to len(seconds) is past the last bar.
        A cell this market covers only in part wraps inside the part it has bars for.
    """
    edge = cells[["start", "end"]].to_numpy("datetime64[s]").astype(np.int64)
    lo = np.maximum(edge[:, 0], seconds[0])[cell]
    hi = np.minimum(edge[:, 1], seconds[-1] + 1)[cell]
    own, offset = _slot(seconds[entry], step)
    base = _slot(lo, step)[0] - 1
    stamps = _stamp(
        base[:, None] + np.arange(int(cells["steps"].max()) + 4), offset[:, None], step
    )
    inside = (stamps >= lo[:, None]) & (stamps < hi[:, None])
    first, count = inside.argmax(1), inside.sum(1)
    column = first + (own - base - first + shifts[:, cell]) % count
    return np.searchsorted(seconds, stamps)[np.arange(entry.size), column]
