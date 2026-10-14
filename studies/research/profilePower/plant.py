"""The planted edge: which bars carry it, and the series with it added."""

import numpy as np

from studies.research.marketProfile import series


def covered(entry: np.ndarray, leave: np.ndarray, n: int) -> np.ndarray:
    """The bars at least one trade holds: from its entry bar to the bar before its exit."""
    steps = np.zeros(n + 1)
    np.add.at(steps, entry, 1)
    np.add.at(steps, leave, -1)
    return np.cumsum(steps)[:n] > 0


def condition(held: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """The bars that follow the measure's own condition: the edge is the measure's."""
    return held


def random(held: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """As many bars, anywhere: the same drift where no rule fires."""
    out = np.zeros(held.size, dtype=bool)
    out[rng.choice(held.size, int(held.sum()), replace=False)] = True
    return out


# Where the edge goes. One signature: (bars the measure's trades hold, rng) -> bars that
# receive the extra return. Adding a third is a function and a row here.
PLANTS = {"condition": condition, "random": random}
HOLDS = {
    "condition": "the measure sees a mean gain of `effect` costs per trade: this is the power",
    "random": "the series gains the same total drift and the measure's trades none of it but "
    "by chance: this is the control, it must detect at the rate of no effect",
}


def planted(
    base: dict,
    entry: np.ndarray,
    leave: np.ndarray,
    sign: int,
    effect: float,
    cost: np.ndarray,
    how: str,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """A series with an edge of known size added to the returns of the chosen bars.

    Args:
        base: What series.logs() returns: the series the measure's trades were read on.
        entry, leave: The measure's trades on `base` (entry bar, exit bar; open to open).
        sign: +1 for a long edge, -1 for a short one.
        effect: Mean gross gain per trade, in round-trip costs.
        cost: One round trip's cost at each bar, as a log return (inputs.cost_log).
        how: A key of PLANTS.
        rng: Generator.

    Returns:
        What series.logs() returns. Every chosen bar's close moves by `effect` costs over the
        mean holding time, so a trade gains `effect` costs on average whether or not trades
        overlap; highs and lows are widened only where the close would leave the bar.
    """
    held = covered(entry, leave, base["c"].size)
    where = PLANTS[how](held, rng)
    g = series.gaps(base)
    close = g["c"] + where * sign * effect * cost / (leave - entry).mean()
    return series.path(
        {
            "o": g["o"],
            "c": close,
            "h": np.maximum(g["h"], close),
            "l": np.minimum(g["l"], close),
        },
        base["o"][0],
    )
