#!/usr/bin/env python3
"""Stands in for a stage whose real module is not written yet, honouring the same contract."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from core.paths import DATA

STEPS = 5
# `sqx` because that is where sqx.variants.make actually writes the batch, now that the
# build stage is the real command. The real collect stage must record the same folder:
# a `removable` pointing anywhere else deletes nothing and frees nothing.
VARIANTS, EXPORT = "sqx", "metrics_placeholder.json"
# What each stage is expected to leave behind, so the chain -- and the verdict thresholds
# that read these names -- can be run end to end today. Every figure here is invented and
# is labelled as such in the file the stub writes.
# The keys have to cover every field the matching recipe row lists under `record`, or the
# ledger raises KeyError on a stage the fixture is only pretending to run.
SHAPE = {"spp_is": {"tested": 1, "wall_s": 2100.0, "steps": 40, "spread_pct": 35},
         "spp_oos": {"tested": 1, "wall_s": 2400.0},
         "spp_export": {"rows": 12000},
         "design": {"n": 5000, "shortfall": 0, "n_target": 5000, "levels": 27},
         "build": {"n": 5000, "bytes": 70000000},
         "ran": {"n_loaded": 5000, "n_returned": 5000},
         "collected": {"n": 5000, "canaries_distinct": 4},
         "wfc": {"n": 1001, "rho": 0.41, "call": "fiable", "pairs": 1200}}


def digest(path: Path) -> str:
    """The sha256 of one file.

    Args:
        path: File to read.

    Returns:
        Hex digest. The collect stage records these so that deleting the variants can be
        proved safe afterwards rather than assumed safe beforehand.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def leftovers(work: Path) -> dict:
    """The bulky data a real collect stage would have exported, and what it could then drop.

    Args:
        work: The strategy's work directory.

    Returns:
        The `files` and `removable` lists of the C5 contract, paths relative to the data
        root. The placeholder writes a real, tiny export and a real, tiny folder of
        variants, so the sweep runs against something that is actually on disk: the export
        is hashed and kept, the variants are recorded as removable.
    """
    heavy = work / VARIANTS
    heavy.mkdir(parents=True, exist_ok=True)
    (heavy / "P00000.txt").write_text("placeholder variant\n", encoding="utf-8")
    kept = work / EXPORT
    kept.write_text('{"placeholder": true}\n', encoding="utf-8")
    return {"removable": [str(heavy.relative_to(DATA))],
            "files": [{"path": str(kept.relative_to(DATA)),
                       "bytes": kept.stat().st_size, "sha256": digest(kept)}]}


def main() -> None:
    """Report progress like a real stage, then write its placeholder output."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", required=True, choices=sorted(SHAPE))
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--seconds", type=float, default=0.5,
                    help="how long to pretend to work; the resume test needs a stage it "
                         "can interrupt halfway")
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)

    for step in range(1, STEPS + 1):
        time.sleep(args.seconds / STEPS)
        print(f"PROGRESS {step * 100 // STEPS} paso {step} de {STEPS} "
              f"(marcador de posición de {args.stage})", flush=True)

    out = dict(SHAPE[args.stage], placeholder=True)
    if args.stage == "collected":
        out |= leftovers(args.work)
    (args.work / f"{args.stage}.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
