#!/usr/bin/env python3
"""Write the Build task's acceptance filters — its «Ranking» conditions — from assets/_study.yaml."""

import argparse
import re
from pathlib import Path

from core.assetcheck import pending
from core.assetdata import load
from core.buildfilters import MODES, STUDY, Condition, Filters, filters
from sqx.projects import cfxio
from sqx.projects import buildrules as rules
from sqx.projects.acceptance import CONDITIONS, condition
from sqx.projects.crosschecks import MC_MANIPULATION
from typing import Any

RANKINGS = re.compile(r"<Rankings\b.*?</Rankings>", re.S)


def set_rankings(text: str, specs: list[Condition]) -> str:
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
    assert found is not None
    block = found.group(0)
    old = CONDITIONS.search(block)
    written = "".join(condition(spec, "main") for spec in specs)
    assert old is not None
    block = block[:old.start()] + f"<Conditions>{written}</Conditions>" + block[old.end():]
    return text[:found.start()] + block + text[found.end():]


def describe(written: Filters) -> str:
    """One line a human and the registry can read: the mode, the sample and each condition."""
    return (f"{written['mode']} @{written['sample']}: "
            + " & ".join(f"{c['metric']} {c['op']} {c['value']}" for c in written["conditions"]))


class Written(Filters):
    """What `apply` returns: the filters written and the task members they went into."""

    tasks: list[str]


def apply(cfx: Path, symbol: str, timeframe: str, mode: str = "study",
          study: Path = STUDY) -> Written:
    """Write one asset's filters into every Build task of a project.cfx no install holds.

    Args:
        cfx: Path of the project.cfx.
        symbol: Asset name, e.g. "XAUUSD".
        timeframe: SQX timeframe name — the trade bounds are per year and per timeframe.
        mode: "study" or "calibration".
        study: The thresholds file.

    Returns:
        What `filters` resolved, plus `tasks`, the members written — none, and no conditions,
        when the project has no Build task.
    """
    members = cfxio.members(cfx)
    tasks = [n for n, blob in members.items() if n.endswith(".xml") and n != "config.xml"
             and rules.BLOCKS.search(blob.decode("utf-8"))]
    # A project with no Build task (a study's retest on its own) has nothing to filter by.
    written: Filters = (filters(load(symbol), timeframe, mode, study) if tasks else
               {"mode": "none", "sample": "-", "build_years": 0, "conditions": []})
    for name in tasks:
        text = set_rankings(members[name].decode("utf-8"), written["conditions"])
        members[name] = text.encode("utf-8")
    cfxio.write(cfx, members)
    return {**written, "tasks": tasks}


def mc_off(cfx: Path) -> int:
    """Switch MonteCarloManipulation off in every task of a project.cfx no install holds.

    Returns:
        How many tasks changed. Only the `use=` attribute moves; the member list is untouched.
    """
    held = cfxio.held(cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al salir. "
                         f"Párala: bin/sqx-worker.sh --role {held} stop")
    members = cfxio.members(cfx)
    changed = 0
    for name, blob in members.items():
        if name.endswith(".xml") and name != "config.xml":
            text = blob.decode("utf-8")
            new = MC_MANIPULATION.sub(r'\g<1>use="false"', text)
            if new != text:
                members[name] = new.encode("utf-8")
                changed += 1
    if changed:
        cfxio.write(cfx, members)
    return changed


def main() -> None:
    """Rewrite the acceptance filters of an existing, stopped project."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cfx", type=Path)
    ap.add_argument("symbol", nargs="?")
    ap.add_argument("--timeframe")
    ap.add_argument("--mc-off", action="store_true",
                    help="only switch MonteCarloManipulation off in every task (no symbol needed)")
    ap.add_argument("--acceptance", choices=MODES, default="study")
    ap.add_argument("--study-file", type=Path, default=STUDY,
                    help="another thresholds file, for an A/B of filters")
    a = ap.parse_args()
    if a.mc_off:
        print(f"{a.cfx}: MonteCarloManipulation apagado en {mc_off(a.cfx)} tareas")
        return
    if not (a.symbol and a.timeframe):
        raise SystemExit("faltan symbol y --timeframe (o usa --mc-off)")
    held = cfxio.held(a.cfx)
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
