"""The population's funnel of one project: the gate's screens, then each later step's in and out."""

import pandas as pd

from ui.daemon.databank.layout import reported
from ui.daemon.gateview import screens
from ui.daemon.results import store
from ui.daemon.workflow.api import workflow

# A step whose count is not read yet, in the owner's words.
WAITING = {"sealed": "sellado", "running": "corriendo", "blocked": "bloqueado"}


def gate_rows(project: str) -> tuple[list[dict], str]:
    """The newest gate report's `funnel.csv`, one row per screen, with the screen's why.

    Returns:
        (rows, the databank and day it came from, or ''). A soft screen marks and removes
        nobody: it passes what entered it.
    """
    bank = reported(project, "gate")
    if bank is None:
        return [], ""
    day = store.days(project, bank, "gate")[0]
    why = {s["name"]: s["why"] for s in screens()}
    rows = []
    table = pd.read_csv(store.bank(project, bank) / day / "gate" / "funnel.csv")
    for r in table.to_dict("records"):
        soft = r["kind"] == "soft"
        rows.append({"screen": r["screen"], "kind": r["kind"], "entered": int(r["entered"]),
                     "passed": int(r["entered"] if soft else r["passed"]),
                     "died": 0 if soft else int(r["died"]), "state": "hecho",
                     "why": ("blanda: marca y no elimina · " if soft else "")
                     + why.get(r["screen"], "")})
    return rows, f"{bank} del {day}"


def funnel(project: str) -> dict:
    """GET /api/databank/funnel: what entered each screen and step, what passed, and why.

    Args:
        project: Project name.

    Returns:
        `rows` [{screen, kind, entered, passed, died, state, why}] — the build's population
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
