#!/usr/bin/env python3
"""Every variant's trades on the three legs and every market, in one `variant_trades.parquet` per batch."""

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.assetdata import load
from core.paths import export_dir
from sqx.projects import registry
from sqx.variants import legs as legmod

TAG = "variants"                  # the `export_retest --batch` tag of this export
OUT = "variant_trades.parquet"    # what `engines/variants/excess.py` reads


def main_feed(project: str) -> str:
    """The SQX feed of the asset the project was built on, from its registry row."""
    row = next(r for r in reversed(registry.rows()) if r["name"] == project)
    return load(row["symbol"])["sqx_symbol"]


def gather(work: Path, project: str, day: str | None = None) -> int:
    """Reunite the three legs' exports of one batch and delete them.

    Args:
        work: The batch folder.
        project: The project whose three leg databanks `export_retest` just exported.
        day: The export's date; today when absent, as `export_retest` writes it.

    Returns:
        The trades written. Schema: `core.tradestore.KEEP` (schema T) plus `variant_id` (the
        file name SQX kept, collision suffix stripped), `leg` (`build`, `oos1`, `oos2`),
        `market` (`Main` where `Symbol` is the project's own feed, else that feed) and `block`,
        which is NOT the market (knowhow/export/data-all-blocks.md). The
        controls are in it, tagged in `manifest.parquet`; nobody analyses them.
        The per-leg export folders are removed: this file is their only keeper.
    """
    day = day or date.today().isoformat()
    parts, folders, own = [], [], main_feed(project)
    for leg in legmod.legs():
        folder = export_dir(project, leg["databank"], day, TAG)
        frame = pd.read_parquet(folder / "trades.parquet")
        symbol = frame["Symbol"].astype(str)
        market = symbol.where(symbol != own, legmod.MAIN)
        parts.append(frame.assign(
            variant_id=frame["strategy"].astype(str).str.replace(r"\(\d+\)$", "", regex=True),
            leg=leg["segment"], market=market).drop(columns=["strategy"]))
        folders.append(folder)
    trades = pd.concat(parts, ignore_index=True)
    for name in trades.select_dtypes(exclude="number").columns.difference(["Open time", "Close time"]):
        trades[name] = trades[name].astype("category")
    trades.to_parquet(work / OUT, index=False)
    for folder in folders:
        shutil.rmtree(folder)
    return len(trades)


def main() -> None:
    """Write `variant_trades.parquet` beside the batch and say how many trades it holds."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--project", required=True)
    ap.add_argument("--day", help="export date; today when absent")
    a = ap.parse_args()
    print(f"{a.work.name}: {gather(a.work, a.project, a.day)} operaciones en {OUT}")


if __name__ == "__main__":
    main()
