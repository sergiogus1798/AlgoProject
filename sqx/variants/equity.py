#!/usr/bin/env python3
"""Harvest every variant's per-day P&L from the three legs, per market, and join them."""

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import fanout, sqxstats
from sqx.variants import legs as legmod

ROUNDING = 1.0        # dollars: the curve is stored at float32 precision
BLOCK = 100           # files per worker task
SCHEMA = pa.schema([("date", pa.timestamp("ns")), ("variant_id", pa.string()),
                    ("pnl", pa.float64()), ("market", pa.string()), ("segment", pa.string())])

# What the block readers see, set before the fork: one leg's sorted files and its results.
_SHARED: dict = {}


def _block(start: int) -> tuple[dict, dict]:
    """Every result's curve for one block of a leg's files, and which did not reconcile.

    Args:
        start: Position of the block's first file in the leg's sorted folder.

    Returns:
        ({market: cumulative curves of the block, dates down and variant across},
        {market: the variants whose curve does not end where SQX says the result ended}).
        ⚠️ A few off are expected and NOT a fault: SQX marks an open position to market in
        the curve and counts only closed trades in net profit, so the two differ when a
        trade is open on a leg's last bar. The failure this catches -- the wrong result read
        out of a .sqx that carries several -- shows up as every variant off, not a handful.
    """
    files, keys = _SHARED["files"], _SHARED["keys"]
    found, off = {m: {} for m in keys}, {m: [] for m in keys}
    for path in files[start:start + BLOCK]:
        for market, key in keys.items():
            try:
                curve = sqxstats.equity(path, key)
            except StopIteration:
                continue
            found[market][path.stem] = curve
            stored = sqxstats.stats(path, key)[sqxstats.FULL]["NetProfit"]
            if abs(float(curve.iloc[-1]) - stored) > ROUNDING:
                off[market].append(path.stem)
    return {m: pd.DataFrame(c) for m, c in found.items()}, off


def leg_curves(folder: Path, keys: dict) -> dict:
    """Every result of one leg: its cumulative curves and the variants that did not reconcile.

    Args:
        folder: One leg's databank folder inside the install.
        keys: What markets_of() returned for it.

    Returns:
        {market: (curves, dates down and `variant_id` across in file order, off-list)}. Gaps
        are carried forward rather than zeroed: a date another variant traded on and this
        one did not is a day this one's total did not move, not a day it lost everything.
        Read in blocks on every core: 🔬 2026-09-25, 15,000 files x 10 results took 385 s
        on one.
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
        out[market] = (cum, [v for i in sorted(parts) for v in parts[i][1][market]])
    return out


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
    # `Main: USDJPY_DukasM1_the5ers/H1` and the archive's folder is
    # `Results/Main: USDJPY_DukasM1_the5ers_LOM_H1/`, so the whole key matched no curve and
    # the harvest came back empty. Up to the "/" it is a prefix of both.
    return {legmod.market(k): k.split("/")[0] for k in keys
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
    main, report, writer = {}, [], None
    for i, leg in enumerate(legs):
        folder = Path(leg["databank_dir"])
        say(i * 30, f"leyendo {leg['segment']} en paralelo")
        for name, (cum, off) in leg_curves(folder, markets_of(folder)).items():
            if cum.empty:
                continue
            report.append({"segment": leg["segment"], "market": name, "n": cum.shape[1],
                           "days": cum.shape[0], "first": str(cum.index[0].date()),
                           "last": str(cum.index[-1].date()), "open_at_end": len(off),
                           "all_off": bool(off and len(off) == cum.shape[1])})
            if name == legmod.MAIN:
                main[leg["segment"]] = daily(cum)
                continue
            # One (leg, market) at a time into the file, never all of them in memory:
            # 🔬 2026-09-25, building the 228 M rows before writing peaked at 31.8 GB.
            rows = daily(cum).stack().rename("pnl").rename_axis(
                ["date", "variant_id"]).reset_index().assign(market=name,
                                                             segment=leg["segment"])
            writer = writer or pq.ParquetWriter(work / "equity_markets.parquet", SCHEMA,
                                                compression="zstd")
            writer.write_table(pa.Table.from_pandas(rows, schema=SCHEMA, preserve_index=False))
    if writer:
        writer.close()

    united = joined(main)
    united.to_parquet(work / "equity.parquet", compression="zstd")
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
