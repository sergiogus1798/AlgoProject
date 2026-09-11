#!/usr/bin/env python3
"""Check whether one databank's conclusions hold on other, independently generated databanks."""

import argparse
from datetime import date

from tasks.analysis import improvement, metrics, replication
from tasks.reports import summary
from core import manifest
from core.paths import metrics_export, report_dir

TARGETS = ["Sharpe Ratio (OOS)", "Ret/DD Ratio (OOS)"]
FILTERS = 6
RESTRICTED = 0.7


def load(project: str, databanks: list[str]) -> dict:
    """Read the current metrics export of every databank being compared.

    Args:
        project: Project name.
        databanks: Databank names, the reference first.

    Returns:
        One entry per databank with its columns, strategy count and export date.
    """
    out = {}
    for databank in databanks:
        src = metrics_export(project, databank)
        columns, names = metrics.load(src / "metrics.csv")
        out[databank] = {"columns": columns, "n": len(names),
                         "exported": manifest.read(src)["date"]}
    return out


def outcomes(samples: dict, reference: str, target: str) -> list[str]:
    """Where each sample ended up out of sample, against the reference.

    Args:
        samples: load() output.
        reference: Name of the databank the conclusions came from.
        target: Full name of the out-of-sample column.

    Returns:
        Markdown lines.
    """
    level = improvement.breakeven(target)
    base = samples[reference]["columns"][target]
    rows = []
    for name, s in samples.items():
        row = dict(improvement.outcome(s["columns"][target], level), databank=name)
        row["hit_pct"] = 100 * row["hit"]
        gap = replication.hit_gap(base, s["columns"][target], level)
        row["gap"] = "—" if name == reference else f"{100 * gap['gap']:+.1f}"
        row["band"] = "—" if name == reference else \
            f"[{100 * gap['lo']:+.1f}, {100 * gap['hi']:+.1f}]"
        rows.append(row)
    return [summary.table(rows, [("databank", "databank", ""), ("n", "strategies", ","),
                                 ("median", "median", ".3f"), ("hit_pct", "hit %", ".1f"),
                                 ("gap", "Δ hit pp", ""), ("band", "95% CI on Δ", "")])]


def replicated(samples: dict, reference: str, target: str, is_metrics: list[str]) -> list[str]:
    """Whether the reference's best filters deliver what they promised on each other sample.

    Args:
        samples: load() output.
        reference: Name of the databank the conclusions came from.
        target: Full name of the out-of-sample column.
        is_metrics: In-sample metrics present in every sample.

    Returns:
        Markdown lines, one table per checked sample.
    """
    ref = samples[reference]["columns"]
    ranked = sorted(improvement.candidates(is_metrics),
                    key=lambda c: -replication.carried(ref, ref, c, target)["predicted"])
    best, seen = [], set()
    for candidate in ranked:
        if candidate["metric"] not in seen:
            seen.add(candidate["metric"])
            best.append(candidate)
        if len(best) == FILTERS:
            break

    lines = []
    for name, s in samples.items():
        if name == reference:
            continue
        rows = []
        for candidate in best:
            got = replication.carried(ref, s["columns"], candidate, target)
            rows.append({"filter": improvement.label(candidate),
                         "predicted": 100 * got["predicted"], "share": 100 * got["share"],
                         "n": got["n"], "observed": 100 * got["observed"],
                         "delta": 100 * (got["observed"] - got["predicted"]),
                         "band": f"[{100 * got['lo']:+.1f}, {100 * got['hi']:+.1f}]"})
        lines += ["", f"**{name}** — the reference's thresholds applied to it:", "",
                  summary.table(rows, [("filter", "filter", ""),
                                       ("predicted", "predicted hit %", ".1f"),
                                       ("share", "% of sample passing", ".1f"),
                                       ("n", "n", ","), ("observed", "observed hit %", ".1f"),
                                       ("delta", "Δ", "+.1f"), ("band", "95% CI on Δ", "")])]
    return lines


def agreement(samples: dict, reference: str, target: str, is_metrics: list[str]) -> list[str]:
    """Whether the samples rank the in-sample predictors the same way.

    Args:
        samples: load() output.
        reference: Name of the databank the conclusions came from.
        target: Full name of the out-of-sample column.
        is_metrics: In-sample metrics present in every sample.

    Returns:
        Markdown lines.
    """
    ref = replication.predictors(samples[reference]["columns"], target, is_metrics)
    lines = []
    for name, s in samples.items():
        if name == reference:
            continue
        here = replication.predictors(s["columns"], target, is_metrics)
        narrowed = [m for m in is_metrics
                    if replication.restriction(samples[reference]["columns"][m],
                                               s["columns"][m]) < RESTRICTED]
        lines.append(f"**{name}** ranks the predictors like the reference at "
                     f"ρ {replication.stability(ref, here):+.3f}.")
        if narrowed:
            lines.append(f"Selected on {len(narrowed)} metric(s) — "
                         + ", ".join(narrowed[:4])
                         + " — whose own correlations are attenuated here by construction.")
        lines.append("")
    return lines


def main() -> None:
    """Compare the current metrics exports of several databanks of one project."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--reference", required=True, help="databank the conclusions came from")
    ap.add_argument("--databank", action="append", required=True, help="repeatable; to check")
    ap.add_argument("--target", action="append", default=None)
    a = ap.parse_args()

    names = [a.reference] + [d for d in a.databank if d != a.reference]
    samples = load(a.project, names)
    common = sorted(set.intersection(*(set(metrics.measured(s["columns"], metrics.IS))
                                       for s in samples.values())))
    targets = [t for t in (a.target or TARGETS)
               if all(t in s["columns"] for s in samples.values())]

    lines = [f"# {a.project} — do the conclusions hold across samples?", "",
             f"Reference: **{a.reference}**. Checked against "
             + ", ".join(f"**{n}**" for n in names[1:]) + ".",
             f"Report {date.today().isoformat()} · code {manifest.code_version()} · "
             f"{len(common)} in-sample metrics common to every sample.", "",
             "Each sample is its own generation run, so the comparison that means something is "
             "the **outcome**: what the",
             "strategies actually did out of sample. A correlation measured inside a sample "
             "that was selected on that",
             "very metric is attenuated by construction and says nothing about whether the "
             "conclusion held."]
    for target in targets:
        lines += ["", f"## {target}", ""] + outcomes(samples, a.reference, target)
        lines += ["", "### Did the reference's filters deliver?", "",
                  "`predicted` is the hit rate the filter reached on the reference. `% of sample "
                  "passing` shows how much of",
                  "the sample already clears that same threshold — near 100% means the sample was "
                  "built to satisfy it."]
        lines += replicated(samples, a.reference, target, common)
        lines += ["", "### Do the samples agree on what predicts this?", ""]
        lines += agreement(samples, a.reference, target, common)

    out = report_dir(a.project, "_comparison", date.today().isoformat())
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest.write(out, {"project": a.project, "reference": a.reference, "databanks": names,
                         "exported": {n: s["exported"] for n, s in samples.items()}},
                   f"compare.py --project {a.project} --reference {a.reference} "
                   + " ".join(f"--databank {n}" for n in names[1:]),
                   {n: s["n"] for n, s in samples.items()})
    print(f"{len(names)} samples, {len(targets)} outcomes, {len(common)} common IS metrics")
    print(f"  {out / 'comparison.md'}")


if __name__ == "__main__":
    main()
