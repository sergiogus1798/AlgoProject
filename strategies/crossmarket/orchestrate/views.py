"""The strategy-level views, built from what each market contributed: correlation and portfolio.

They exist apart from orchestrate/strategy.py because a single-market re-run has to rebuild
them from the markets already in the session plus the one just recomputed — the panel's
per-market **run** button merges into a record rather than replacing it, and a correlation
matrix or a combined account that still described the old market would be silently wrong."""

import numpy as np

from strategies.crossmarket.simulate import correlation, joint, portfolio


def build(weekly: dict, streams: dict, runs: dict, cfg: dict) -> dict:
    """Everything that needs more than one market at once.

    Args:
        weekly: {feed: what correlation.weekly_equity() returned}.
        streams: {feed: the trade stream simulate/portfolio.py takes} — feed, open, close and pnl.
        runs: {feed: that market's model results}, for the joint null.
        cfg: What config.load() returned.

    Returns:
        Keys correlation, portfolio and joint. The base asset is in the first two: the
        correlation matrix needs it because the question is whether the additional markets add
        anything to it, and the combined account needs it because the portfolio the owner
        would trade has gold in it. It is **not** in the joint null, which is a test and not a
        description: on the market it was optimised on a strategy beats its null by
        construction, and `runs` carries the out-of-sample markets only.
    """
    rng = np.random.default_rng(cfg["nulls"]["seed"])
    return {"correlation": correlation.correlation_matrix(weekly).to_dict(),
            "portfolio": portfolio.run(streams, cfg, rng),
            "joint": joint.run(runs, cfg)}
