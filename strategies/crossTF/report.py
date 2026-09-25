#!/usr/bin/env python3
"""The panel: every mother across timeframes, scaled and not, with what each cell means."""

import argparse
from pathlib import Path

import pandas as pd

from nulls import inputs as nullinputs
from strategies.crossTF import cells, inputs, verdict


def mapping(cfg: dict) -> str:
    """Which result block was read as which timeframe, printed so it can be eyeballed.

    Args:
        cfg: What `inputs.config` returned.

    Returns:
        One line. A wrong `run.blocks` prices every cell on the wrong bars and nothing
        else in the study would notice, so it is stated before any number is shown.
    """
    pairs = ", ".join(f"block {i} = {tf}" for i, tf in enumerate(cfg["run"]["blocks"]))
    return f"result blocks read as: {pairs}"


def main() -> None:
    """Measure every cell of the matrix and print what each scaled one means."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", required=True, type=Path,
                    help="trades.parquet from sqx/export/export_retest.py")
    ap.add_argument("--scaling", required=True, type=Path,
                    help="scaling.parquet from sqx.variants.scale")
    ap.add_argument("--feed", help="SQX symbol the cells were run on; overrides run.feed, "
                    "which is only a default and belongs to whichever asset was studied last")
    ap.add_argument("--out", type=Path, help="write the panel here as Parquet")
    ap.add_argument("--set", dest="overrides", action="append", default=[])
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    nullcfg = nullinputs.config([])
    scaling = pd.read_parquet(a.scaling)
    packed = inputs.trades(a.export)

    plan = inputs.plan(scaling, cfg["run"]["blocks"])
    feed = a.feed or cfg["run"]["feed"]
    # The null layer names whose costs its p-values carry, and the feed is the only thing
    # that says whose. Passed in rather than read from nulls' own config: the asset is a
    # property of this run, not of the null machinery.
    nullcfg["feed"] = feed
    frames = inputs.bars(feed, cfg["run"]["blocks"])
    panel = cells.panel(plan, packed, frames, nullcfg, cfg)
    readings = verdict.read(panel, scaling, cfg)

    statistic = cfg["verdict"]["statistic"]
    print(f"barras de {feed}")
    print(mapping(cfg))
    print(f"statistic {statistic} · null rung {cfg['verdict']['rung']} · "
          f"alpha {cfg['verdict']['alpha']}\n")

    print("-- the mother on every timeframe, periods left alone (no verdict: this asks")
    print("   whether the market is self-similar, not whether the strategy is overfit)")
    print(verdict.unscaled(panel).to_string(index=False), "\n")

    print("-- the scaled siblings, judged")
    print(readings.drop(columns=["warnings"]).to_string(index=False), "\n")

    for timeframe, tally in verdict.counts(readings).items():
        print(f"{timeframe}: " + " · ".join(f"{k} {v}" for k, v in sorted(tally.items())))
    print("\n" + "\n".join(f"  {k}: {v}" for k, v in verdict.MEANS.items()))

    loud = readings[readings["warnings"].str.len() > 0]
    for row in loud.itertuples():
        print(f"\n! {row.mother} {row.timeframe}: " + "; ".join(row.warnings))

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(a.out, index=False)
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
