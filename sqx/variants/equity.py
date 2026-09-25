#!/usr/bin/env python3
"""Harvest every variant's per-day P&L from the three legs, per market, and join them."""

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import sqxstats
from sqx.variants import legs as legmod

ROUNDING = 1.0        # dollars: the curve is stored at float32 precision
STEP = 100            # files between progress lines


def curves(folder: Path, result: str, say: Callable[[int, str], None]) -> pd.DataFrame:
    """One result's cumulative P&L for every variant in a leg's databank.

    Args:
        folder: One leg's databank folder inside the install.
        result: Which `Results/` entry to read — "Main", or "AdditionalMarket: <feed>".
        say: Called with a percentage and a status line.

    Returns:
        Cumulative account-currency profit, dates down and `variant_id` across. Gaps are
        carried forward rather than zeroed: a date another variant traded on and this one
        did not is a day this one's total did not move, not a day it lost everything.
    """
    files = sorted(folder.glob("*.sqx"))
    found = {}
    for n, path in enumerate(files, 1):
        try:
            found[path.stem] = sqxstats.equity(path, result)
        except StopIteration:
            continue
        if n % STEP == 0:
            say(n * 100 // len(files), f"{n} de {len(files)} curvas ({result[:24]})")
    return pd.DataFrame(found).ffill().fillna(0.0)


def daily(cum: pd.DataFrame) -> pd.DataFrame:
    """The same curves as per-day increments.

    Args:
        cum: What `curves` returned.

    Returns:
        One row per date, one column per variant, each cell that day's profit or loss.
        The first row keeps its level, so summing a column down reproduces the cumulative
        curve exactly -- which is what lets any later study re-cut the windows itself.
    """
    steps = cum.diff()
    steps.iloc[0] = cum.iloc[0]
    return steps


def joined(per_leg: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """The three legs of one market, end to end, as one continuous daily series.

    Args:
        per_leg: {segment: daily increments}, in the doctrine's segment order.

    Returns:
        One frame, dates down and `variant_id` across, spanning `build` to `oos2`.

        The join is on INCREMENTS and never on the cumulative curves, and that is the
        whole trick: each leg is its own backtest and restarts its equity at zero, so
        stacking the cumulative curves would drop the account back to zero twice. Summing
        the increments down reproduces the account the three legs would have produced run
        as one — which is what the united metrics are read off.
    """
    return pd.concat([per_leg[s] for s in per_leg], axis=0).sort_index()


def unreconciled(cum: pd.DataFrame, folder: Path, result: str) -> list[str]:
    """Variants whose harvested curve does not end where SQX says the result ended.

    Args:
        cum: What `curves` returned for this leg and result.
        folder: The leg's databank folder.
        result: The result that was read.

    Returns:
        The variants that disagree by more than a dollar.

        ⚠️ Expected in small numbers and NOT a fault: SQX marks an open position to market
        in the equity curve and counts only closed trades in net profit, so the two differ
        exactly when a trade is open on the last bar of the leg. Three legs means three
        such boundaries. What it does catch is the failure this module was written around
        — reading the wrong result out of a .sqx that carries four of them — and that one
        shows up as *every* variant disagreeing, not a handful.
    """
    off = []
    for name in cum.columns:
        stored = sqxstats.stats(folder / f"{name}.sqx", result)[sqxstats.FULL]["NetProfit"]
        if abs(float(cum[name].iloc[-1]) - stored) > ROUNDING:
            off.append(name)
    return off


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
    return {legmod.market(k): k for k in keys
            if k.startswith(legmod.MAIN) or k.startswith(legmod.EXTRA)}


def harvest(work: Path, legs: list[dict], say: Callable[[int, str], None]) -> dict:
    """Read all three legs, write the joined curves, and report what did not reconcile.

    Args:
        work: The batch directory.
        legs: What `ran.json` recorded, in segment order.
        say: Called with a percentage and a status line.

    Returns:
        What went into `equity.json`. Two files are written: `equity.parquet`, the main
        market's joined daily P&L in the wide shape every study downstream already reads,
        and `equity_markets.parquet`, the same thing in long form for every extra market —
        which is what a surface-of-performance view on other assets needs.
    """
    main, extra, report = {}, [], []
    for i, leg in enumerate(legs):
        folder = Path(leg["databank_dir"])
        results = markets_of(folder)
        for name, key in results.items():
            cum = curves(folder, key, lambda p, line, i=i: say(i * 30 + p * 30 // 100, line))
            if cum.empty:
                continue
            off = unreconciled(cum, folder, key)
            report.append({"segment": leg["segment"], "market": name, "n": cum.shape[1],
                           "days": cum.shape[0], "first": str(cum.index[0].date()),
                           "last": str(cum.index[-1].date()), "open_at_end": len(off),
                           "all_off": bool(off and len(off) == cum.shape[1])})
            if name == legmod.MAIN:
                main[leg["segment"]] = daily(cum)
            else:
                extra.append(daily(cum).stack().rename("pnl").reset_index(
                    names=["date", "variant_id"]).assign(market=name,
                                                         segment=leg["segment"]))

    united = joined(main)
    united.to_parquet(work / "equity.parquet", compression="zstd")
    if extra:
        pd.concat(extra).to_parquet(work / "equity_markets.parquet", compression="zstd")
    return {"n": united.shape[1], "days": united.shape[0],
            # The real span of each leg, measured off its own curves rather than restated
            # from the project: it is what `collect.unions` slices the joined curve by.
            "windows": {s: [str(d.index[0].date()), str(d.index[-1].date())]
                        for s, d in main.items()},
            "first": str(united.index[0].date()), "last": str(united.index[-1].date()),
            "segments": [leg["segment"] for leg in legs],
            # Every boundary, as the first day of each leg after the first. The studies
            # read a boundary from here and never restate one of their own: two files
            # naming one date is how they come to disagree.
            "splits": {s: d.index[0].strftime("%Y-%m-%d")
                       for s, d in list(main.items())[1:]},
            "markets": sorted({r["market"] for r in report if r["market"] != legmod.MAIN}),
            # Lifted to the top level for the pipeline's `must` gate, which reads one
            # number out of this file by name. `unreadable` is the one that must be zero:
            # a whole block where no curve reconciles is the wrong-result bug. Positions
            # open at a leg boundary are expected and only counted.
            "open_at_end": sum(r["open_at_end"] for r in report),
            "unreadable": sum(1 for r in report if r["all_off"]),
            "bytes": (work / "equity.parquet").stat().st_size,
            "blocks": report}


def main() -> None:
    """Read the three legs' curves off the custodian's disk and leave them beside the batch."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds ran.json and the retest_*.csv")
    a = ap.parse_args()

    ran = json.loads((a.work / "ran.json").read_text(encoding="utf-8"))
    started = time.time()
    done = harvest(a.work, ran["legs"],
                   lambda pct, line: print(f"PROGRESS {5 + pct * 85 // 100} {line}",
                                           flush=True))
    done["wall_s"] = round(time.time() - started, 1)
    (a.work / "equity.json").write_text(json.dumps(done, indent=2), encoding="utf-8")

    print(f"PROGRESS 100 {done['n']} variantes x {done['days']} dias unidos "
          f"({done['first']} a {done['last']}), mercados: "
          f"{', '.join(done['markets']) or 'ninguno'}, {done['wall_s']:.0f} s", flush=True)
    for row in done["blocks"]:
        print(f"  {row['segment']:<6} {row['market']:<24} {row['n']:>5} curvas  "
              f"{row['first']} a {row['last']}  {row['open_at_end']} con posicion abierta")
    broken = [r for r in done["blocks"] if r["all_off"]]
    if broken:
        sys.exit(f"{len(broken)} bloques donde NINGUNA curva cuadra con lo que SQX guardo: "
                 f"{[(r['segment'], r['market']) for r in broken]}. El lector esta leyendo "
                 "el resultado equivocado del .sqx, o el databank no es el de este lote.")


if __name__ == "__main__":
    main()
