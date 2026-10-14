#!/usr/bin/env python3
"""Each batch's mother, trade by trade: her retested `.sqx` kept per leg, exported in one SQX start."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import exportdrv, tradepack
from core.datapaths import tmp_dir

KEPT = "origin"  # in the batch folder: the mother's retested .sqx, <segment>.sqx
OUT = "trades.parquet"  # what `studies/closing/blindJoint/inputs.py` reads


def keep(work: Path, legs: list[dict]) -> None:
    """Copy the mother's retested file of every leg into the batch, before the databanks are emptied.

    Args:
        work: The batch folder.
        legs: What `ran.json` recorded: each leg's `segment` and `databank_dir`.

    Returns:
        Nothing. The mother is the variant the manifest flags `origin`; SQX names a databank
        entry after the file it was loaded from, so her file is `<variant_id>.sqx`.
    """
    manifest = pd.read_parquet(
        work / "manifest.parquet", columns=["variant_id", "origin"]
    )
    origin = manifest.loc[manifest["origin"], "variant_id"].item()
    (work / KEPT).mkdir(exist_ok=True)
    for leg in legs:
        shutil.copy(
            Path(leg["databank_dir"]) / f"{origin}.sqx",
            work / KEPT / f"{leg['segment']}.sqx",
        )


def harvest(works: list[Path]) -> dict[Path, int]:
    """Write every batch's `trades.parquet` from the files `keep` left, in one `orderstocsv`.

    Args:
        works: Batch folders, each with its `origin/<segment>.sqx`.

    Returns:
        {batch folder: trades written}. The file is schema T (`core.tradepack`) with the
        mother's `variant_id` and the leg's `segment` in place of `strategy`: only the
        mother, not the batch — a batch's trades cost ~90 min to export (decision E3,
        owner 2026-10-04: «solo para la madre»). A leg opens with a warm-up that repeats
        the previous leg's last weeks without trading in them, so the legs do not overlap.
    """
    with tempfile.TemporaryDirectory(dir=tmp_dir()) as tmp:
        staged, csvs, where = Path(tmp) / "sqx", Path(tmp) / "csv", {}
        staged.mkdir()
        for work in works:
            manifest = pd.read_parquet(
                work / "manifest.parquet", columns=["variant_id", "origin"]
            )
            origin = manifest.loc[manifest["origin"], "variant_id"].item()
            for kept in sorted((work / KEPT).glob("*.sqx")):
                where[f"{len(where):04d}"] = (work, origin, kept.stem)
                shutil.copy(kept, staged / f"{len(where) - 1:04d}.sqx")
        exportdrv.trades(staged, csvs)
        tradepack.pack(sorted(csvs.glob("*.csv")), Path(tmp) / OUT, per_market=False)
        trades = pd.read_parquet(Path(tmp) / OUT)
    spot = trades.pop("strategy").astype(str).map(where)
    trades = trades.assign(variant_id=spot.str[1], segment=spot.str[2])
    written = {}
    for work in works:
        own = trades[(spot.str[0] == work).to_numpy()]
        own.to_parquet(work / OUT, index=False)
        written[work] = len(own)
    return written


def main() -> None:
    """Export the mothers of the batches given and say how many trades each one left."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--work",
        required=True,
        type=Path,
        action="append",
        help="a batch folder `collect` already read; repeat it for several",
    )
    a = ap.parse_args()
    for work, n in harvest(a.work).items():
        print(f"{work.name}: {n} operaciones de la madre en {OUT}")


if __name__ == "__main__":
    main()
