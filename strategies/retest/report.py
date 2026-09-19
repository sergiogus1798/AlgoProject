#!/usr/bin/env python3
"""The command: every strategy of one ingest, from parquet to a report and a verdict table."""

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core import manifest
from core.paths import report_dir
from strategies.retest import run
from strategies.retest.inputs import config, tasks
from strategies.retest.measure import store
from strategies.retest.render import panel, text
from strategies.retest.verdict import gates


def verdict_table(result: dict) -> pd.DataFrame:
    """One row per strategy: the call and what drove it.

    Args:
        result: What run.battery() returned.

    Returns:
        The frame the CSV is written from, worst composite first.
    """
    rows = [{"strategy": name, "verdict": got["verdict"]["verdict"],
             "composite": got["verdict"]["composite"],
             "binding": got["verdict"]["binding"],
             "stress_net_p5": round(got["stress"]["fragility"]["net_p5"]["point"], 2),
             "stress_cvar_dd_pct": round(got["stress"]["fragility"]["drawdown"]["cvar"], 2),
             "vetoes": "; ".join(got["verdict"]["vetoes"]),
             "blocked_by": "; ".join(got["verdict"]["blocked_by"])}
            for name, got in sorted(result["strategies"].items())]
    return pd.DataFrame(rows).sort_values("composite")


def markdown_table(frame: pd.DataFrame) -> str:
    """A frame as a markdown table.

    Args:
        frame: Any frame.

    Returns:
        Header, rule and one line per row. Written out rather than calling `to_markdown`,
        which pulls in `tabulate` -- a whole dependency pinned for one table.
    """
    head = "| " + " | ".join(frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    rows = ["| " + " | ".join(str(value) for value in row) + " |"
            for row in frame.itertuples(index=False)]
    return "\n".join([head, rule] + rows)


def strategy_section(name: str, got: dict) -> str:
    """One strategy's section of the report.

    Args:
        name: Strategy id.
        got: That strategy's entry in a run.battery() result.

    Returns:
        Markdown: the verdict, what fired, the eight tasks, and what broke it worst.
    """
    v = got["verdict"]
    lines = [f"## {name} — {v['verdict']} ({v['composite']:.1f}/100)", "",
             text.VERDICTS[v["verdict"]], "",
             "Subnotas: " + ", ".join(f"{k} {x:.0f}" for k, x in v["subscores"].items())
             + f". Limita: **{v['binding']}**.", ""]
    if got["flags"]:
        lines += ["### Qué saltó", ""] + [f"- {text.flag(f)}" for f in got["flags"]] + [""]
    lines += ["### Las ocho tareas", "",
              "| tarea | qué perturba | beneficio p5 | drawdown CVaR | operaciones vs original | forma |",
              "|---|---|---|---|---|---|"]
    lines += [text.task_line(task, got[task]) for task in tasks.TASKS if task in got]
    lines += ["", "### Qué la rompe, en unidades del control", "",
              f"El control mueve el resultado {got['attribution']['control_sigma']:,.0f} USD "
              "por sí solo. Todo lo de abajo está medido contra eso.", "",
              "| tarea | coste USD | en sigmas del control |", "|---|---|---|"]
    lines += [f"| {tasks.TITLES[r['task']]} | {r['cost']:,.0f} | {r['cost_in_sigmas']:.1f} |"
              for r in got["attribution"]["ranking"]]
    return "\n".join(lines + [""])


def page(result: dict, args: argparse.Namespace) -> str:
    """The whole report.

    Args:
        result: What run.battery() returned.
        args: The parsed command line.

    Returns:
        Markdown, ready to write.
    """
    table = verdict_table(result)
    head = [f"# Monte Carlo Retest — {args.project} / {args.databank} / {args.day}", "",
            "Ocho tareas, cada una perturbando una sola cosa, mil re-ejecuciones completas del "
            "backtest en cada una. La pregunta no es si la curva fue suerte, sino si habría "
            "existido.", "",
            "## Veredictos", "", markdown_table(table), "",
            "## De la batería entera", "", text.battery_note(result), "",
            "## Los umbrales son valores por defecto, no una política",
            "",
            "Los cortes de `gates.py` —cuánto drawdown aguanta la cuenta, qué parte del "
            "beneficio debe sobrevivir a la ejecución— salen del `config.yaml` y **nadie los ha "
            "calibrado todavía contra tu operativa real**. Si todas las estrategias fallan, lo "
            "primero que hay que mirar es si el umbral es el correcto, no si las estrategias lo "
            "son.", ""]
    return "\n".join(head + [strategy_section(n, g) for n, g in sorted(result["strategies"].items())])


def main() -> None:
    """Read one ingest and write its report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--databank", default="MCR_All")
    parser.add_argument("--day", default=date.today().isoformat())
    parser.add_argument("--set", action="append", dest="overrides", metavar="KEY=VALUE")
    args = parser.parse_args()

    missing = set(gates.VETOES) ^ set(text.SENTENCES)
    assert not missing, f"gates and text disagree about these vetoes: {sorted(missing)}"

    cfg = config.load(args.overrides)
    keys = {"project": args.project, "databank": args.databank, "day": args.day}
    provenance = manifest.read(store.root(**keys))["source"]["tasks"]
    result = run.battery(keys, provenance, cfg)

    out = report_dir(args.project, args.databank, args.day) / "retest"
    out.mkdir(parents=True, exist_ok=True)
    (out / "retest.md").write_text(page(result, args), encoding="utf-8")
    title = f"Monte Carlo Retest — {args.project} / {args.databank} / {args.day}"
    note = ("Ocho tareas, cada una perturbando una sola cosa, mil re-ejecuciones completas del "
            "backtest en cada una. La pregunta no es si la curva fue suerte, sino si habria "
            "existido.")
    (out / "retest.html").write_text(panel.page(result, title, note), encoding="utf-8")
    table = verdict_table(result)
    table.to_csv(out / "verdict.csv", index=False)
    manifest.write(out, {"project": args.project, "databank": args.databank,
                         "ingest_day": args.day, "config": config.flatten(cfg)},
                   " ".join(sys.argv), {"strategies": len(table)})

    print(f"report: {len(table)} strategies -> {out}")
    print(f"  abrelo: {out / 'retest.html'}")
    print(table.to_string(index=False, max_colwidth=40))


if __name__ == "__main__":
    main()
