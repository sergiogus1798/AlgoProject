#!/usr/bin/env python3
"""Export a databank's Sys. Param Permutation profiles: one wide table, the histograms, the counts."""

import argparse
import shutil
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from core import manifest, optprofile
from core.paths import MASTER, databank_dir, export_dir, worker_dir

RUN = ["strategy", "permutations", "profitable", "losing", "zero", "profitable_pct",
       "avg_profit", "top_profit", "stdev", "uniform_changes", "parameters"]


def profiles(project: str, databank: str, install: Path = MASTER) -> dict:
    """Read every SPP profile a databank's strategies carry.

    Args:
        project: Project name on the master.
        databank: Databank name as SQX shows it, e.g. "SPP IS".
        install: Which SQX install holds it. The master by default; a worker when the SPP
            was run on a harness there, which is the only way to run one without touching
            the owner's own projects.

    Returns:
        Strategy name to the profile `core.optprofile.read` returns. Strategies whose .sqx
        holds no profile were never cross-checked with SPP and are skipped silently.
    """
    return {f.stem: optprofile.read(f)
            for f in sorted(databank_dir(project, databank, install).glob("*.sqx"))
            if optprofile.MEMBER in zipfile.ZipFile(f).namelist()}


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


def runs_of(profile: dict) -> list[tuple[int, dict]]:
    """The original result and every permutation of one profile, numbered.

    Args:
        profile: Output of `core.optprofile.read` with `permutation_results` true.

    Returns:
        `(-1, original)` first, then `(0, first permutation)` onwards. The original is the
        strategy as SQX saved it, so it is the row every permutation is compared against.
    """
    return [(-1, profile["original"])] + list(enumerate(profile["results"]))


def table(found: dict) -> pd.DataFrame:
    """One row per permutation: its parameter values wide, then every statistic SQX kept.

    Args:
        found: Output of `profiles`, holding profiles with `permutation_results` true.

    Returns:
        Columns `strategy` (categorical), `permutation` (-1 is the original, the row every
        permutation is compared against), one column per parameter any strategy permuted
        (NaN where this strategy did not), then the statistics. Wide on purpose: the long
        form measured 34 MB in memory for 21,205 x 8 numbers that fit in 6 MB wide, and a
        reader that needs four of 154 columns can ask Parquet for just those.

    Raises:
        SystemExit: A parameter and a statistic share a name, which would silently merge
            two columns.
    """
    rows = []
    for name, p in found.items():
        for i, r in runs_of(p):
            params = {k: v for k, _, v in (kv.partition("=") for kv in r["params"].split(",") if kv)}
            rows.append({"strategy": name, "permutation": i, **params, **r["stats"]})
    names = sorted({k for p in found.values() for _, r in runs_of(p)
                    for k in (kv.partition("=")[0] for kv in r["params"].split(",") if kv)})
    stats = sorted({m for p in found.values() for _, r in runs_of(p) for m in r["stats"]})
    if set(names) & set(stats):
        raise SystemExit(f"parameter and statistic share a name: {sorted(set(names) & set(stats))}")
    frame = pd.DataFrame(rows, columns=["strategy", "permutation", *names, *stats])
    frame[names] = frame[names].apply(pd.to_numeric, errors="coerce")
    frame["strategy"] = frame["strategy"].astype("category")
    frame["permutation"] = frame["permutation"].astype("int32")
    return frame


def write_table(found: dict, path: Path) -> int:
    """Write `table(found)` as one zstd Parquet.

    Args:
        found: Output of `profiles`, holding profiles with `permutation_results` true.
        path: Parquet to write.

    Returns:
        Rows written.
    """
    frame = table(found)
    frame.to_parquet(path, compression="zstd", index=False)
    return len(frame)


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
    found = profiles(a.project, a.databank, install)
    kept = [n for n, p in found.items() if p["permutation_results"]]
    out = export_dir(a.project, a.out_databank or a.databank,
                     date.today().isoformat()) / "spp"
    out.mkdir(parents=True, exist_ok=True)

    counts = {"runs.parquet": write_runs(found, out / "runs.parquet"),
              "metrics.parquet": write_metrics(found, out / "metrics.parquet"),
              "histograms.parquet": write_histograms(found, out / "histograms.parquet")}
    if kept:
        full = {n: p for n, p in found.items() if p["permutation_results"]}
        counts["spp.parquet"] = write_table(full, out / "spp.parquet")
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
