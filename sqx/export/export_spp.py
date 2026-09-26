#!/usr/bin/env python3
"""Export a databank's Sys. Param Permutation profiles: one wide table, the histograms, the counts."""

import argparse
import shutil
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from core import fanout, manifest, optprofile
from core.paths import MASTER, databank_dir, export_dir, worker_dir
from sqx.export import spp_table

RUN = ["strategy", "permutations", "profitable", "losing", "zero", "profitable_pct",
       "avg_profit", "top_profit", "stdev", "uniform_changes", "parameters"]


# 🔬 2026-09-26: one reader holds ~0.34 GB for a 12,000-permutation profile, so 48 of them
# would be 16 GB of the 20 the RAM budget gives Python; 16 keep it near 5.5 GB and still read
# 500 strategies in about a minute.
WORKERS = 16
# Where the workers spill their permutation rows, set before the fork.
_SPILL: dict = {}


def _read(path: Path) -> tuple[dict, dict | None]:
    """One strategy's profile, its permutations already spilled as its rows of the table.

    Args:
        path: A .sqx holding an optimization profile.

    Returns:
        (the profile without `original` and `results`, what spp_table.spill() returned or
        None when SQX kept no permutation). Done in the worker: handing 10,000 dicts of 170
        keys back to the parent cost more than reading them.
    """
    profile = optprofile.read(path)
    if not profile["permutation_results"]:
        return profile, None
    got = spp_table.spill(path.stem, profile, _SPILL["folder"])
    del profile["original"], profile["results"]
    return profile, got


def profiles(project: str, databank: str, install: Path, spill: Path) -> tuple[dict, dict]:
    """Read every SPP profile a databank's strategies carry, one process per file.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it, e.g. "SPP IS".
        install: Which SQX install holds it: the master, or a worker when the SPP was run
            on a harness there, which is the only way to run one without touching the
            owner's own projects.
        spill: Scratch directory the permutation rows are written into.

    Returns:
        (strategy name to the profile `core.optprofile.read` returns, minus its permutations;
        strategy name to what spp_table.spill() returned, for the strategies SQX kept them
        for). Strategies whose .sqx holds no profile were never cross-checked with SPP and
        are skipped silently.
    """
    found = {f: f.stat().st_size
             for f in sorted(databank_dir(project, databank, install).glob("*.sqx"))
             if optprofile.MEMBER in zipfile.ZipFile(f).namelist()}
    spill.mkdir(parents=True, exist_ok=True)
    _SPILL["folder"] = spill
    got = dict(fanout.run(_read, found, WORKERS))
    return ({f.stem: got[f][0] for f in found},
            {f.stem: got[f][1] for f in found if got[f][1] is not None})


def write_runs(found: dict, path: Path) -> int:
    """One row per strategy: how the permutation run as a whole came out.

    Args:
        found: Output of `profiles`.
        path: Parquet to write.

    Returns:
        Rows written. `parameters` is the space-joined list of what the SPP permuted.
    """
    rows = [{"strategy": name, "parameters": " ".join(p["params"]),
             **{k: p[k] for k in RUN[1:-1]}} for name, p in found.items()]
    pd.DataFrame(rows, columns=RUN).to_parquet(path, index=False)
    return len(rows)


def write_metrics(found: dict, path: Path) -> int:
    """One row per strategy and metric: the permutation median against the original value.

    Args:
        found: Output of `profiles`.
        path: Parquet to write.

    Returns:
        Rows written.
    """
    rows = [{"strategy": name, "metric": metric, "median": median,
             "orig": p["orig"][metric],
             "orig_over_median": p["orig"][metric] / median if median else float("nan")}
            for name, p in found.items() for metric, median in p["medians"].items()]
    pd.DataFrame(rows).to_parquet(path, index=False)
    return len(rows)


def write_histograms(found: dict, path: Path) -> int:
    """One row per strategy, metric and bin: the distribution over the permutations.

    Args:
        found: Output of `profiles`.
        path: Parquet to write.

    Returns:
        Rows written. Kept because the binning is SQX's own and cannot be derived back.
    """
    rows = [{"strategy": name, "metric": metric, **b}
            for name, p in found.items() for metric, chart in p["charts"].items()
            for b in optprofile.histogram(chart)]
    pd.DataFrame(rows).to_parquet(path, index=False)
    return len(rows)


def copy_mothers(project: str, databank: str, install: Path, out: Path) -> int:
    """Put each profiled strategy's own .sqx beside its profile.

    Args:
        project: Project name.
        databank: Databank the profiles were read from.
        install: Which install holds it.
        out: The export directory the Parquet tables were written into.

    Returns:
        How many were copied. `sqx/variants/inputs.py` resolves a mother as
        `<export>/strategies/<name>.sqx`, so without this the variant factory of step 16.5
        cannot open the strategy its own design brief describes.
    """
    dest = out / "strategies"
    dest.mkdir(parents=True, exist_ok=True)
    found = sorted(databank_dir(project, databank, install).glob("*.sqx"))
    for path in found:
        shutil.copy2(path, dest / path.name)
    return len(found)


def main() -> None:
    """Read every profile in a databank and write its Parquet tables into a dated directory."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--role", help="read a worker's install instead of the master")
    ap.add_argument("--out-databank", help="name the export directory this instead")
    a = ap.parse_args()

    install = worker_dir(a.role) if a.role else MASTER
    out = export_dir(a.project, a.out_databank or a.databank,
                     date.today().isoformat()) / "spp"
    out.mkdir(parents=True, exist_ok=True)
    found, spilled = profiles(a.project, a.databank, install, out / "_permutations")
    kept = list(spilled)

    counts = {"runs.parquet": write_runs(found, out / "runs.parquet"),
              "metrics.parquet": write_metrics(found, out / "metrics.parquet"),
              "histograms.parquet": write_histograms(found, out / "histograms.parquet")}
    if kept:
        counts["spp.parquet"] = spp_table.write(spilled, out / "_permutations",
                                                out / "spp.parquet")
    shutil.rmtree(out / "_permutations")
    manifest.write(out,
                   {"install": str(install), "project": a.project, "databank": a.databank,
                    "profiles_found": len(found),
                    "with_permutation_results": len(kept)},
                   f"export_spp.py --project {a.project} --databank {a.databank}",
                   counts)
    mothers = copy_mothers(a.project, a.databank, install, out.parent)
    print(f"{len(found)} profiles -> {out}")
    print(f"  strategies/      {mothers} madres, que es lo que abre la fábrica de variantes")
    for name, n in counts.items():
        print(f"  {name:16s} {n} rows")


if __name__ == "__main__":
    main()
