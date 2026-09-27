"""The discrete colour scale of an outcome: nine round, equal steps symmetric about zero, and its key."""

import math

from ui.desktop.blocks.chart import num
from ui.desktop.blocks.states import DIVERGING
from ui.desktop.theme import C

MISSING = C["pending"]


def edges(values: list) -> list[float]:
    """Ten cut points symmetric about zero, every step one round width wide.

    Args:
        values: The outcome per variant, None where missing.

    Returns:
        Cut points at (i - 4.5) × w, w the smallest of 1, 2, 2.5 or 5 × 10^k that covers the
        largest absolute value: zero sits inside the pale middle step, losses red, gains blue.
    """
    top = max((abs(v) for v in values if v is not None), default=1.0) or 1.0
    need = top / (len(DIVERGING) / 2)
    mag = 10 ** math.floor(math.log10(need))
    width = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= need)
    half = len(DIVERGING) / 2
    return [(i - half) * width for i in range(len(DIVERGING) + 1)]


def step(v: float | None, cuts: list[float]) -> int | None:
    """The step a value falls in.

    Args:
        v: The value, None when missing.
        cuts: As `edges` returns them.

    Returns:
        0..8, None for a missing value.
    """
    if v is None:
        return None
    return min(len(DIVERGING) - 1, max(0, int((v - cuts[0]) / (cuts[1] - cuts[0]))))


def colour(v: float | None, cuts: list[float]) -> str:
    """The colour of one value.

    Args:
        v, cuts: As in `step`.

    Returns:
        A hex colour; grey for a missing value.
    """
    s = step(v, cuts)
    return MISSING if s is None else DIVERGING[s]


def key(values: list, cuts: list[float]) -> list[tuple[str, str, str]]:
    """The legend: each step's range and how many variants fall in it.

    Args:
        values, cuts: As above.

    Returns:
        (mark, colour, text) items for `chart.key`; empty steps are left out.
    """
    counts = [0] * len(DIVERGING)
    for v in values:
        if v is not None:
            counts[step(v, cuts)] += 1
    # No-break spaces: a range split across two lines of the key reads as two ranges.
    items = [("line", DIVERGING[i],
              f"{num(cuts[i])} a {num(cuts[i + 1])}: {counts[i]}".replace(" ", "\u00a0"))
             for i in range(len(DIVERGING)) if counts[i]]
    gone = sum(v is None for v in values)
    return items + ([("line", MISSING, f"sin valor: {gone}")] if gone else [])
