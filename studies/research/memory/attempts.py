"""The attempts table: one row per project run of a template on an asset, timeframe and direction."""

import re
from pathlib import Path

from studies.research.memory import sources
from studies.research.memory.sources import CONFIG

STAGES = CONFIG["stages"]
COLUMNS = ["project", "template", "family", "archetype", "symbol", "timeframe", "direction",
           "asset_class", "idea", "date", "custodian_hours", "runs", *STAGES, "crosstf_cells",
           "last_stage", "died_at", "survivors", "dev_cut", "failed_at", "outcome", "verdict",
           "source"]
NAME = re.compile(r"^(?:Test|Trade)_([A-Z0-9]+)_.*_(M15|M30|H1|H4|D1)$")
DIRECTION = {"market_long": "long", "market_short": "short"}


def funnel(stages: dict, failed: str) -> dict:
    """Where a population stopped.

    Args:
        stages: {stage: strategies left} as the resumen counted them.
        failed: Step the newest run failed at, '' when it did not.

    Returns:
        `last_stage`, `died_at` (the first stage that left none, '' if none did), `survivors`
        (what the last stage holds when that stage is the final one, else ''), `outcome`:
        failed@<step> (inconclusive: a failed run is not a verdict), died@<stage>,
        survivors, incomplete@<stage> or unknown. A zero after a failure is not a death:
        the task may simply not have run.
    """
    seen = [s for s in STAGES if s in stages]
    died = next((s for s, prev in zip(seen, [None, *seen]) if stages[s] == 0
                 and (prev is None or stages[prev] > 0)), "")
    last = seen[-1] if seen else ""
    final = last == STAGES[-1] and stages[last] > 0
    outcome = ("failed@" + failed if failed else f"died@{died}" if died else
               "survivors" if final else f"incomplete@{last}" if last else "unknown")
    return {"last_stage": last, "died_at": "" if failed else died,
            "survivors": 0 if died and not failed else stages[last] if final else "",
            "outcome": outcome}


def one(project: str, reg: dict, runs: dict, tpl: dict, ideas: set, root: Path | None = None) -> dict:
    """The row of one project from every source that knows it; what none knows stays ''."""
    name = sources.template_of(reg) or runs.get("template", "")
    parts = NAME.match(project)
    pilot = sources.autopilot_project(project, root)
    info = tpl.get(name, {})
    symbol = reg.get("symbol") or runs.get("symbol") or (parts[1] if parts else "")
    stages = dict(pilot["stages"])
    if not stages and runs.get("strategies_built"):
        stages["built"] = int(runs["strategies_built"])
    row = {c: "" for c in COLUMNS}
    row |= {"project": project, "template": name, "archetype": info.get("archetype", ""),
            "family": CONFIG["archetype_family"].get(info.get("archetype", ""), ""),
            "symbol": symbol, "timeframe": reg.get("timeframe") or runs.get("timeframe")
            or (parts[2] if parts else ""), "direction": DIRECTION.get(info.get("shape"), ""),
            "asset_class": CONFIG["asset_class"].get(symbol, ""),
            "idea": name if name in ideas else "",
            "date": (reg.get("created") or runs.get("date") or pilot["first"])[:10],
            "custodian_hours": round(pilot["minutes"] / 60, 2) if pilot["runs"] else "",
            "runs": pilot["runs"], "crosstf_cells": pilot["crosstf"] if pilot["runs"] else "",
            "dev_cut": "yes" if pilot["dev_cut"] else "", "failed_at": pilot["failed"],
            "verdict": runs.get("verdict", ""),
            "source": "+".join(s for s, on in (("projects", reg), ("runs.csv", runs),
                                               ("autopilot", pilot["runs"])) if on)}
    row |= {s: stages.get(s, "") for s in STAGES}
    return row | funnel(stages if pilot["runs"] else {}, pilot["failed"])


def table(ideas: set = frozenset()) -> list[dict]:
    """Every attempt known today, oldest first.

    Args:
        ideas: Names of the ideas in the ideas index; a template of the same name links to it.

    Returns:
        One dict per project that has a library template (registry) or a runs.csv row or an
        autopilot folder. Projects of other kinds (MT5 verification, hand-made) carry no
        template and are left out.
    """
    reg, runs, tpl = sources.registry_projects(), sources.runs_by_project(), sources.templates()
    folders = {p.name for p in sources.autopilot_runs().glob("*") if p.is_dir()}
    names = {n for n, r in reg.items() if sources.template_of(r)} | set(runs) | folders
    rows = [one(n, reg.get(n, {}), runs.get(n, {}), tpl, ideas) for n in names]
    return sorted(rows, key=lambda r: (r["date"], r["project"]))
