"""How a figure is written on MetaTracker's screens: the Spanish way, and «—» where there is none."""
from datetime import datetime, timezone

DASH = "—"


def money(x: float | None) -> str:
    """A figure the Spanish way: 9.744,36; None is a dash."""
    if x is None:
        return DASH
    return f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x: float | None, digits: int = 1) -> str:
    """A share as a Spanish percentage: 0.8 -> 80,0 %."""
    if x is None:
        return DASH
    return f"{100 * x:.{digits}f}".replace(".", ",") + " %"


def clock(epoch: int | None) -> str:
    """A server-clock epoch as day-month and time."""
    if epoch is None:
        return DASH
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%d-%m %H:%M")


def day(epoch: int | None) -> str:
    """A server-clock epoch as day-month."""
    if epoch is None:
        return DASH
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%d-%m")


def span(seconds: float) -> str:
    """A span in the largest unit that reads well: 40 s, 12 min, 1 h 45 min, 3 h, 2 d."""
    seconds = int(seconds)
    if seconds >= 86400:
        return f"{seconds // 86400} d"
    if seconds >= 3600:
        h, m = divmod(seconds // 60, 60)
        return f"{h} h {m} min" if m else f"{h} h"
    if seconds >= 60:
        return f"{seconds // 60} min"
    return f"{seconds} s"
