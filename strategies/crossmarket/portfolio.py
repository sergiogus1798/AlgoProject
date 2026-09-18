"""The same strategy in several markets, as one account: does adding a market break it?

Not a portfolio construction and not a substitute for strategies/monteCarlo — that study asks
how much of one stream is luck. This asks a narrower question the cross-market retest raises on
its own: oil and the Nasdaq need not be brilliant, but they must not wreck what gold does.

The drawdown of a combination is computed on the **combined** curve, never summed from the
parts, as portfolio/CLAUDE.md requires."""

import numpy as np
import pandas as pd

from strategies.crossmarket import bootstrap, curves, metrics
from strategies.monteCarlo.model import draws as mcdraws

CHUNK = 500     # draws priced per batch; the padded position matrix is the memory, not the maths


def priced(fixed: dict, feed: str) -> pd.DataFrame:
    """One market's trades reduced to what a combined account needs.

    Args:
        fixed: What backtest.setting() returned.
        feed: That market's SQX symbol.

    Returns:
        Columns feed, open, close and pnl, over **every** trade SQX reported — a combined
        account that quietly omitted the trades the bar grid could not hold would not be the
        account anyone lived through. Kept in the session record instead of the whole `fixed`
        dict, which carries a price array per bar: this is four columns per trade and it is
        everything the portfolio, and a later merge of it, ever reads.
    """
    return pd.DataFrame({"feed": feed, "open": fixed["all"]["open"],
                         "close": fixed["all"]["close"], "pnl": fixed["all"]["pnl"]})


def stream(streams: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Every market's real trades merged into one time-ordered account.

    Args:
        streams: {feed: what priced() returned}, the base asset included.

    Returns:
        One frame sorted by close time — when the money is realised. The P&L is each market's
        own dollars at its own real position sizes: no rescaling, so this is what the
        combination actually did, not what a sized version of it would do.
    """
    return pd.concat(streams.values(), ignore_index=True).sort_values(
        "close").reset_index(drop=True)


def account(pnl: np.ndarray, cfg: dict) -> dict:
    """The statistics of one combined account.

    Args:
        pnl: Trade P&L in USD, in the order the trades closed.
        cfg: What config.load() returned.

    Returns:
        What metrics.observed() returned. One account of equity.starting for the whole
        combination — not one per market — because that is the drawdown a person operating
        all of them at once would actually have lived through.
    """
    return metrics.observed(pnl, cfg["equity"]["starting"])


def marginal(merged: pd.DataFrame, cfg: dict) -> list[dict]:
    """What each market adds to, or takes from, the combined account.

    Args:
        merged: What stream() returned.
        cfg: What config.load() returned.

    Returns:
        One row per market: the whole portfolio, the portfolio without that market, and the
        difference on every statistic. **This is the table the tab exists for.** A market
        whose removal improves Ret/DD is costing the combination more than it brings, however
        good its own p-value looked.
    """
    whole = account(merged["pnl"].to_numpy(), cfg)
    out = []
    for feed in merged["feed"].unique():
        rest = merged.loc[merged["feed"] != feed, "pnl"].to_numpy()
        without = account(rest, cfg) if rest.size else {k: float("nan") for k in whole}
        out.append({"feed": feed, "trades": int((merged["feed"] == feed).sum()),
                    "without": without,
                    "delta": {k: whole[k] - without[k] for k in whole}})
    return out


def overlap(merged: pd.DataFrame) -> dict:
    """How much of the time more than one market was open at once.

    Args:
        merged: What stream() returned.

    Returns:
        Keys share (of the time at least one position was open, how much had two or more) and
        most (the largest number open at once). Four uncorrelated markets that nevertheless
        enter on the same day are not diversifying anything, and the correlation of weekly
        equity does not show it — this does.
    """
    edges = np.concatenate([merged["open"].to_numpy(), merged["close"].to_numpy()])
    moves = np.concatenate([np.ones(len(merged)), -np.ones(len(merged))])
    # A close and an open at the same instant are one position handing over to the next, not
    # two open at once: closes go first, or a strategy that re-enters on its own exit bar
    # reports more concurrent positions than it has markets.
    order = np.lexsort((moves, edges))
    times, level = edges[order], np.cumsum(moves[order])
    span = (times[1:] - times[:-1]) / np.timedelta64(1, "D")
    live, many = level[:-1] >= 1, level[:-1] >= 2
    return {"share": float(span[many].sum() / max(span[live].sum(), 1e-9)),
            "most": int(level.max())}


def calendar_blocks(merged: pd.DataFrame, weeks: int) -> np.ndarray:
    """Which calendar block each trade closed in.

    Args:
        merged: What stream() returned.
        weeks: Block length.

    Returns:
        One block id per trade. Blocks are **calendar** time, not trade count: the dependence
        that matters in a portfolio is contemporaneous — two markets losing in the same week —
        and resampling single trades would destroy exactly the thing being measured.
    """
    day = (merged["close"] - merged["close"].min()).dt.days.to_numpy()
    return day // (7 * weeks)


def laid(members: list[np.ndarray], picks: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Lay a batch of block draws out as one padded matrix of trade positions.

    Args:
        members: Trade positions of each calendar block, in time order.
        picks: (draws, blocks) of block indices, drawn with replacement.

    Returns:
        (positions, live): one row per draw, the drawn blocks concatenated in the order they
        were drawn and padded to the widest row, with `live` False in the padding. Built in
        one pass instead of a Python loop per draw — 2,000 draws of 170 blocks each was nine
        seconds of concatenating small arrays, and metrics.paths() already takes a `live`
        mask because the null models need one.
    """
    order = np.concatenate(members)
    starts = np.cumsum([0] + [m.size for m in members])[:-1]
    lens = np.array([m.size for m in members])[picks]
    offsets = np.cumsum(lens, axis=1) - lens
    flat = lens.ravel()
    within = np.arange(flat.sum()) - np.repeat(np.cumsum(flat) - flat, flat)
    rows = np.repeat(np.repeat(np.arange(picks.shape[0]), picks.shape[1]), flat)
    cols = np.repeat(offsets.ravel(), flat) + within
    out = np.zeros((picks.shape[0], int(lens.sum(axis=1).max())), dtype=np.int64)
    live = np.zeros(out.shape, dtype=bool)
    out[rows, cols] = order[np.repeat(starts[picks].ravel(), flat) + within]
    live[rows, cols] = True
    return out, live


def resampled(merged: pd.DataFrame, cfg: dict, rng: np.random.Generator) -> dict:
    """Confidence intervals on the combination, by resampling whole calendar blocks.

    Args:
        merged: What stream() returned.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        A percentile interval per statistic. Every market's trades inside a drawn block travel
        together, so a bad week for gold and silver at once stays a bad week for both — which
        is the whole reason the blocks are calendar time and not trade count.
    """
    p = cfg["portfolio"]
    block = calendar_blocks(merged, p["block_weeks"])
    members = [np.flatnonzero(block == b) for b in np.unique(block)]
    pnl = merged["pnl"].to_numpy()
    stats: dict[str, list[np.ndarray]] = {}
    for done in range(0, p["draws"], CHUNK):
        picks = rng.integers(0, len(members), (min(CHUNK, p["draws"] - done), len(members)))
        positions, live = laid(members, picks)
        for k, v in metrics.paths(np.where(live, pnl[positions], 0.0), live,
                                  cfg["equity"]["starting"]).items():
            stats.setdefault(k, []).append(v)
    return {k: bootstrap.percentile_ci(np.concatenate(v)[np.isfinite(np.concatenate(v))],
                                       *cfg["bootstrap"]["ci"])
            for k, v in stats.items()}


def reordered(merged: pd.DataFrame, cfg: dict, rng: np.random.Generator) -> dict:
    """The same trades in a different order, to price how much the sequence mattered.

    Args:
        merged: What stream() returned.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        What metrics.table() returns for the reordered runs against the real one. The
        reordering itself comes from strategies.monteCarlo.model.draws, which owns this family:
        duplicating it here would be two copies of one decision. It answers a different
        question from resampled() — composition is untouched, only the order changes — so net
        profit is invariant by construction and only the path statistics move.
    """
    p = cfg["portfolio"]
    pnl = merged["pnl"].to_numpy()
    picks = mcdraws.block_shuffle(p["draws"], pnl.size, rng, p["order_block"])
    paths = metrics.paths(pnl[picks], np.ones(picks.shape, dtype=bool),
                          cfg["equity"]["starting"])
    return metrics.table(paths, account(pnl, cfg), cfg["equity"]["percentiles"])


def run(streams: dict[str, pd.DataFrame], cfg: dict, rng: np.random.Generator) -> dict:
    """The whole portfolio view of one strategy across its markets.

    Args:
        streams: {feed: what priced() returned}, base asset included.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        The combined account's statistics, the marginal contribution of every market, how
        often positions overlapped, the calendar-block intervals and the reordering table.
        No verdict: the marginal table is read by the owner, who decides what "breaks" means.
    """
    merged = stream(streams)
    return {"markets": list(streams), "trades": len(merged),
            "curves": curves.combined(merged, cfg),
            "whole": account(merged["pnl"].to_numpy(), cfg),
            "marginal": marginal(merged, cfg), "overlap": overlap(merged),
            "ci": resampled(merged, cfg, rng), "order": reordered(merged, cfg, rng),
            "from": str(merged["close"].min().date()),
            "to": str(merged["close"].max().date())}
