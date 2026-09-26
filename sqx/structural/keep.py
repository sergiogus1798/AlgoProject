#!/usr/bin/env python3
"""After the run: copy the retested files out of the install and check each still carries its edit."""

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import worker
from core.paths import worker_dir
from sqx.structural import make
from sqx.variants import inputs

FILE = "retained.parquet"


def keep(work: Path) -> pd.DataFrame:
    """Copy every leg's retested `.sqx` beside the batch and read the rules back out of them.

    Args:
        work: The batch directory `sqx.variants.execute` ran; its `ran.json` names the
            databank folders.

    Returns:
        One row per retested file and leg: the plan's row, what the retested file holds,
        and `ok`. An identical backtest is only evidence of a redundant condition once
        this says SQX kept the edit — the same result with the block back in the file is
        the silent failure of OPEN.md §9, and the two look the same from the panel.
    """
    plan = pd.read_parquet(work / make.FILE)[
        ["variant_id", "strategy", "kind", "signal", "index", "block", "expect_blocks",
         "expect_direction"]]
    frames = []
    for leg in json.loads((work / "ran.json").read_text(encoding="utf-8"))["legs"]:
        target = work / "retested" / leg["databank"]
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(leg["databank_dir"], target)
        checked = make.verify(plan, make.read_back(target))
        frames.append(checked.assign(leg=leg["segment"], databank=leg["databank"]))
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    """Keep the retested files and refuse a batch where SQX dropped an edit."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path, help="the batch directory")
    a = ap.parse_args()

    # Reading files is safe with the install up, but a sync could be deleting them.
    role = inputs.load()["execute"]["role"]
    held = worker.holding(worker_dir(role))
    if held:
        raise SystemExit(f"{role} sigue arriba (PID {held}): espera a que `execute` lo pare")
    done = keep(a.work)
    done.to_parquet(a.work / FILE, compression="zstd", index=False)
    print(done[["leg", "variant_id", "kind", "block", "blocks", "direction", "ok"]]
          .to_string(index=False))
    if not done["ok"].all():
        raise SystemExit("SQX no conservó la edición de "
                         f"{sorted(set(done.loc[~done['ok'], 'variant_id']))}")


if __name__ == "__main__":
    main()
