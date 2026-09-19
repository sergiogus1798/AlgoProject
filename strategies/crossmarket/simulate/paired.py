"""Test 1b — each real trade against the average blind trade of its own length, near it in time.

Two ways of saying "near it in time", because the answer must not depend on which one is
chosen: a **centered** window of the entry's own neighbourhood, and the fixed **calendar
block** partition block_shift moves trades inside. Both are exact — every legal start bar in
the reference, never a sample of them — and the panel prints the test under both."""

import numpy as np
import pandas as pd
from scipy import stats

from strategies.crossmarket.mechanics import pricing, units
from strategies.crossmarket.model import bootstrap

BLOCK = "block"      # the sensitivity entry that means the regime-block partition, not a width


def half_bars(bars: pd.DataFrame, months: float) -> int:
    """A half-width in months, expressed in bars of this market.

    Args:
        bars: One market's bars, already sliced to the backtest's window.
        months: Half-width, e.g. 3 for a window of +/- 3 months.

    Returns:
        Bars either side. Measured in **market time**, not calendar time: equal counts of
        bars are equal stretches of trading, which is the same axis equity.bin_of() uses, and
        it means a holiday week costs the window nothing.
    """
    span = (bars.index[-1] - bars.index[0]).days / 30.44
    return max(int(round(len(bars) * months / span)), 1) if span else len(bars)


def centered_means(enter_px: np.ndarray, leave_px: np.ndarray, hold: int,
                   half: int) -> np.ndarray:
    """Mean return of every window of one length, averaged over each bar's own neighbourhood.

    Args:
        enter_px: Fill price for an entry on each bar.
        leave_px: Fill price for an exit on each bar.
        hold: Window length in bars.
        half: Bars either side of a trade's entry that its reference averages over.

    Returns:
        One mean per bar: the average of every blind trade of that duration starting within
        `half` bars of it. A running mean by cumulative sum, so it costs one pass whatever the
        width. It reads bars **after** the entry as well as before — the reference is "what
        this market was paying around then", not a rule anyone could have traded.
    """
    value = np.full(enter_px.size, np.nan)
    start = np.arange(enter_px.size - hold)
    value[start] = np.log(leave_px[start + hold] / enter_px[start])
    ok = np.isfinite(value)
    total = np.concatenate([[0.0], np.cumsum(np.where(ok, value, 0.0))])
    count = np.concatenate([[0], np.cumsum(ok)])
    lo = np.maximum(np.arange(value.size) - half, 0)
    hi = np.minimum(np.arange(value.size) + half + 1, value.size)
    n = count[hi] - count[lo]
    return np.divide(total[hi] - total[lo], n, out=np.full(value.size, np.nan), where=n > 0)


def block_means(enter_px: np.ndarray, leave_px: np.ndarray, block: np.ndarray,
                hold: int) -> np.ndarray:
    """Mean return of every window of one length, per regime block.

    Args:
        enter_px: Fill price for an entry on each bar.
        leave_px: Fill price for an exit on each bar.
        block: One regime-block id per bar.
        hold: Window length in bars.

    Returns:
        One mean per bar, taken from the block that bar belongs to. Every legal start bar of
        the block is used, so it is the exact expected return of a blind trade of that
        duration there. Its defect, and the reason the centered window exists: a trade
        entering three days before the block ends is measured against a reference that is
        almost entirely past, and two trades a week apart across a boundary get disjoint ones.
    """
    start = np.arange(len(enter_px) - hold)
    value = np.log(leave_px[start + hold] / enter_px[start])
    total = np.bincount(block[start], weights=value, minlength=block.max() + 1)
    count = np.bincount(block[start], minlength=block.max() + 1)
    return np.divide(total, count, out=np.full(total.shape, np.nan), where=count > 0)[block]


def benchmark(fixed: dict, market: dict, bars: pd.DataFrame, reference: str) -> np.ndarray:
    """The blind-trade reference for each real trade: same length, same stretch of market.

    Args:
        fixed: What backtest.setting() returned.
        market: What envelope.describe() returned for this market.
        bars: That market's bars.
        reference: BLOCK, or a half-width in months as a number.

    Returns:
        One reference return per trade. Computed once per distinct holding time rather than
        per trade, because a whole databank shares a handful of holds.
    """
    held = fixed["held"]
    entry, hold = held["entry"].to_numpy(), held["hold"].to_numpy()
    out = np.empty(len(held))
    for h in np.unique(hold):
        means = (block_means(fixed["enter_px"], fixed["leave_px"], market["block"], int(h))
                 if reference == BLOCK else
                 centered_means(fixed["enter_px"], fixed["leave_px"], int(h),
                                half_bars(bars, float(reference))))
        here = hold == h
        out[here] = means[entry[here]]
    return out


def differences(fixed: dict, bars: pd.DataFrame, market: dict, reference: str) -> np.ndarray:
    """Per-trade timing alpha: what the trade made, minus what its blind twin would have.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        market: What envelope.describe() returned.
        reference: BLOCK, or a half-width in months.

    Returns:
        One difference per trade. Cost appears in both terms and cancels, so this test says
        nothing about whether the strategy is profitable — only about whether its entries
        beat blind entries of the same duration. That is the whole point: it is the one test
        here that needs neither a cost assumption nor a null model.
    """
    return pricing.realised(bars, fixed["held"], fixed["fill"]["convention"]) - benchmark(
        fixed, market, bars, reference)


def one(fixed: dict, bars: pd.DataFrame, market: dict, cfg: dict, reference: str,
        rng: np.random.Generator) -> dict:
    """Test 1b under one definition of the reference window.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        market: What envelope.describe() returned.
        cfg: What config.load() returned.
        reference: BLOCK, or a half-width in months.
        rng: Seeded generator.

    Returns:
        The mean and median difference, the Wilcoxon signed-rank p-value, the share of trades
        that beat their reference, a block-bootstrap interval on the mean, and the same mean
        in bps, per cent, ATR units and dollars. Wilcoxon rather than a t-test because
        per-trade returns are skewed and fat-tailed — measured, skew +1.9 and excess kurtosis
        +18 on Brent.
    """
    d = differences(fixed, bars, market, reference)
    b = cfg["bootstrap"]
    picks = bootstrap.block_bootstrap(b["draws"], len(d), rng, b["block"])
    return {"reference": reference, "mean": float(d.mean()), "median": float(np.median(d)),
            "p": float(stats.wilcoxon(d, alternative=cfg["paired"]["alternative"]).pvalue),
            "beat_share": float((d > 0).mean()), "trades": len(d),
            "ci": bootstrap.percentile_ci(d[picks].mean(axis=1), *b["ci"]),
            **units.spread(d, fixed)}


def run(fixed: dict, bars: pd.DataFrame, market: dict, cfg: dict,
        rng: np.random.Generator) -> dict:
    """Test 1b for one strategy on one market, under every reference the config lists.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        market: What envelope.describe() returned.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        What one() returned for `paired.reference`, plus `sensitivity` — the same test under
        every entry of `paired.sensitivity`. The sensitivity list is not decoration: if a
        p-value survives all of them the result does not depend on how "the same stretch of
        market" was defined, and if it survives only one, that definition was carrying it.
    """
    p = cfg["paired"]
    wanted = [p["reference"]] + [w for w in p["sensitivity"] if w != p["reference"]]
    done = {w: one(fixed, bars, market, cfg, w, rng) for w in wanted}
    return {**done[p["reference"]],
            "sensitivity": [done[w] for w in p["sensitivity"]]}
