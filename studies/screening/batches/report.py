"""Can several builds of one cell be added up as one big build? Setup, funnel and repeats, in one line."""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path
from typing import TypedDict

import pandas as pd

from core.datapaths import project_registry
from core.paths import DATA, report_dir
from studies.screening.batches import measure

DATABANK = "Results"     # the gate judges the build's databank


class Batch(TypedDict):
    """One batch as the gate left it."""
    parts: pd.DataFrame
    funnel: pd.DataFrame
    print: dict[str, str | list[str]]
    gate: str


def read(project: str) -> Batch:
    """One batch as the gate left it: who went where, the funnel, and the setup it ran under.

    Args:
        project: The project the batch was built in; a retired one still has its reports.

    Returns:
        `parts`, `funnel` and `print` (`measure.fingerprint`), from the newest gate report.
    """
    gate = sorted((DATA / "reports" / project / DATABANK).glob("*/gate/verdict.csv"))[-1].parent
    funnel = pd.read_csv(gate / "funnel.csv")
    source = json.loads((gate / "manifest.json").read_text(encoding="utf-8"))["source"]
    with project_registry().open(encoding="utf-8", newline="") as f:
        row = [r for r in csv.DictReader(f) if r["name"] == project][-1]
    return Batch(parts=measure.parts(pd.read_csv(gate / "verdict.csv")), funnel=funnel,
                 print=measure.fingerprint(source, list(funnel["screen"]), row), gate=str(gate))


def text(lots: dict[str, Batch], fields: list[str], same: measure.Homogeneity | None,
         dup: list[measure.Repeat],
         verdict: tuple[str, str]) -> str:
    """The report, in the owner's language."""
    names = list(lots)
    total = sum(len(lot["parts"]) for lot in lots.values())
    out = [f"# Lotes de una celda — {' + '.join(names)}", "",
           f"**{verdict[0]}** — {verdict[1]}. Generadas acumuladas: {total:,}.", ""]
    if fields:
        out += ["## Configuración distinta", ""] + [
            f"- `{k}`: " + " · ".join(f"{n} = {lots[n]['print'][k]}" for n in names) for k in fields]
        return "\n".join(out) + "\n"
    assert same is not None
    out += ["## ¿Se comportan igual los lotes?", "",
            f"Ji-cuadrado entre lotes {same['chi2']:.1f}; p = {same['p']:.4f} barajando islas "
            f"enteras ({measure.DRAWS:,} veces), alarma por debajo de {measure.ALARM}. Las islas "
            f"de un mismo lote se dispersan {same['phi']:.1f} veces lo que darían sorteos "
            "independientes: por eso se barajan islas y no estrategias.", "",
            "| lote | generadas | sobreviven al 8 | en cuántas islas | la isla que más lleva |",
            "|---|---|---|---|---|"]
    for n in names:
        s = measure.spread(lots[n]["parts"])
        out.append(f"| {n} | {len(lots[n]['parts']):,} | {s['alive']} | {s['islands']} de "
                   f"{s['of']} | isla {s['top']}: {s['top_n']} |")
    rules = measure.by_rule({n: lots[n]["funnel"] for n in names})
    out += ["", "Por regla, de las que llegan a ella (diagnóstico, no prueba: con estrategias "
            "emparentadas estas z salen más grandes que con el azar solo):", "",
            "| regla | " + " | ".join(f"mueren {n}" for n in names) + " | "
            + " | ".join(f"z {n}" for n in names[1:]) + " |",
            "|---|" + "---|" * (2 * len(names) - 1)]
    for _, r in rules.iterrows():
        died = " | ".join(f"{r[f'died {n}']:,.0f} de {r[f'entered {n}']:,.0f} "
                          f"({r[f'rate {n}']:.1%})" for n in names)
        out.append(f"| {r['screen']} | {died} | "
                   + " | ".join(f"{r[f'z {n}']:+.1f}" for n in names[1:]) + " |")
    out += ["", "## ¿Estoy generando lo que ya tenía?", "",
            f"Aviso a partir del {measure.WARN:.0%} del lote, parar la celda desde el "
            f"{measure.STOP:.0%}.", "",
            "| lote | repetidas | del lote | supervivientes repetidas | la celda tiene al menos |",
            "|---|---|---|---|---|"]
    for d in dup:
        bound = f"{'> ' if not d['repeated'] else ''}{d['space']:,.0f} distintas"
        out.append(f"| {d['batch']} | {d['repeated']:,} de {d['generated']:,} | {d['share']:.1%} | "
                   f"{d['alive_repeated']} de {d['alive']} | {bound} |")
    out += ["", "La huella es exacta: dos estrategias con el periodo 14 y 15 cuentan como distintas. "
            "No ve un error común a todos los lotes, ni las casi gemelas."]
    return "\n".join(out) + "\n"


def main() -> None:
    """Read each project's gate report and say whether the batches add up."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("projects", nargs="+", help="los lotes, del más antiguo al más nuevo")
    a = ap.parse_args()

    lots = {p: read(p) for p in a.projects}
    fields = measure.differing({p: lot["print"] for p, lot in lots.items()})
    parts = {p: lot["parts"] for p, lot in lots.items()}
    dup = measure.repeats(parts)
    same = None if fields else measure.homogeneity(measure.table(parts))
    verdict = measure.decision(fields, same, dup)
    out = report_dir(a.projects[-1], DATABANK, date.today().isoformat()) / "batches"
    out.mkdir(parents=True, exist_ok=True)
    page = text(lots, fields, same, dup, verdict)
    (out / "batches.md").write_text(page, encoding="utf-8")
    (out / "batches.json").write_text(json.dumps(
        {"verdict": verdict[0], "why": verdict[1], "differing": fields, "homogeneity": same,
         "repeats": dup, "inputs": {p: lot["gate"] for p, lot in lots.items()}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(page)
    print(f"-> {Path(out) / 'batches.md'}")
    sys.exit(0 if verdict[0] in ("SUMAR", "AVISO") else 1)


if __name__ == "__main__":
    main()
