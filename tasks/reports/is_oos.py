#!/usr/bin/env python3
"""Build the interactive IS/OOS panel and its written summary for one databank."""

import argparse
import json
from datetime import date
from pathlib import Path

from tasks.analysis import correlations, metrics
from tasks.reports import summary
from core import manifest
from core.paths import metrics_export, report_dir

TEMPLATE = Path(__file__).with_name("panel.html")
TARGETS = ["Profit factor (OOS)", "Sharpe Ratio (OOS)", "Ret/DD Ratio (OOS)", "Net profit (OOS)"]


def payload(columns: dict, names: list[str], source: dict,
            is_metrics: list[str], oos_metrics: list[str]) -> dict:
    """Everything the HTML panel needs, ready to embed.

    Args:
        columns: Numeric columns from analysis.metrics.load.
        names: Strategy names in row order.
        source: What produced the export, shown in the page header.
        is_metrics, oos_metrics: Full column names, in menu order.

    Returns:
        A JSON-serialisable dict. The page carries every strategy because it recomputes
        its statistics whenever a filter changes; five decimals keeps that a few megabytes.
    """
    return {"source": source, "names": names, "is": is_metrics, "oos": oos_metrics,
            "data": {k: [round(float(v), 5) for v in col] for k, col in columns.items()}}


def main() -> None:
    """Read a databank's current metrics export and write one dated report from it."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    a = ap.parse_args()

    src = metrics_export(a.project, a.databank)
    columns, names = metrics.load(src / "metrics.csv")
    made = manifest.read(src)
    source = {"project": a.project, "databank": a.databank, "view": made["source"]["view"],
              "exported": made["date"], "reported": date.today().isoformat(),
              "code_version": manifest.code_version()}

    is_metrics = metrics.measured(columns, metrics.IS)
    oos_metrics = metrics.measured(columns, metrics.OOS)
    ranked = {t: correlations.predictors(columns, t, is_metrics)
              for t in TARGETS if t in oos_metrics}
    found = {t: correlations.discoveries(rows) for t, rows in ranked.items()}
    persist = correlations.persistence(columns, metrics.paired(columns))

    out = report_dir(a.project, a.databank, source["reported"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(
        summary.render(source, len(names), correlations.critical_r(len(names)),
                       persist, ranked, found), encoding="utf-8")
    (out / "explorer.html").write_text(
        TEMPLATE.read_text(encoding="utf-8").replace(
            "__PAYLOAD__",
            json.dumps(payload(columns, names, source, is_metrics, oos_metrics))),
        encoding="utf-8")

    manifest.write(out, dict(source, csv=str(src / "metrics.csv")),
                   f"is_oos.py --project {a.project} --databank {a.databank}",
                   {"strategies": len(names), "is_metrics": len(is_metrics),
                    "oos_metrics": len(oos_metrics), "targets": list(ranked)})
    print(f"{len(names)} strategies, {len(is_metrics)} IS metrics x {len(oos_metrics)} OOS")
    print(f"  {out / 'explorer.html'}")
    print(f"  {out / 'summary.md'}")


if __name__ == "__main__":
    main()
