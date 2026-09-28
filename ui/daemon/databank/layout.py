"""The databank panel's two rows of tabs for one project: each sub-panel and its databank."""

from core import cfx
from core.paths import DATA
from engines.variants import look
from sqx.projects.stage import titles
from ui.daemon.databank import table
from ui.daemon.workflow import sources

# The top row as the mock fixed it (encargo 22 §4.3, kept by the owner after wave 1), each tab
# with the workflow stage whose task writes its databank and its sub-panels: (name, studies,
# stage of its databank — '' for the build's —, `split` from the data or None). A study key
# of `*` shows every study's verdict beside the metrics.
TABS = [
    ("Puerta IS/OOS", [("Build + OOS1", ["*"], "", None),
                       ("Cribas", ["gate", "decay", "snoopingScreen", "edgeCost",
                                   "feedQuality", "monkeyExcess"], "", None),
                       ("Spread real", ["spread"], "", None)]),
    ("Cross Market", [("Resumen", ["crossmarket"], "crossmarket", "crossmarket")]),
    ("Cross Timeframe", [("Resumen", ["crossTF"], "crosstf", "crossTF")]),
    ("MC Retest", [("Resumen", ["mcRetest"], "mcretest", "mcRetest")]),
    ("SPP", [("IS", ["spp"], "spp", None), ("OOS", ["spp"], "spp.1", None)]),
    ("WFM", [("Matriz", ["wfm"], "wfm", None)]),
    ("WFC", [("", ["wfc"], "", "wfc"), ("Nube de parámetros", ["cloud"], "", None)]),
    ("CSCV", [("PBO", ["cscv"], "", None)]),
    ("Market Surfaces", [("Superficies", ["marketSurfaces"], "", None)]),
    ("Cierre", [("Análisis conjunto (paso 20)", ["blindJoint"], "", None),
                ("Exposición", ["exposure"], "", None),
                ("Mapa condicional", ["conditionalMap"], "", None),
                ("Estructura", ["structure"], "", None), ("Stop ATR", ["atrCalculator"], "", None),
                ("Edge por coste", ["edgeCost"], "", None)]),
]
# The sub-panels of step 20 and of the three it waits for, locked while the ledger's door is.
LOCKED = {"blindJoint", "wfc", "cscv", "wfm"}
SEGMENT = {"build": "Build", "oos1": "OOS1", "oos2": "OOS2"}


def outputs(project: str) -> dict[str, str]:
    """The databank each workflow stage writes, read off the project's `project.cfx`.

    Returns:
        Task title → output databank; {} when no install holds the project any more.
    """
    where = sources.install(project)
    if where is None:
        return {}
    path = str(where[1] / "user" / "projects" / project / "project.cfx")
    out = {}
    for t in cfx.tasks(path):       # a donor's ClearDatabanks or GoToTask writes no databank
        io = {d.get("name"): d.get("value") for d in cfx.task_xml(path, t["file"]).iter("Databank")}
        if io.get("Output"):
            out[t["title"]] = io["Output"]
    return out


def reported(project: str, study: str) -> str | None:
    """The databank folder whose newest report holds this study, or None."""
    found = sorted((DATA / "reports" / project).glob(f"*/*/{study}"),
                   key=lambda p: p.parent.name)
    return found[-1].parent.parent.name if found else None


def databank(project: str, out: dict, stage: str, studies: list[str]) -> str:
    """Where a sub-panel reads: the databank its study reported on, else the one its stage's
    task writes, else the build's. `spp.1` is the stage's second task (SPP OOS)."""
    own = reported(project, studies[0]) if studies != ["*"] and stage != "spp.1" else None
    if own:
        return own
    name, _, nth = stage.partition(".")
    wanted = titles(name)[int(nth or 0)] if name else titles("build")[0]
    return out.get(wanted) or out.get(titles("build")[0]) or \
        reported(project, "gate") or "Results"


def splits(project: str, bank: str, study: str) -> list[str]:
    """The sub-panels a study's own data names: its tasks, markets or timeframes."""
    got = table.table(project, bank)
    return list(dict.fromkeys(c["sub"] for c in got["columns"]
                              if c.get("study") == study and c["sub"]))


def composition(label: str) -> str:
    """`build+oos1__oos2` as the owner reads it: «IS Build + OOS1 → OOS OOS2»."""
    inside, outside = (" + ".join(SEGMENT[s] for s in part.split("+"))
                       for part in label.split("__"))
    return f"IS {inside} → OOS {outside}"


def panels(project: str) -> dict:
    """GET /api/databank/panels: the two tab rows of one project.

    Args:
        project: Project name.

    Returns:
        `tabs` [{tab, subs: [{sub, databank, studies, split, blocked}]}] — `split` the
        sub-key its columns carry (a task, market, timeframe or WFC composition), `blocked`
        the ledger's sentence while the door holds that sub-panel — and `blind`.
    """
    blind, asset = table.door(project)
    out = outputs(project)
    tabs = []
    for tab, specs in TABS:
        subs = []
        for name, studies, stage, split in specs:
            bank = databank(project, out, stage, studies)
            locked = blind["text"] if blind["sealed"] and LOCKED & set(studies) else None
            row = {"sub": name, "databank": bank, "studies": studies, "split": None,
                   "blocked": locked}
            if split == "wfc":
                subs += [{**row, "sub": composition(c), "split": c}
                         for c in (look.offered(asset) if asset else [])]
                continue
            subs.append(row)
            if split and not locked:
                subs += [{**row, "sub": s, "split": s} for s in splits(project, bank, split)]
        tabs.append({"tab": tab, "subs": subs})
    return {"project": project, "tabs": tabs, "blind": blind}
