#!/usr/bin/env python3
"""Write the Walk Forward Matrix task of a custom project: the grid, and the reserved window."""

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.assetcheck import pending
from core.assetdata import doctrine, load, policy, sqx_settings, window
from sqx.projects.acceptance import acceptance, area
from sqx.projects.configure import running_install
from sqx.projects.crosschecks import active, enable, member_of, others_on, recommended, silence
from sqx.projects.databanks import set_databank
from sqx.projects.setups import bounds, set_costs, set_data_range
from sqx.projects.tasksettings import set_precision

BLOCK = re.compile(r"<WalkForwardMatrix\b.*?</WalkForwardMatrix>", re.S)
# 🔬 Decoded 2026-09-24 (`OptimizationConst.wfTypeToString`): `type` is the "Walk-Forward
# type" of the GUI, not a flag saying the element is a matrix -- what makes it a matrix is
# being a <WalkForwardMatrix>, whose Param1/Param2 carry ranges. Exact re-backtests the
# window for real; simulated slices it out of one backtest already computed, which also
# decides WHICH parameters each step picks. The label is SQX's own, so the output says what
# the GUI would say.
WF_TYPES = {"simulated_is_simulated_oos": (0, "Simulated IS, Simulated OOS (fastest)"),
            "simulated_is_exact_oos": (1, "Simulated IS, Exact OOS (slower)"),
            "exact_is_exact_oos": (2, "Exact IS, Exact OOS (slow)")}
# 🔬 Decoded 2026-09-24 from the install's own plugin (`CrossCheckWalkForwardMatrix`): the two
# integers the donor carried are enums. The period type is what makes Param1 a percentage and
# Param2 a number of passes; with `days` or `bars` both axes would be lengths and the grid
# would mean something else. The optimisation type says whether the optimisation window slides
# (floating) or stays anchored at the start (fixed).
PERIOD_TYPES = {"percent": 10, "days": 20, "bars": 30}
OPTIMIZATION_TYPES = {"floating": 15, "fixed": 25}


def grid(cfg: dict) -> tuple[int, int]:
    """Args:
        cfg: The `wfm` block of _build.yaml.

    Returns:
        How many rows and columns the matrix has. Rows are the numbers of passes and columns
        the out-of-sample percentages, in that order: it is how SQX lays the matrix out
        (`WalkForwardMatrixResult.createMatrix`, decompiled 2026-09-24) and therefore what
        the area rule slides its rectangle over.
    """
    oos, runs = cfg["oos_pct"], cfg["runs"]
    return (len(range(runs["start"], runs["stop"] + 1, runs["step"])),
            len(range(oos["start"], oos["stop"] + 1, oos["step"])))


def axes(cfg: dict) -> tuple[str, int]:
    """The two ranges the matrix sweeps, as the <WalkForward> element writes them.

    Args:
        cfg: The `wfm` block of _build.yaml.

    Returns:
        The <WalkForward> element and how many steps one parameter is moved in. SQX takes
        `maxSteps`, not a step size, so it is derived the way the SPP derives its own: the
        walk spans `2 * distribution_pct` percent and one step moves `step_pct`.
    """
    oos, runs = cfg["oos_pct"], cfg["runs"]
    steps = round(2 * cfg["distribution_pct"] / cfg["step_pct"])
    return (f'<WalkForward type="{WF_TYPES[cfg["wf_type"]][0]}" '
            f'period="{PERIOD_TYPES[cfg["period_type"]]}" '
            f'optimization="{OPTIMIZATION_TYPES[cfg["optimization_type"]]}" '
            f'distributionUp="{cfg["distribution_pct"]}" '
            f'distributionDown="{cfg["distribution_pct"]}" maxSteps="{steps}">'
            f'<Param1 value="undefined" start="{oos["start"]}" stop="{oos["stop"]}" '
            f'step="{oos["step"]}" />'
            f'<Param2 value="undefined" start="{runs["start"]}" stop="{runs["stop"]}" '
            f'step="{runs["step"]}" /></WalkForward>'), steps


def settings(block: str, cfg: dict) -> tuple[str, dict]:
    """Write the grid, the ceiling on each step's optimisation, and how a cell is judged.

    Args:
        block: The <WalkForwardMatrix> element.
        cfg: The `wfm` block of _build.yaml.

    Returns:
        The element and what was written. `MaxTests` caps how many parameter sets each step
        tries; only the winner survives into the stored period, so raising it buys a better
        pick per step and nothing readable afterwards (knowhow/sqx-format/wfm-in-settings-xml.md).
    """
    rows, cols = grid(cfg)
    element, steps = axes(cfg)
    found = re.search(r"<WalkForward\b.*?</WalkForward>", block, re.S)
    block = block[:found.start()] + element + block[found.end():]
    block = re.sub(r"<MaxTests>\d+</MaxTests>", f"<MaxTests>{cfg['max_tests']}</MaxTests>",
                   block, count=1)
    size = cfg["grid_passing_size"]
    block = acceptance(recommended(block), cfg["conditions"],
                       area(rows, cols, size, cfg["min_squares"], cfg["threshold_pct"]),
                       "WalkForwardMatrix")
    return block, {"cells": rows * cols, "rows": rows, "columns": cols, "steps": steps,
                   "wf_type": cfg["wf_type"],
                   "conditions": len(cfg["conditions"]),
                   "threshold_pct": cfg["threshold_pct"], "area": f"{size}x{size}",
                   "min_squares": cfg["min_squares"],
                   "positions": (rows - size + 1) * (cols - size + 1)}


def write_task(text: str, cfg: dict, data: dict) -> tuple[str, dict]:
    """Turn one Retest task into the walk-forward matrix task the catalogue describes.

    Args:
        text: A task XML.
        cfg: The `wfm` block of _build.yaml.
        data: One asset as load() returned it.

    Returns:
        The task and what was written.
    """
    # `build..oos2` is one continuous window from the first segment's start to the last
    # one's end, and the reason a walk-forward gets history in front of the reserved tail:
    # the first pass has to optimise on something before it can run on anything. Unlike the
    # spans of the MC Retest it is NOT priced at its last segment: `costs_segment` says at
    # whose costs, because eighteen years charged at the four-year tail's spread would be a
    # price nobody trades at (owner, 2026-09-24). So costs come from one segment and the
    # window from another, and the two Setup dates are written over what pricing left.
    names = cfg["segment"].split("..")
    text, setups = set_costs(text, data, cfg["costs_segment"])
    start, end = bounds(data, names[0])[0], bounds(data, names[-1])[1]
    priced = bounds(data, cfg["costs_segment"])
    text = text.replace(f'dateFrom="{priced[0]}"', f'dateFrom="{start}"')
    text = text.replace(f'dateTo="{priced[1]}"', f'dateTo="{end}"')
    text, _ = set_data_range(text, data, (window(data, names[0])[0],
                                          window(data, names[-1])[1]))
    text = set_precision(text, cfg["precision"])
    # The donor's own judgement goes first and the catalogue's is written after: `silence`
    # turns off every active condition of the WHOLE task, this one's included, so writing
    # them in the other order would leave the matrix judging by nothing and passing
    # everything at 100 % (`computeRobustnessScore`, decompiled 2026-09-24).
    text, silenced = silence(enable(text, "WalkForwardMatrix"))
    found = BLOCK.search(text)
    block, written = settings(found.group(0), cfg)
    text = text[:found.start()] + block + text[found.end():]
    return text, {"segment": cfg["segment"], "from": start, "to": end,
                  "priced_at": cfg["costs_segment"], "spread": sqx_settings(
                      data, cfg["costs_segment"])["defaultSpread"],
                  "precision": cfg["precision"], "setups": setups, "silenced": silenced,
                  "others_on": others_on(text, "WalkForwardMatrix"), **written}


def configure(cfx: Path, symbol: str, source: str) -> dict:
    """Write the WFM task of one project, on the window policy reserves for it.

    Args:
        cfx: Path of a project.cfx. Must not be held by a running install.
        symbol: Asset name, e.g. "XAUUSD".
        source: The databank it reads — the survivors that reached step 19.

    Returns:
        What was written, and the project name.

    Raises:
        SystemExit: The project has no task with the catalogue's title. A project cloned
            without the donor's WFM task cannot grow one here: the element and its
            conditions come from a task SQX itself wrote.
    """
    data = load(symbol)
    cfg = doctrine()["wfm"]
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    config = members["config.xml"].decode("utf-8")
    member = member_of(config, cfg["title"])
    if not member:
        raise SystemExit(f"el proyecto no lleva la tarea {cfg['title']}. Clonalo del donante "
                         "con --tasks Retest y el --only que la incluya.")

    text, done = write_task(members[member].decode("utf-8"), cfg, data)
    text, _ = set_databank(text, "Input", source)
    text, _ = set_databank(text, "Output", cfg["title"])
    members[member] = text.encode("utf-8")
    members["config.xml"] = active(config, cfg["title"], True).encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    return {"project": ElementTree.fromstring(config).get("name"), "title": cfg["title"],
            "member": member, "reads": source, "writes": cfg["title"],
            "reserved_for": policy()["segments_default"][cfg["segment"].split("..")[-1]]
                            .get("reserved_for"),
            "max_tests": cfg["max_tests"], **done}


def main() -> None:
    """Configure a project's WFM task, refusing on anything undecided."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol")
    ap.add_argument("--cfx", required=True, type=Path)
    ap.add_argument("--input", required=True,
                    help="databank que lee. No se adivina: son los supervivientes que han "
                         "llegado hasta el paso 19")
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
    print(f"{done['project']}  {a.symbol}  {done['reads']} → {done['writes']}")
    print(f"  ✓ {done['title']:<4} {done['segment']} {done['from']}→{done['to']}  "
          f"{done['cells']} celdas ({done['rows']} pasadas x {done['columns']} % OOS), "
          f"tope {done['max_tests']} tests por paso, {done['steps']} pasos de parametro, "
          f"precision {done['precision']}")
    print(f"      cobrada al tramo {done['priced_at']}: spread {done['spread']} — NO al "
          "ultimo tramo de la ventana, que es lo que hacen los demas spans")
    print(f"      fidelidad \"{WF_TYPES[done['wf_type']][1]}\" — {done['max_tests']} tests "
          f"por paso x {done['cells']} celdas, y cada paso es una optimizacion propia")
    print(f"      {done['silenced']} condicion(es) del donante apagadas y "
          f"{done['conditions']} propias escritas: una casilla aprueba con "
          f"{done['threshold_pct']} % de ellas cumplidas")
    if done["min_squares"]:
        print(f"      la estrategia pasa si encuentra {done['min_squares']} casillas "
              f"aprobadas en un area de {done['area']} — {done['positions']} posiciones "
              "posibles. ⚠️ ESTO FILTRA: SQX descarta a quien no lo encuentre y no lo "
              "escribe en el databank de salida")
    else:
        print("      min_squares 0 — modo mapa: puntua cada casilla y no descarta a nadie")
    if done["others_on"]:
        print(f"      ⚠️ esta tarea corre ademas: {', '.join(done['others_on'])} — el "
              "proyecto no paso por la doctrina")
    print(f"\n⚠️ {done['segment']} acaba en un tramo RESERVADO para "
          f"{', '.join(done['reserved_for'] or [])}: cada mirada lo gasta y no se repite.")
    print("⚠️ Y no se LEE hasta que 17, 18 y 19 esten los tres hechos. Mirar el WFC antes "
          "de decidir si se corre esto contamina la decision con lo ya visto.")


if __name__ == "__main__":
    main()
