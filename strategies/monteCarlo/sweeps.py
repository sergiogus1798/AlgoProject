"""Which reordering and resampling runs a stream of this size gets, and the numbers they give."""

from strategies.monteCarlo import config, draws, engine

HEADLINE = "stationary"     # its drawdown distribution is the order-luck one the gates read
BASELINE = "iid_bootstrap"  # the independence baseline of the composition family


def plan(n_trades: int, cfg: dict) -> list[dict]:
    """Every sub-run of Families A and B for a stream of this length.

    Args:
        n_trades: Trades in the stream.
        cfg: What config.load() returned.

    Returns:
        One dict per sub-run with its label, model, block length and family. The block
        sweep is scaled to N and disappears entirely when N cannot support min_blocks
        blocks of the smallest size — a sweep that cannot randomise is skipped and flagged,
        never run degenerate.
    """
    blocks = config.block_sizes(n_trades, cfg)
    out = [("iid_shuffle", "iid_shuffle", 0, "A")]
    out += [(f"block_shuffle/{b}", "block_shuffle", b, "A") for b in blocks]
    out.append((HEADLINE, "stationary", config.stationary_block(n_trades), "A"))
    out.append((BASELINE, "iid_bootstrap", 0, "B"))
    out += [(f"block_bootstrap/{b}", "block_bootstrap", b, "B") for b in blocks]
    return [{"label": label, "model": model, "block": block, "family": family,
             "title": draws.title(model, block)} for label, model, block, family in out]


def execute(data: dict, steps: list[dict], n_sims: int, cfg: dict) -> dict:
    """Run every sub-run of a plan.

    Args:
        data: What engine.payload() returned.
        steps: What plan() returned, or a subset of it.
        n_sims: Simulations per sub-run.
        cfg: What config.load() returned.

    Returns:
        {label: one array per statistic}. The raw arrays travel back rather than summaries
        because the same pool is asked several questions — percentiles, ranks, histograms
        and the Sharpe cross-check of Family E all read the same draws.
    """
    return {s["label"]: engine.run(data, "draw", s["model"], s["block"], n_sims, cfg,
                                   s["title"])
            for s in steps}


def invariant(stats: dict) -> float:
    """How far a composition-preserving run moved net profit, which must be nowhere.

    Args:
        stats: One label's arrays, from execute().

    Returns:
        The standard deviation of net profit across the simulations, in USD. For
        iid_shuffle and block_shuffle it is zero up to floating point: the same trades in
        another order add up to the same total, and anything else is a bug in the model
        rather than a property of the strategy.
    """
    return float(stats["net"].std())
