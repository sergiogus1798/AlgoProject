"""Every variant's cumulative curve off one leg's databank, checked against what SQX stored."""

import os
from pathlib import Path

import pandas as pd

from core import fanout, sqxstats
from sqx.variants import legs as legmod

ROUNDING = 1.0        # dollars: the curve is stored at float32 precision
BLOCK = 100           # files per worker task
# An open position at a leg's last bar leaves the curve ahead of NetProfit by at most about
# one trade's own size. 2026-09-26, USDJPY WFC on 1,093 variants of one mother: every variant
# shared an open USDCAD position at the `build` boundary (they all trade the same fixed
# condition on the same market, only periods differ) -- the gap was $447-$840 against an
# AvgWin of $640-$720, nowhere near "the wrong result", but 100% of the block was "off" and
# tripped the fatal gate below written for a *handful* being off. PLAUSIBLE widens the
# tolerance to "at most a few trades' worth" before calling a fully-off block a real misread.
PLAUSIBLE_TRADES = 3

# What the block readers see, set before the fork: one leg's sorted files and its results.
_SHARED: dict = {}


def _block(start: int) -> tuple[dict, dict]:
    """Every result's curve for one block of a leg's files, and which did not reconcile.

    Args:
        start: Position of the block's first file in the leg's sorted folder.

    Returns:
        ({market: cumulative curves of the block, dates down and variant across},
        {market: (the variants whose curve does not end where SQX says the result ended,
        the ones among those where the gap is too big to be one open position)}).
        ⚠️ A few off are expected and NOT a fault: SQX marks an open position to market in
        the curve and counts only closed trades in net profit, so the two differ when a
        trade is open on a leg's last bar. A *handful* off used to be the only case this
        module had seen; on a large population sharing one fixed condition and one market,
        every variant can land there together (🔬 2026-09-26, see PLAUSIBLE_TRADES) -- so
        "off" alone no longer means broken. What still means broken: the gap being bigger
        than a few trades' worth, which is the wrong-result read out of a .sqx that carries
        several, not an open position.
    """
    files, keys = _SHARED["files"], _SHARED["keys"]
    found, off, implausible = {m: {} for m in keys}, {m: [] for m in keys}, {m: [] for m in keys}
    for path in files[start:start + BLOCK]:
        for market, key in keys.items():
            try:
                curve = sqxstats.equity(path, key)
            except StopIteration:
                continue
            found[market][path.stem] = curve
            stats = sqxstats.stats(path, key)[sqxstats.FULL]
            diff = abs(float(curve.iloc[-1]) - stats["NetProfit"])
            if diff > ROUNDING:
                off[market].append(path.stem)
                bound = PLAUSIBLE_TRADES * max(abs(stats.get("MaxProfit") or 0),
                                               abs(stats.get("MaxLoss") or 0))
                if bound == 0 or diff > bound:
                    implausible[market].append(path.stem)
    return {m: pd.DataFrame(c) for m, c in found.items()}, off, implausible


def leg_curves(folder: Path, keys: dict) -> dict:
    """Every result of one leg: its cumulative curves and the variants that did not reconcile.

    Args:
        folder: One leg's databank folder inside the install.
        keys: What markets_of() returned for it.

    Returns:
        {market: (curves, dates down and `variant_id` across in file order, off-list,
        implausible-list)}. Gaps are carried forward rather than zeroed: a date another
        variant traded on and this one did not is a day this one's total did not move, not
        a day it lost everything. Read in blocks on every core: 🔬 2026-09-25, 15,000 files
        x 10 results took 385 s on one.
    """
    files = sorted(folder.glob("*.sqx"))
    _SHARED.update(files=files, keys=keys)
    parts = dict(fanout.run(_block, {i: BLOCK for i in range(0, len(files), BLOCK)},
                            os.cpu_count()))
    out = {}
    for market in keys:
        frames = [parts[i][0][market] for i in sorted(parts) if not parts[i][0][market].empty]
        cum = (pd.concat(frames, axis=1).sort_index().ffill().fillna(0.0) if frames
               else pd.DataFrame())
        out[market] = (cum, [v for i in sorted(parts) for v in parts[i][1][market]],
                       [v for i in sorted(parts) for v in parts[i][2][market]])
    return out

def markets_of(folder: Path) -> list[str]:
    """Which results this leg's .sqx carry, main first and one per cross-check market.

    Args:
        folder: One leg's databank folder.

    Returns:
        {market name: result key}, read off the first file. `Portfolio` is left out on
        purpose: it is every market summed, and harvesting it beside its parts would
        double-count anything that adds them up.
    """
    first = next(iter(sorted(folder.glob("*.sqx"))), None)
    keys = sqxstats.results(first) if first else []
    # Cut at the "/": 🔬 2026-09-25 on USDJPY, the key `settings.xml` stores is
    # `Main: USDJPY_M1/H1` and the archive's folder is
    # `Results/Main: USDJPY_M1_LOM_H1/`, so the whole key matched no curve and
    # the harvest came back empty. Up to the "/" it is a prefix of both.
    return {legmod.market(k): k.split("/")[0] for k in keys
            if k.startswith(legmod.MAIN) or k.startswith(legmod.EXTRA)}
