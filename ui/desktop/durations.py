"""How the generation zone prints a duration, a processed-over-total and a time per strategy."""


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
        `300 / 1000`, `100 / ·` for a build (no total), «·» before it started.
    """
    done = "·" if t["done"] is None else str(t["done"])
    total = "·" if t["total"] is None else str(t["total"])
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
    return f"{ms:.0f} ms" if ms < 1000 else f"{ms / 1000:.1f} s"
