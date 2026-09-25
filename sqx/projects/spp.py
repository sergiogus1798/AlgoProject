#!/usr/bin/env python3
"""Write the two SPP tasks of a custom project: the permutation grid, one window each."""

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.assetcheck import pending
from core.assetdata import doctrine, load
from sqx.projects.configure import running_install
from sqx.projects.crosschecks import active, enable, member_of, others_on, recommended, silence
from sqx.projects.databanks import set_databank
from sqx.projects.setups import bounds, set_costs
from sqx.projects.tasksettings import set_precision

# ⚠️ The SPP is OptProfileSysParamPermutation. SequentialOptimization sits beside it in the
# same <CrossChecks> block, is also about permuting parameters, and writes no profile at
# all -- enabling it burned 47 cores for 91 minutes and produced nothing (2026-09-22).
BLOCK = re.compile(r"<OptProfileSysParamPermutation\b.*?</OptProfileSysParamPermutation>",
                   re.S)
EVALUATIONS = ("EvalProfitOptCheck", "EvalAvgProfitCheck", "EvalUniformDistrCheck",
               "EvalTopProfitCheck")


def settings(block: str, cfg: dict) -> tuple[str, int]:
    """Write the grid the permutation walks.

    Args:
        block: The <OptProfileSysParamPermutation> element.
        cfg: The `spp` block of _build.yaml.

    Returns:
        The element and the number of steps written. `Steps` is derived rather than
        declared: the walk spans `2 * spread` percent and one step moves a parameter by
        `step_pct`, so 18 steps at ±35 is ~4 % a step. Twelve steps over ±30, which is
        what the donor carries, is 5 % and coarse.
    """
    steps = round(2 * cfg["spread_pct"] / cfg["step_pct"])
    for tag, value in (("MaxTests", cfg["max_tests"]),
                       ("DistributionUp", cfg["spread_pct"]),
                       ("DistributionDown", cfg["spread_pct"]), ("Steps", steps)):
        block = re.sub(rf"<{tag}>\d+</{tag}>", f"<{tag}>{value}</{tag}>", block, count=1)
    return recommended(block), steps


def evaluations_off(block: str) -> tuple[str, int]:
    """Stop the SPP judging the strategies it permutes.

    Args:
        block: The <OptProfileSysParamPermutation> element.

    Returns:
        The element and how many checks were turned off. The four Eval*Check flags are the
        SPP's own acceptance — `ProfitOptPct 70` on the donor's IS task means a strategy
        whose permutations are profitable less than 70 % of the time is dropped. This step
        maps a surface; the surface of the strategies that already passed a filter is a
        different object, and `studies/breakage/spp/` would be reading it without knowing.
    """
    done = 0
    for flag in EVALUATIONS:
        block, n = re.subn(rf"<{flag}>true</{flag}>", f"<{flag}>false</{flag}>", block)
        done += n
    return block, done


def write_task(text: str, spec: dict, data: dict, cfg: dict) -> tuple[str, dict]:
    """Turn one Retest task into the SPP task the catalogue describes.

    Args:
        text: A task XML.
        spec: One task of the `spp` catalogue.
        data: One asset as load() returned it.
        cfg: The `spp` block of _build.yaml.

    Returns:
        The task and what was written. The cross-check is switched on here and not by
        `doctrine.apply_doctrine`, which writes `crosschecks.default: []` into every task
        without a generator and so leaves this one running a plain retest — named SPP,
        permuting nothing, and silent about it.
    """
    text, setups = set_costs(text, data, spec["segment"])
    text = set_precision(text, spec["precision"])
    found = BLOCK.search(text)
    block, steps = settings(found.group(0), cfg)
    block, checks = evaluations_off(block)
    text = text[:found.start()] + block + text[found.end():]
    text, silenced = silence(enable(text, "OptProfileSysParamPermutation"))
    start, end = bounds(data, spec["segment"])
    return text, {"segment": spec["segment"], "from": start, "to": end, "steps": steps,
                  "precision": spec["precision"], "setups": setups, "silenced": silenced,
                  "evaluations_off": checks,
                  "others_on": others_on(text, "OptProfileSysParamPermutation")}


def configure(cfx: Path, symbol: str, source: str) -> dict:
    """Write both SPP tasks of one project, and say what each one runs.

    Args:
        cfx: Path of a project.cfx. Must not be held by a running install.
        symbol: Asset name, e.g. "XAUUSD".
        source: The databank the first task reads — the survivors of whatever step came
            before. The second reads what the first wrote, which is the whole population
            again: with the acceptance off nothing is dropped, so the chain carries every
            strategy into the out-of-sample reconnaissance.

    Returns:
        One row per catalogue task under "tasks", plus the project name.
    """
    data = load(symbol)
    cfg = doctrine()["spp"]
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    config = members["config.xml"].decode("utf-8")

    rows, reads = [], source
    for spec in cfg["tasks"]:
        member = member_of(config, spec["title"])
        if not member:
            rows.append({"title": spec["title"], "written": False,
                         "why": f"el proyecto no lleva la tarea {spec['title']}"})
            continue
        text, done = write_task(members[member].decode("utf-8"), spec, data, cfg)
        text, _ = set_databank(text, "Input", reads)
        text, _ = set_databank(text, "Output", spec["title"])
        members[member] = text.encode("utf-8")
        config = active(config, spec["title"], True)
        rows.append({"title": spec["title"], "member": member, "written": True,
                     "reads": reads, "writes": spec["title"], **done})
        reads = spec["title"]

    members["config.xml"] = config.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    return {"project": ElementTree.fromstring(config).get("name"), "input": source,
            "max_tests": cfg["max_tests"], "spread_pct": cfg["spread_pct"], "tasks": rows}


def main() -> None:
    """Configure a project's SPP tasks, refusing on anything undecided."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol")
    ap.add_argument("--cfx", required=True, type=Path)
    ap.add_argument("--input", required=True,
                    help="databank que lee la primera tarea. No se adivina: son los "
                         "supervivientes del paso anterior")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    missing = pending(load(a.symbol))
    if missing:
        raise SystemExit(f"{a.symbol}: {', '.join(missing)} sin valor pactado. "
                         "Preguntale al dueno antes de configurar nada (regla dura 5).")
    held = running_install(a.cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al "
                         f"salir. Parala: bin/sqx-worker.sh --role {held} stop")
    done = configure(a.cfx, a.symbol, a.input)

    if a.json:
        print(json.dumps(done, indent=2, default=str))
        return
    print(f"{done['project']}  {a.symbol}  <- {done['input']}")
    for row in done["tasks"]:
        if not row["written"]:
            print(f"  ⊘ {row['title']:<8} NO configurada — {row['why']}")
            continue
        print(f"  ✓ {row['title']:<8} {row['segment']} {row['from']}→{row['to']}  "
              f"±{done['spread_pct']} % en {row['steps']} pasos, tope "
              f"{done['max_tests']:,} permutaciones, precision {row['precision']}")
        print(f"      {row['reads']} → {row['writes']}   {row['silenced']} condicion(es) y "
              f"{row['evaluations_off']} chequeo(s) del SPP apagados")
        if row["others_on"]:
            print(f"      ⚠️ esta tarea corre ademas: {', '.join(row['others_on'])} — el "
                  "proyecto no paso por la doctrina")
    print("\nEl perfil lo guarda cada .sqx del databank de salida: sacalo con "
          "sqx/export/export_spp.py y leelo con studies/breakage/spp/.")
    print("⚠️ Una SPP a la vez por instalacion: el perfil ocupa decenas de GB mientras se "
          "construye (medido 2026-09-22).")


if __name__ == "__main__":
    main()
