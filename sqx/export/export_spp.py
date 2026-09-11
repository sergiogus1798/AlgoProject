#!/usr/bin/env python3
"""Export a databank's Sys. Param Permutation profiles: the table, the histograms, the counts."""

import argparse
import csv
import zipfile
from datetime import date
from pathlib import Path

from core import manifest, optprofile
from core.paths import MASTER, databank_dir, export_dir

RUN = ["strategy", "permutations", "profitable", "losing", "zero", "profitable_pct",
       "avg_profit", "top_profit", "stdev", "uniform_changes", "parameters"]


def profiles(project: str, databank: str) -> dict:
    """Read every SPP profile a databank's strategies carry.

    Args:
        project: Project name on the master.
        databank: Databank name as SQX shows it, e.g. "SPP IS".

    Returns:
        Strategy name to the profile `core.optprofile.read` returns. Strategies whose .sqx
        holds no profile were never cross-checked with SPP and are skipped silently.
    """
    return {f.stem: optprofile.read(f)
            for f in sorted(databank_dir(project, databank, MASTER).glob("*.sqx"))
            if optprofile.MEMBER in zipfile.ZipFile(f).namelist()}


def write_runs(found: dict, path: Path) -> int:
    """One row per strategy: how the permutation run as a whole came out.

    Args:
        found: Output of `profiles`.
        path: CSV to write.

    Returns:
        Rows written.
    """
    with open(path, "w", newline="", encoding="utf-8") as fh:
        out = csv.DictWriter(fh, RUN)
        out.writeheader()
        for name, p in found.items():
            out.writerow({"strategy": name, "parameters": " ".join(p["params"]),
                          **{k: p[k] for k in RUN[1:-1]}})
    return len(found)


def write_metrics(found: dict, path: Path) -> int:
    """One row per strategy and metric: the permutation median against the original value.

    Args:
        found: Output of `profiles`.
        path: CSV to write.

    Returns:
        Rows written.
    """
    rows = [{"strategy": name, "metric": metric, "median": median,
             "orig": p["orig"][metric],
             "orig_over_median": p["orig"][metric] / median if median else ""}
            for name, p in found.items() for metric, median in p["medians"].items()]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        out = csv.DictWriter(fh, ["strategy", "metric", "median", "orig", "orig_over_median"])
        out.writeheader()
        out.writerows(rows)
    return len(rows)


def write_histograms(found: dict, path: Path) -> int:
    """One row per strategy, metric and bin: the distribution over the permutations.

    Args:
        found: Output of `profiles`.
        path: CSV to write.

    Returns:
        Rows written.
    """
    rows = [{"strategy": name, "metric": metric, **b}
            for name, p in found.items() for metric, chart in p["charts"].items()
            for b in optprofile.histogram(chart)]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        out = csv.DictWriter(fh, ["strategy", "metric", "bin", "edge", "frequency",
                                  "is_median", "is_orig"])
        out.writeheader()
        out.writerows(rows)
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


def write_permutations(found: dict, path: Path) -> int:
    """One row per permutation: every statistic SQX kept for it.

    Args:
        found: Output of `profiles`, holding profiles with `permutation_results` true.
        path: CSV to write.

    Returns:
        Rows written. Columns are the union over the databank, so a metric one strategy
        does not carry comes out blank rather than shifting the row.
    """
    metrics = sorted({m for p in found.values() for _, r in runs_of(p) for m in r["stats"]})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        out = csv.DictWriter(fh, ["strategy", "permutation", *metrics])
        out.writeheader()
        rows = 0
        for name, p in found.items():
            for i, r in runs_of(p):
                out.writerow({"strategy": name, "permutation": i, **r["stats"]})
                rows += 1
    return rows


def write_permutation_params(found: dict, path: Path) -> int:
    """One row per permutation and parameter: the value SQX gave it.

    Args:
        found: Output of `profiles`, holding profiles with `permutation_results` true.
        path: CSV to write.

    Returns:
        Rows written. SQX stores the whole permutation as one `Name=value,` string; this
        splits it so the table can be pivoted per parameter.
    """
    rows = [{"strategy": name, "permutation": i, "parameter": k, "value": v}
            for name, p in found.items() for i, r in runs_of(p)
            for k, _, v in (kv.partition("=") for kv in r["params"].split(",") if kv)]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        out = csv.DictWriter(fh, ["strategy", "permutation", "parameter", "value"])
        out.writeheader()
        out.writerows(rows)
    return len(rows)


def main() -> None:
    """Read every profile in a databank and write the three CSVs into a dated directory."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    a = ap.parse_args()

    found = profiles(a.project, a.databank)
    kept = [n for n, p in found.items() if p["permutation_results"]]
    out = export_dir(a.project, a.databank, date.today().isoformat()) / "spp"
    out.mkdir(parents=True, exist_ok=True)

    counts = {"runs.csv": write_runs(found, out / "runs.csv"),
              "metrics.csv": write_metrics(found, out / "metrics.csv"),
              "histograms.csv": write_histograms(found, out / "histograms.csv")}
    if kept:
        full = {n: p for n, p in found.items() if p["permutation_results"]}
        counts["permutations.csv"] = write_permutations(full, out / "permutations.csv")
        counts["permutation_params.csv"] = write_permutation_params(
            full, out / "permutation_params.csv")
    manifest.write(out,
                   {"install": str(MASTER), "project": a.project, "databank": a.databank,
                    "profiles_found": len(found),
                    "with_permutation_results": len(kept)},
                   f"export_spp.py --project {a.project} --databank {a.databank}",
                   counts)
    print(f"{len(found)} profiles -> {out}")
    for name, n in counts.items():
        print(f"  {name:16s} {n} rows")


if __name__ == "__main__":
    main()
