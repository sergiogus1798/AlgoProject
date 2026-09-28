#!/usr/bin/env python3
"""The IS/OOS study of one databank: the population's correlation map (with its explorer) from the
metrics export, and each strategy's per-trade distributions IS against OOS from the newest harvest."""

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from core import manifest
from core.paths import harvest_dir, metrics_export, report_dir
from core.study import config as study_config, output
from core.study.render import markdown
from core.study.result import progress
from studies.screening.analysis import metrics
from studies.screening.isOos import many, one

TEMPLATE = Path(__file__).with_name("panel.html")
CONFIG = Path(__file__).with_name("config.yaml")
TRADES = ["identity", "sample", "Open time", "Close time", "Profit/Loss", "Balance", "Size",
          "MAE ($)", "MFE ($)"]


def payload(columns: dict, names: list[str], source: dict,
            is_metrics: list[str], oos_metrics: list[str]) -> dict:
    """Everything the interactive explorer needs, ready to embed.

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


def config(overrides: list[str]) -> dict:
    """Every knob of config.yaml, with `--set section.key=value` applied."""
    return study_config.load(CONFIG, overrides)


def population(project: str, databank: str, cfg: dict) -> dict:
    """The population half: the correlation map over the metrics export, and the explorer.

    Args:
        project, databank: Whose export.
        cfg: The study's config.

    Returns:
        `result`, `source`, `input` and `counts`, for the page and the manifest.
    """
    src = metrics_export(project, databank)
    columns, names = metrics.load(src / "metrics.csv")
    made = manifest.read(src)
    # Exports before 2026-09-27 went through the view on the conductor and name it; since
    # then they are read off the .sqx and say so under `metrics`.
    origin = (f"vista «{made['source']['view']}»" if "view" in made["source"]
              else "métricas leídas de cada .sqx")
    source = {"project": project, "databank": databank, "origin": origin,
              "exported": made["date"], "reported": date.today().isoformat(),
              "code_version": manifest.code_version()}
    is_metrics = metrics.measured(columns, metrics.IS)
    oos_metrics = metrics.measured(columns, metrics.OOS)
    got = many.run({"columns": columns, "n": len(names), "is": is_metrics,
                    "oos": oos_metrics}, cfg)
    explorer = TEMPLATE.read_text(encoding="utf-8").replace(
        "__PAYLOAD__", json.dumps(payload(columns, names, source, is_metrics, oos_metrics)))
    return {"result": got, "source": source, "explorer": explorer,
            "input": str((src / "metrics.csv").resolve()),
            "counts": {"strategies": len(names), "is_metrics": len(is_metrics),
                       "oos_metrics": len(oos_metrics)}}


def per_trade(folder: Path, out: Path, title: str, cfg: dict) -> dict:
    """The per-trade half: every strategy of a harvest, IS against OOS, one page each.

    Args:
        folder: The harvest folder, harvest/<P>/<D>/<day>/.
        out: The report folder.
        title: Heading prefix of each page.
        cfg: The study's config.

    Returns:
        Counts for the manifest: strategies written, and those skipped for lacking a sample.
    """
    names = pd.read_parquet(folder / "metrics.parquet", columns=["strategy"])["strategy"]
    trades = pd.read_parquet(folder / "trades.parquet", columns=TRADES)
    trades["sample"] = trades["sample"].astype(str)
    stray = set(trades["sample"]) - {"IS", "OOS"}
    if stray:
        raise ValueError(f"{folder}: samples {sorted(stray)} besides IS and OOS; "
                         f"OOS2 is not read here")
    groups = dict(tuple(trades.groupby("identity")))
    full = [i for i, g in groups.items() if g["sample"].nunique() == 2]
    for n, identity in enumerate(full):
        got = one.run(names[identity], {"identity": identity, "trades": groups[identity]}, cfg)
        output.member(out, got, f"{title} — {names[identity]}")
        progress(5 + 95 * (n + 1) // len(full), names[identity])
    return {"trade_strategies": len(full), "trade_skipped_one_sample": len(groups) - len(full)}


def main() -> None:
    """Both halves over one databank, each where its input exists; one dated report."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    a = ap.parse_args()

    cfg = config(a.set)
    has_metrics = (metrics_export(a.project, a.databank) / "metrics.csv").exists()
    harvests = sorted(harvest_dir(a.project, a.databank, "_").parent.glob("*/trades.parquet"))
    if not has_metrics and not harvests:
        raise SystemExit(f"{a.project}/{a.databank}: ni export de métricas (skill /export) "
                         f"ni cosecha (studies.screening.gate.harvest, skill /oos-gate)")
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "isOos"
    title = f"{a.project} / {a.databank} — dentro de muestra contra fuera"
    source, counts, inputs = {"project": a.project, "databank": a.databank,
                              "reported": date.today().isoformat(),
                              "code_version": manifest.code_version()}, {}, []
    progress(1, "leyendo")
    if has_metrics:
        pop = population(a.project, a.databank, cfg)
        output.population(out, "isOos", pop["result"], title,
                          f"{pop['counts']['strategies']:,} estrategias · "
                          f"{pop['source']['origin']} · exportado {pop['source']['exported']}.")
        # The explorer recomputes every statistic in the browser as a filter changes; it stays
        # until the window has an IS/OOS zone that filters, and is the last page that needs one.
        (out / "explorer.html").write_text(pop["explorer"], encoding="utf-8")
        source |= pop["source"]
        counts |= pop["counts"]
        inputs.append(pop["input"])
        print(markdown.render(pop["result"], title))
    if harvests:
        folder = harvests[-1].parent
        counts |= per_trade(folder, out, title, cfg)
        source["harvest"] = str(folder.resolve())
        inputs.append(str((folder / "trades.parquet").resolve()))
        print(f"{counts['trade_strategies']} estrategias IS contra OOS por operación "
              f"({counts['trade_skipped_one_sample']} sin una de las dos muestras) "
              f"-> {out / 'estrategias'}")
    manifest.write(out, dict(source, input=inputs[0], inputs=inputs, overrides=a.set),
                   " ".join(["python3 -m studies.screening.isOos.report", "--project",
                             a.project, "--databank", a.databank, *a.set]), counts)
    progress(100, "hecho")
    print(f"  {out}")


if __name__ == "__main__":
    main()
