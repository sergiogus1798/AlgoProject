"""Test 1b — each real trade against the average window of its own length in its own regime."""

import numpy as np
import pandas as pd
from scipy import stats

from strategies.crossmarket import bootstrap, pricing


def window_means(enter_px: np.ndarray, leave_px: np.ndarray, block: np.ndarray,
                 hold: int) -> np.ndarray:
    """Mean log return of every window of one length, per regime block.

    Args:
        enter_px: Fill price for an entry on each bar.
        leave_px: Fill price for an exit on each bar.
        block: One regime-block id per bar.
        hold: Window length in bars.

    Returns:
        One mean per block id. Every legal start bar in the block is used, so this is the
        exact expected return of a blind trade of that duration there — no sampling error,
        unlike drawing random entries.
    """
    start = np.arange(len(enter_px) - hold)
    value = np.log(leave_px[start + hold] / enter_px[start])
    total = np.bincount(block[start], weights=value, minlength=block.max() + 1)
    count = np.bincount(block[start], minlength=block.max() + 1)
    return np.divide(total, count, out=np.full(total.shape, np.nan), where=count > 0)


def benchmark(fixed: dict, market: dict) -> np.ndarray:
    """The blind-trade reference for each real trade: same length, same regime block.

    Args:
        fixed: What backtest.setting() returned.
        market: What envelope.describe() returned for this market.

    Returns:
        One reference return per trade. Computed once per distinct holding time rather than
        per trade, because a whole databank shares a handful of holds.
    """
    held, block = fixed["held"], market["block"]
    entry, hold = held["entry"].to_numpy(), held["hold"].to_numpy()
    out = np.empty(len(held))
    for h in np.unique(hold):
        means = window_means(fixed["enter_px"], fixed["leave_px"], block, int(h))
        here = hold == h
        out[here] = means[block[entry[here]]]
    return out


def differences(fixed: dict, bars: pd.DataFrame, market: dict) -> np.ndarray:
    """Per-trade timing alpha: what the trade made, minus what its blind twin would have.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        market: What envelope.describe() returned.

    Returns:
        One difference per trade. Cost appears in both terms and cancels, so this test says
        nothing about whether the strategy is profitable — only about whether its entries
        beat blind entries of the same duration. That is the whole point: it is the one test
        here that needs neither a cost assumption nor a null model.
    """
    return pricing.realised(bars, fixed["held"], fixed["fill"]["convention"]) - benchmark(
        fixed, market)


def run(fixed: dict, bars: pd.DataFrame, market: dict, cfg: dict,
        rng: np.random.Generator) -> dict:
    """Test 1b for one strategy on one market.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.
        market: What envelope.describe() returned.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        The mean and median difference, the Wilcoxon signed-rank p-value, the share of trades
        that beat their reference, and a block-bootstrap interval on the mean. Wilcoxon
        rather than a t-test because per-trade returns are skewed and fat-tailed — measured,
        skew +1.9 and excess kurtosis +18 on Brent.
    """
    d = differences(fixed, bars, market)
    b = cfg["bootstrap"]
    picks = bootstrap.block_bootstrap(b["draws"], len(d), rng, b["block"])
    return {"mean": float(d.mean()), "median": float(np.median(d)),
            "p": float(stats.wilcoxon(d, alternative=cfg["paired"]["alternative"]).pvalue),
            "beat_share": float((d > 0).mean()), "trades": len(d),
            "ci": bootstrap.percentile_ci(d[picks].mean(axis=1), *b["ci"])}
