"""Is this a test, or just a number? The two checks that must pass before any p is read."""

import argparse

import numpy as np
import pandas as pd
from scipy import stats

from nulls import inputs, kernel, model, simulate
from nulls.report import newest
from nulls.stats import measure


def slow_exits(entries: np.ndarray, holds: np.ndarray, low: np.ndarray, high: np.ndarray,
               stop: np.ndarray, target: np.ndarray) -> np.ndarray:
    """The first barrier touch of every trade, written the obvious way.

    Args:
        entries: Entry bar index of each trade.
        holds: Bars until the vertical barrier.
        low, high: Extremes of every bar.
        stop, target: Price level of each trade's lower and upper barrier.

    Returns:
        Offset of the first touch, 0 when neither is reached. Exists only to be compared
        against `kernel.touched()`: a vectorised scan that is subtly wrong produces
        plausible exits and nothing downstream notices.
    """
    found = np.zeros(len(entries), dtype=np.int64)
    for k, (start, hold) in enumerate(zip(entries, holds)):
        for step in range(1, hold + 1):
            if low[start + step] <= stop[k] or high[start + step] >= target[k]:
                found[k] = step
                break
    return found


def barriers(kept: dict, atr_mult: float = 1.5) -> dict:
    """The vectorised barrier scan against the slow one, on barriers this corpus lacks.

    Args:
        kept: What simulate.fixed() returned.
        atr_mult: How many ATRs away the synthetic stop and target are placed.

    Returns:
        How many trades the two scans disagree on. The XAUUSD corpus of 2026-09 carries
        neither stop nor target, so `kernel.touched()` is never exercised by a real run --
        and shipping the path the owner asked for without testing it would mean its first
        use is also its first test. The barriers here are synthetic on purpose.
    """
    located, arrays = kept["located"], kept["bars"]
    entry_px = arrays["enter_px"][located["entry"]]
    reach = kept["atr"][located["entry"]] * atr_mult
    stop, target = entry_px - reach, entry_px + reach
    fast, _, _ = kernel.touched(located["entry"], located["hold"], arrays["low"],
                                arrays["high"], stop, target)
    slow = slow_exits(located["entry"], located["hold"], arrays["low"], arrays["high"],
                      stop, target)
    return {"trades": len(fast), "disagree": int((fast != slow).sum()),
            "touched": int((fast > 0).sum())}


def uniformity(kept: dict, cfg: dict, trials: int) -> dict:
    """Treat null runs as if they were real and check their p-values are uniform.

    Args:
        kept: What simulate.fixed() returned.
        cfg: What inputs.config() returned.
        trials: How many null runs stand in for the real one.

    Returns:
        The Kolmogorov-Smirnov statistic and p of those p-values against Uniform(0, 1). A
        correct null produces uniform p-values under itself, by construction; a sampling bug
        -- an edge of the window unreachable, a hold that overruns, a generator reused --
        shows up here as a skew, and it shows up **before** a real strategy is looked at.
    """
    drawn = simulate.nulls(kept, cfg["nulls"]["headline"], cfg, "verify")["net"]
    stand_in, rest = drawn[:trials], drawn[trials:]
    found = np.array([(1 + (rest >= one).sum()) / (len(rest) + 1) for one in stand_in])
    result = stats.kstest(found, "uniform")
    return {"trials": trials, "ks": float(result.statistic), "p": float(result.pvalue),
            "mean": float(found.mean())}


def main() -> None:
    """Run both checks on one strategy and print what they found."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True)
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--timeframe", default="M30")
    ap.add_argument("--sample", default="OOS1")
    ap.add_argument("--trials", type=int, default=400)
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    trades = inputs.sample(newest(a.project, a.databank), a.strategy, a.sample)
    kept = simulate.fixed(trades, inputs.bars(a.feed, a.timeframe), cfg)

    print(f"{a.strategy}  ({len(trades)} trades, muestra {a.sample})\n")
    print(f"RECONCILIACION  fill={kept['checks']['fill']}  corr={kept['checks']['corr']:.6f}  "
          f"gap mediano={kept['checks']['median_gap']:.2f} $  "
          f"(segunda mejor convencion: {kept['checks']['runner_up']:.4f})")
    got = barriers(kept)
    print(f"BARRERAS        {got['trades']} trades, {got['touched']} tocan una barrera "
          f"sintetica, discrepancias vectorizado vs bucle: {got['disagree']}")
    flat = uniformity(kept, cfg, a.trials)
    print(f"UNIFORMIDAD     {flat['trials']} runs nulos juzgados contra el resto: "
          f"KS={flat['ks']:.4f} p={flat['p']:.3f} media={flat['mean']:.3f} (debe ser ~0.5)")


if __name__ == "__main__":
    main()
