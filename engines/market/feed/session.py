"""A feed's trading week as a minute-of-week mask: deduced from the feed, written and read as text."""

import numpy as np

from engines.market.feed.scale import WEEK

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def deduce(at: np.ndarray, first_year_min: int, last_year_min: int, share: float) -> np.ndarray:
    """The minutes of the week the feed quotes in most weeks of a span.

    Args:
        at: Bar times in whole minutes (engines.market.feed.scale.minutes).
        first_year_min, last_year_min: The span, as the minute numbers that open and close it.
        share: A minute is in session when at least this share of the span's weeks has a bar.

    Returns:
        A bool mask of WEEK minutes, Monday 00:00 first.
    """
    inside = at[(at >= first_year_min) & (at < last_year_min)]
    weeks = len(np.unique(inside // WEEK))
    return np.bincount(inside % WEEK, minlength=WEEK) >= share * weeks


def _clock(minute: int) -> str:
    """Minute of the week as "Mon 01:00"; the end of Friday reads "Sat 00:00"."""
    day, rest = divmod(minute, 1440)
    return f"{DAYS[day % 7]} {rest // 60:02d}:{rest % 60:02d}"


def text(mask: np.ndarray) -> str:
    """The mask as the intervals it holds, e.g. "Mon 01:00-Tue 00:00, Tue 01:00-Wed 00:00".

    Args:
        mask: A WEEK-long bool mask.

    Returns:
        Comma-separated half-open intervals, the form the ledger stores.
    """
    edges = np.flatnonzero(np.diff(np.r_[0, mask.astype(np.int8), 0]))
    return ", ".join(f"{_clock(a)}-{_clock(b)}" for a, b in zip(edges[::2], edges[1::2]))


def mask(spec: str) -> np.ndarray:
    """The inverse of text().

    Args:
        spec: As text() writes it.

    Returns:
        A WEEK-long bool mask.
    """
    out = np.zeros(WEEK, bool)
    for part in spec.split(", "):
        bounds = []
        for end in part.split("-"):
            day, clock = end.split(" ")
            hh, mm = clock.split(":")
            bounds.append(DAYS.index(day) * 1440 + int(hh) * 60 + int(mm))
        a, b = bounds
        out[a:b if b > a else WEEK] = True
    return out


def without_hours(week_mask: np.ndarray, hours: list[int]) -> np.ndarray:
    """The session with some clock hours of every day taken out.

    Args:
        week_mask: A WEEK-long bool mask.
        hours: Hours of the feed's clock, 0-23.

    Returns:
        A copy with those hours False on every day.
    """
    hour = (np.arange(WEEK) % 1440) // 60
    return week_mask & ~np.isin(hour, hours)


def prefix(week_mask: np.ndarray, at: np.ndarray) -> np.ndarray:
    """How many in-session minutes lie before each absolute minute.

    Args:
        week_mask: A WEEK-long bool mask.
        at: Absolute minutes.

    Returns:
        int64 per minute: P(a) = in-session minutes in [0, a), so the in-session minutes of
        [a, b) are P(b) - P(a).
    """
    cum = np.r_[0, np.cumsum(week_mask)]
    return (at // WEEK) * cum[-1] + cum[at % WEEK]
