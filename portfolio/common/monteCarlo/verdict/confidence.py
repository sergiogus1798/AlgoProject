"""Whether the sample can hold up a number. Every statistic in the report carries one of these."""

TIERS = ("reliable", "provisional", "unreliable")
TAIL_RELIABLE, TAIL_PROVISIONAL = 10, 4
MEAN_RELIABLE, MEAN_PROVISIONAL = 30, 10


def percentile(n: int, q: float) -> str:
    """How much a percentile of a sample of this size can be trusted.

    Args:
        n: Trades the statistic was computed from.
        q: The percentile, 0-100.

    Returns:
        One of TIERS, from the expected count in the tail, n * min(q, 1-q). The 99th
        percentile of 100 trades rests on one observation and is called unreliable; the
        95th of 400 rests on twenty and is not.
    """
    tail = n * min(q, 100 - q) / 100
    if tail >= TAIL_RELIABLE:
        return TIERS[0]
    return TIERS[1] if tail >= TAIL_PROVISIONAL else TIERS[2]


def average(n: int) -> str:
    """How much a mean or a median of a sample of this size can be trusted.

    Args:
        n: Trades the statistic was computed from.

    Returns:
        One of TIERS.
    """
    if n >= MEAN_RELIABLE:
        return TIERS[0]
    return TIERS[1] if n >= MEAN_PROVISIONAL else TIERS[2]


def blocks(n: int, block: int, min_blocks: int) -> str:
    """Whether a block method has enough blocks to randomise anything.

    Args:
        n: Trades in the stream.
        block: Block length.
        min_blocks: Blocks the config demands.

    Returns:
        "reliable" or "unreliable". Below the floor the permutation has almost nothing to
        permute and its distribution collapses onto the observed path.
    """
    return TIERS[0] if n // block >= min_blocks else TIERS[2]


def worst(tiers: list[str]) -> str:
    """The weakest tier of a set of statistics.

    Args:
        tiers: Tiers of the statistics that drove a decision.

    Returns:
        The worst one. A verdict is only as good as the least supported number under it,
        which is why the data gate reads this and not an average.
    """
    return next(t for t in reversed(TIERS) if t in tiers) if tiers else TIERS[2]
