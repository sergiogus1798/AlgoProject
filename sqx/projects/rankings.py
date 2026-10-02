#!/usr/bin/env python3
"""Write the Build task's acceptance filters — its «Ranking» conditions — from assets/_study.yaml."""

import argparse
import re
import zipfile
from pathlib import Path

from core.assetcheck import pending
from core.assetdata import load
from core.buildfilters import MODES, STUDY, filters
from sqx.projects import buildrules as rules
from sqx.projects.acceptance import CONDITIONS, condition
from sqx.projects.configure import running_install

RANKINGS = re.compile(r"<Rankings\b.*?</Rankings>", re.S)
MC_MANIPULATION = re.compile(r'(<MonteCarloManipulation )use="true"')


def set_rankings(text: str, specs: list[dict]) -> str:
    """Replace the conditions of a Build task's `<Rankings>` — all of them — with these.

    Args:
        text: A Build task XML.
        specs: The conditions, as `core.buildfilters.filters` returns them.

    Returns:
        The task with the donor's conditions gone and these in their place, active. The search
        is scoped to `<Rankings>`: the first `<Conditions>` of a Build task is the initial
        population's, under `<BuildMode>`, and that one is not an acceptance filter.
    """
    found = RANKINGS.search(text)
    block = found.group(0)
    old = CONDITIONS.search(block)
    written = "".join(condition(spec, "main") for spec in specs)
    block = block[:old.start()] + f"<Conditions>{written}</Conditions>" + block[old.end():]
    return text[:found.start()] + block + text[found.end():]


def describe(written: dict) -> str:
    """One line a human and the registry can read: the mode, the sample and each condition."""
    return (f"{written['mode']} @{written['sample']}: "
            + " & ".join(f"{c['metric']} {c['op']} {c['value']}" for c in written["conditions"]))


def apply(cfx: Path, symbol: str, timeframe: str, mode: str = "study",
          study: Path = STUDY) -> dict:
    """Write one asset's filters into every Build task of a project.cfx no install holds.

    Args:
        cfx: Path of the project.cfx.
        symbol: Asset name, e.g. "XAUUSD".
        timeframe: SQX timeframe name — the trade bounds are per year and per timeframe.
        mode: "study" or "calibration" (which also switches the build's MonteCarloManipulation
            cross-check off: its conditions are off, so it only costs CPU).
        study: The thresholds file.

    Returns:
        What `filters` resolved, plus `tasks`, the members written — none, and no conditions,
        when the project has no Build task.
    """
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    tasks = [n for n, blob in members.items() if n.endswith(".xml") and n != "config.xml"
             and rules.BLOCKS.search(blob.decode("utf-8"))]
    # A project with no Build task (a study's retest on its own) has nothing to filter by.
    written = (filters(load(symbol), timeframe, mode, study) if tasks else
               {"mode": "none", "sample": "-", "build_years": 0, "conditions": []})
    for name in tasks:
        text = set_rankings(members[name].decode("utf-8"), written["conditions"])
        if mode == "calibration":
            text = MC_MANIPULATION.sub(r'\g<1>use="false"', text)
        members[name] = text.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    return {**written, "tasks": tasks}


def main() -> None:
    """Rewrite the acceptance filters of an existing, stopped project."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cfx", type=Path)
    ap.add_argument("symbol")
    ap.add_argument("--timeframe", required=True)
    ap.add_argument("--acceptance", choices=MODES, default="study")
    ap.add_argument("--study-file", type=Path, default=STUDY,
                    help="another thresholds file, for an A/B of filters")
    a = ap.parse_args()
    held = running_install(a.cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al salir. "
                         f"Párala: bin/sqx-worker.sh --role {held} stop")
    missing = pending(load(a.symbol))
    if missing:
        raise SystemExit(f"{a.symbol}: {', '.join(missing)} sin valor pactado. "
                         "Pregúntale al dueño antes de configurar nada.")
    written = apply(a.cfx, a.symbol, a.timeframe, a.acceptance, a.study_file)
    print(f"{a.cfx}: {', '.join(written['tasks'])}\n  aceptación  {describe(written)}"
          f"  (build {written['build_years']} años)")


if __name__ == "__main__":
    main()
