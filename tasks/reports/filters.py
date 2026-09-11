#!/usr/bin/env python3
"""Sweep in-sample filters against out-of-sample outcomes and write improvement.md."""

import argparse
from datetime import date

from tasks.analysis import correlations, improvement, metrics
from tasks.reports import summary
from core import manifest
from core.paths import metrics_export, report_dir

TARGETS = ["Sharpe Ratio (OOS)", "Ret/DD Ratio (OOS)"]
COLUMNS = [("metric", "filter", ""), ("n", "kept", ","), ("median", "median", ".3f"),
           ("d_median", "Δ median", "+.3f"), ("band", "95% CI on Δ", ""),
           ("hit_pct", "hit %", ".1f"), ("d_hit_pp", "Δ hit pp", "+.1f"),
           ("p", "p", ".2e"), ("mark", "BH", "")]


def rendered(rows: list[dict], found: set[str], top: int) -> list[dict]:
    """Turn sweep rows into the strings the table prints.

    Args:
        rows: Rows from analysis.improvement.sweep, best first.
        found: Labels surviving Benjamini-Hochberg.
        top: How many rows to keep.

    Returns:
        The first top rows with the interval and the percentages preformatted.
    """
    return [dict(r, band=f"[{r['d_median_lo']:+.3f}, {r['d_median_hi']:+.3f}]",
                 hit_pct=100 * r["hit"], d_hit_pp=100 * r["d_hit"],
                 mark="✓" if r["metric"] in found else "")
            for r in rows[:top]]


def section(target: str, base: dict, rows: list[dict], found: set[str], top: int) -> list[str]:
    """The block of the report covering one out-of-sample outcome.

    Args:
        target: Full name of the out-of-sample column.
        base: Unfiltered outcome from analysis.improvement.outcome.
        rows: Rows from the sweep for this target, best first.
        found: Labels surviving Benjamini-Hochberg for this target.
        top: How many filters to list.

    Returns:
        Markdown lines.
    """
    level = improvement.breakeven(target)
    survived = [r for r in rows if r["metric"] in found and r["d_median"] > 0]
    lines = [
        "", f"## {target}", "",
        f"Unfiltered: {base['n']:,} strategies · median {base['median']:.3f} · "
        f"{100 * base['hit']:.1f}% above {level:g}.",
        f"{len(survived)} of the {len(rows)} filters judged both improve the median and survive "
        "the correction.", "",
        summary.table(rendered(rows, found, top), COLUMNS),
    ]
    if survived:
        best = survived[0]
        lines += ["", f"Best surviving filter: **{best['metric']}** — keeps {best['n']:,} "
                  f"strategies, median {best['median']:.3f} ({best['d_median']:+.3f}), "
                  f"hit rate {100 * best['hit']:.1f}% ({100 * best['d_hit']:+.1f} pp)."]
    return lines


def main() -> None:
    """Read a databank's current metrics export and write the filter sweep for it."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--target", action="append", default=None, help="repeatable; OOS column")
    ap.add_argument("--top", type=int, default=15, help="filters listed per outcome")
    a = ap.parse_args()

    src = metrics_export(a.project, a.databank)
    columns, names = metrics.load(src / "metrics.csv")
    made = manifest.read(src)
    is_metrics = metrics.measured(columns, metrics.IS)
    targets = [t for t in (a.target or TARGETS) if t in metrics.measured(columns, metrics.OOS)]
    tried = len(improvement.candidates(is_metrics))

    lines = [
        f"# {a.project} / {a.databank} — what a filter buys",
        "",
        f"{len(names):,} strategies · view \"{made['source']['view']}\" · exported "
        f"{made['date']} · report {date.today().isoformat()} · code {manifest.code_version()}",
        "",
        f"Every in-sample metric was cut at {'/'.join(str(c) for c in improvement.CUTS)}% from "
        f"both ends: {tried} candidate filters over {len(is_metrics)} metrics. A candidate is",
        f"only judged if it leaves at least {improvement.MIN_SURVIVORS} strategies, and the ones",
        "judged are corrected together with Benjamini-Hochberg at a 5% false discovery rate.",
        "",
        "Δ is the survivors minus the whole population. The interval is a "
        f"{improvement.DRAWS}-draw bootstrap",
        "on that difference, so a band straddling zero means the improvement is not "
        "distinguishable from noise.",
        f"The bootstrap p cannot go below 1/{improvement.DRAWS} by construction: where it sits "
        "at that floor, read the",
        "interval rather than the p-value.",
    ]
    for target in targets:
        rows = improvement.sweep(columns, is_metrics, target)
        base = improvement.outcome(columns[target], improvement.breakeven(target))
        lines += section(target, base, rows, correlations.discoveries(rows), a.top)

    out = report_dir(a.project, a.databank, date.today().isoformat()) / "filters"
    out.mkdir(parents=True, exist_ok=True)
    (out / "improvement.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest.write(out, {"project": a.project, "databank": a.databank,
                         "view": made["source"]["view"], "csv": str(src / "metrics.csv")},
                   f"filters.py --project {a.project} --databank {a.databank}",
                   {"strategies": len(names), "candidates": tried, "targets": targets})
    print(f"{tried} candidate filters over {len(names)} strategies, {len(targets)} outcomes")
    print(f"  {out / 'improvement.md'}")


if __name__ == "__main__":
    main()
