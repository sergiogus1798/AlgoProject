"""The population's funnel of one project: the gate's rules by level, then each later step's in and out."""

import pandas as pd

from ui.daemon.databank.layout import reported
from ui.daemon.results import store
from ui.daemon.workflow.api import workflow

# A step whose count is not read yet, in the owner's words.
WAITING = {"sealed": "sellado", "running": "corriendo", "blocked": "bloqueado"}


def gate_rows(project: str) -> tuple[list[dict], str]:
    """The newest gate report's `funnel.csv`, one row per rule (`screen` holds its label, `level` the level that judged it).

    Returns:
        (rows, the databank and day it came from, or ''). `passed` already counts Limbo as
        standing: only Fail removes anybody.
    """
    bank = reported(project, "gate")
    if bank is None:
        return [], ""
    day = store.days(project, bank, "gate")[0]
    rows = []
    table = pd.read_csv(store.bank(project, bank) / day / "gate" / "funnel.csv")
    for r in table.to_dict("records"):
        limbo = int(r.get("limbo", 0))
        # a report written before encargo 44 has no `level`: its rows are the old screens
        rows.append({"level": str(r["level"]) if pd.notna(r.get("level")) else "", "screen": r["screen"], "kind": r["kind"],
                     "entered": int(r["entered"]), "limbo": limbo, "passed": int(r["passed"]),
                     "died": int(r["died"]), "state": "hecho",
                     "why": f"nivel {r['level']}: {limbo} en Limbo, siguen" if limbo and r.get("level")
                     else f"nivel {r['level']}" if r.get("level") else ""})
    return rows, f"{bank} del {day}"


def funnel(project: str) -> dict:
    """GET /api/databank/funnel: what entered each screen and step, what passed, and why.

    Args:
        project: Project name.

    Returns:
        `rows` [{level, screen, kind, entered, limbo, passed, died, state, why}] — the build's population
        first, the gate's screens, then every later Python step `/api/workflow` counted, in
        workflow order — and `source`. A step sealed by the ledger's door or still running
        has `entered` None: its count is not read before its time. Later steps read their
        own databank, so their population is theirs, not what the previous row left.
    """
    rows, source = gate_rows(project)
    if rows:
        rows.insert(0, {"screen": "Build", "kind": "build", "entered": rows[0]["entered"],
                        "passed": rows[0]["entered"], "died": 0, "state": "hecho",
                        "why": "la población del build que el gate juzgó"})
    for step in workflow(project)["steps"]:
        if step["kind"] != "python" or float(step["n"]) <= 8:
            continue
        if step["state"] == "done" and step["in"] is not None:
            rows.append({"screen": step["title"], "kind": "step", "entered": step["in"],
                         "passed": step["out"], "died": step["in"] - step["out"],
                         "state": "hecho", "why": step["why"]})
        elif step["state"] in WAITING:
            rows.append({"screen": step["title"], "kind": "step", "entered": None,
                         "passed": None, "died": None, "state": WAITING[step["state"]],
                         "why": step["why"]})
    return {"project": project, "rows": rows, "source": source}
