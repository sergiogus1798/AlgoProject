#!/usr/bin/env python3
"""The command: how the block length of the null moves the p-values, measured on real assets."""

import argparse
import zlib

import numpy as np
import pandas as pd
from arch.bootstrap import optimal_block_length
from scipy.stats import spearmanr

from core import assetdata, fanout
from core.researchpaths import research_profiles_dir
from studies.research.marketProfile import inputs, one, series
from studies.research.marketProfile.measure import SYMMETRIC

LEVEL = 0.05
STATE = {}


def _cell(symbol: str, timeframe: str) -> tuple[dict, dict]:
    """One cell's log bars and calendar."""
    bars = inputs.bars(inputs.minute_bars(symbol, STATE["cfg"]["run"]["fresh_minutes"]), timeframe)
    return series.logs(bars), series.calendar(bars.index, timeframe, STATE["cfg"])


def memory(symbol: str, timeframe: str) -> dict:
    """How long the series remembers: Politis-White's block and the decay of |returns|.

    Returns:
        The optimal circular block of the returns and of their absolute value, and the first
        lag at which the autocorrelation of absolute returns falls under LEVEL.
    """
    x, _ = _cell(symbol, timeframe)
    r = np.diff(x["c"])
    a = np.abs(r) - np.abs(r).mean()
    acf = np.array([a[k:] @ a[:-k] for k in range(1, 2001)]) / (a @ a)
    return {"symbol": symbol, "timeframe": timeframe,
            "pw_returns": optimal_block_length(r)["circular"].iloc[0],
            "pw_abs_returns": optimal_block_length(np.abs(r))["circular"].iloc[0],
            "abs_acf_1": acf[0], "lag_abs_acf_below_0.05": int(np.argmax(acf < LEVEL)) + 1}


def trial(key: tuple) -> dict:
    """One block length on one cell: the real p-values, and the false alarms on flipped series.

    Args:
        key: (symbol, timeframe, block).

    Returns:
        `p` of every measure on the real series; `null_sd` of each; and `size`, the share of
        directional tests rejected at LEVEL on sign-flipped copies of the series, where no
        direction exists by construction — 0.05 when the null is the right width.
    """
    symbol, timeframe, block = key
    cfg, flips = STATE["cfg"], STATE["flips"]
    x, cal = _cell(symbol, timeframe)
    rng = np.random.default_rng([cfg["nulls"]["seed"], block, zlib.crc32(symbol.encode())])
    real, sims = one.against_null(x, cal, cfg, block, rng)
    fns = {s["name"]: s["fn"] for s in cfg["measures"]}
    directional = np.array([fns[r[0]] not in ("range_acf", "narrow_wide") for r in real])
    hits = []
    for _ in range(flips):
        fake, fake_sims = one.against_null(series.flipped(x, rng), cal, cfg, block, rng)
        hits.append(one.pvalues(fake, fake_sims)[directional] <= LEVEL)
    return {"p": one.pvalues(real, sims), "null_sd": sims.std(axis=0, ddof=1),
            "size": float(np.mean(hits)), "tests": int(np.size(hits)),
            "trade": np.array([fns[r[0]] not in SYMMETRIC for r in real])}


def main() -> None:
    """Measure the block length on a few cells, print the table, write it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", nargs="+", default=["XAUUSD", "EURUSD", "USA500"])
    ap.add_argument("--timeframes", nargs="+", default=["H1", "H4"])
    ap.add_argument("--blocks", nargs="+", type=int, default=[1, 6, 24, 72, 240])
    ap.add_argument("--flips", type=int, default=30, help="sign-flipped copies per trial")
    ap.add_argument("--draws", type=int, default=200, help="null draws per series")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    cfg = inputs.config([f"nulls.draws={a.draws}"])
    STATE.update(cfg=cfg, flips=a.flips)
    for s in a.symbols:
        assetdata.load(s)
    cells = [(s, t) for s in a.symbols for t in a.timeframes]
    print(pd.DataFrame([memory(*c) for c in cells]).round(3).to_string(index=False), flush=True)
    keys = {(s, t, b): series.MINUTES[t] ** -1 for s, t in cells for b in a.blocks}
    got = dict(fanout.run(trial, keys, a.workers))
    rows = []
    for s, t in cells:
        ref = got[(s, t, a.blocks[0])]
        for b in a.blocks:
            g = got[(s, t, b)]
            rows.append({"symbol": s, "timeframe": t, "block": b, "size_at_0.05": g["size"],
                         "tests": g["tests"], "real_p_below_0.05": int((g["p"] <= LEVEL).sum()),
                         "of": g["p"].size,
                         "trade_p_below_0.05": int((g["p"][g["trade"]] <= LEVEL).sum()),
                         "rank_corr_p_vs_first": spearmanr(g["p"], ref["p"])[0],
                         "null_sd_vs_first": float(np.median(g["null_sd"] / ref["null_sd"]))})
    table = pd.DataFrame(rows)
    print(table.round(3).to_string(index=False))
    out = research_profiles_dir() / "blocklen.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
