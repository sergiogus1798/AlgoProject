#!/usr/bin/env python3
"""Harvest every retested variant's per-day P&L out of the custodian's .sqx, without SQX."""

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import sqxstats
from sqx.variants import inputs

NAME = "Strategy Name"
IS, OOS = "Net profit (IS)", "Net profit (OOS)"
ROUNDING = 1.0        # dollars: the curve is stored at float32 precision, the panel at 2 dp
STEP = 100            # files between progress lines


def curves(folder: Path, say: Callable[[int, str], None]) -> pd.DataFrame:
    """Every variant's cumulative P&L, one column each, aligned on one calendar.

    Args:
        folder: The databank folder inside the install, after `execute.synced`.
        say: Called with a percentage and a status line.

    Returns:
        Cumulative account-currency profit, dates down and `variant_id` across. Gaps are
        carried forward rather than zeroed: a date another variant traded on and this one
        did not is a day this one's total did not move, not a day it lost everything.
    """
    files = sorted(folder.glob("*.sqx"))
    found = {}
    for n, path in enumerate(files, 1):
        found[path.stem] = sqxstats.equity(path)
        if n % STEP == 0:
            say(n * 100 // len(files), f"{n} de {len(files)} curvas leidas")
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


def mismatches(cum: pd.DataFrame, panel: pd.DataFrame, split: str) -> list[str]:
    """Variants whose harvested curve disagrees with the result SQX stored for them.

    Args:
        cum: What `curves` returned.
        panel: The retest export, as `collect.panel` reads it.
        split: First day of the out-of-sample range.

    Returns:
        The variants that disagree by more than a dollar, named.

        **This is the invariant that ties the binary reader to the number the databank
        shows**, and it is read at the in-sample boundary rather than at the end of the
        curve. It catches the failure this module was written around -- a strategy
        retested with a cross-market check carries three equity members, and the first in
        the archive is gold plus silver, which misses by thousands.
    """
    stored = panel.set_index(NAME)[IS].reindex(cum.columns)
    gap = (cum[cum.index < split].iloc[-1] - stored).abs()
    return sorted(gap.index[~(gap <= ROUNDING)])


def open_at_end(cum: pd.DataFrame, panel: pd.DataFrame) -> list[str]:
    """Variants still holding a position when the data ran out.

    Args:
        cum: What `curves` returned.
        panel: The retest export.

    Returns:
        The variants whose whole-curve total exceeds in-sample plus out-of-sample profit.

        Not a fault and not a gate: SQX marks an open position to market in the equity
        curve and counts only closed trades in net profit, so the two disagree exactly
        when a trade is open on the last bar. Measured 2026-09-22 on this batch, 172 of
        962, by 95 to 332 dollars, and they average three times the trades of the rest --
        which is why `matrix.py` drops the final period rather than trusting it.
    """
    stored = (panel.set_index(NAME)[IS] + panel.set_index(NAME)[OOS]).reindex(cum.columns)
    gap = (cum.iloc[-1] - stored).abs()
    return sorted(gap.index[~(gap <= ROUNDING)])


def main() -> None:
    """Read one batch's curves off the custodian's disk and leave them beside the batch."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds ran.json and retest.csv")
    a = ap.parse_args()

    cfg = inputs.load()["execute"]
    ran = json.loads((a.work / "ran.json").read_text(encoding="utf-8"))
    folder = Path(ran["databank_dir"])
    started = time.time()

    print(f"PROGRESS 5 leyendo {ran['n_on_disk']} .sqx de {folder.name}", flush=True)
    cum = curves(folder, lambda pct, line: print(f"PROGRESS {5 + pct * 85 // 100} {line}",
                                                 flush=True))

    print("PROGRESS 92 comprobando cada curva contra lo que SQX guardo", flush=True)
    panel = pd.read_csv(a.work / "retest.csv", sep=";")
    bad = mismatches(cum, panel, cfg["split"])
    held = open_at_end(cum, panel)

    out = a.work / "equity.parquet"
    daily(cum).to_parquet(out, compression="zstd")
    spent = time.time() - started
    (a.work / "equity.json").write_text(json.dumps(
        {"n": cum.shape[1], "days": cum.shape[0], "bytes": out.stat().st_size,
         "first": str(cum.index[0].date()), "last": str(cum.index[-1].date()),
         "split": cfg["split"], "mismatch": len(bad), "mismatched": bad[:20],
         "open_at_end": len(held), "wall_s": round(spent, 1)},
        indent=2), encoding="utf-8")

    print(f"PROGRESS 100 {cum.shape[1]} curvas x {cum.shape[0]} dias, "
          f"{out.stat().st_size / 1e6:.1f} MB en {spent:.0f} s, "
          f"{len(held)} con posicion abierta al final", flush=True)
    if bad:
        sys.exit(f"{len(bad)} variantes cuya curva no cuadra con el resultado que SQX "
                 f"guardo, p.ej. {bad[:5]}. El lector esta leyendo el resultado "
                 f"equivocado del .sqx, o el databank no es el de este lote.")


if __name__ == "__main__":
    main()
