"""How «En marcha» prints a duration, a processed-over-total and a time per strategy."""

from ui.text.numbers import num


def clock(seconds: int | None) -> str:
    """Seconds as the zone prints a duration.

    Args:
        seconds: Whole seconds, or None.

    Returns:
        `47 s`, `8 min 3 s` or `2 h 14 min`; «·» for None.
    """
    if seconds is None:
        return "·"
    if seconds < 60:
        return f"{seconds} s"
    if seconds < 3600:
        return f"{seconds // 60} min {seconds % 60} s"
    return f"{seconds // 3600} h {seconds % 3600 // 60} min"


def ratio(t: dict) -> str:
    """A task's processed strategies over its input.

    Args:
        t: A task row of `/api/progress`.

    Returns:
        `300 / 1 000`, `100 / ·` for a build (no total), «·» before it started.
    """
    done = "·" if t["done"] is None else num(t["done"])
    total = "·" if t["total"] is None else num(t["total"])
    return f"{done} / {total}"


def per(t: dict) -> str:
    """A task's time per strategy.

    Args:
        t: A task row.

    Returns:
        Milliseconds below a second, seconds above; «·» when unknown.
    """
    ms = t["per_strategy_ms"]
    if not ms:
        return "·"
    return f"{num(round(ms))} ms" if ms < 1000 else f"{num(round(ms / 1000, 1))} s"


def share(done: int | None, total: int | None, percent: int | None = None) -> int | None:
    """How far a task is, 0-100, for a progress bar.

    Args:
        done: Processed so far, or None.
        total: Its input, or None (a build has none).
        percent: SQX's own figure when its log carries one; it wins.

    Returns:
        The percentage, or None when nothing says how far: the bar then only shows motion.
    """
    if percent is not None:
        return int(percent)
    if done is None or not total:
        return None
    return min(100, round(100 * done / total))
