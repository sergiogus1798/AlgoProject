"""The strategy-level views, built from what each market contributed: correlation and the joint null.

They exist apart from orchestrate/strategy.py because a single-market re-run has to rebuild
them from the markets already in the session plus the one just recomputed — the panel's
per-market **run** button merges into a record rather than replacing it, and a correlation
matrix that still described the old market would be silently wrong."""

from studies.transfer.crossmarket.simulate import correlation, joint


def build(weekly: dict, runs: dict, cfg: dict) -> dict:
    """Everything that needs more than one market at once.

    Args:
        weekly: {feed: what correlation.weekly_equity() returned}.
        runs: {feed: that market's model results}, for the joint null.
        cfg: What config.load() returned.

    Returns:
        Keys correlation and joint. The base asset is in the first: the correlation matrix
        needs it because the question is whether the additional markets add anything to it.
        It is **not** in the joint null, which is a test and not a description: on the market
        it was optimised on a strategy beats its null by construction, and `runs` carries the
        out-of-sample markets only.
    """
    return {"correlation": correlation.correlation_matrix(weekly).to_dict(),
            "joint": joint.run(runs, cfg)}
