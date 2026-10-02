"""The databank panel's two rows of tabs for one project: each sub-panel and its databank."""

from core import cfx
from core.paths import DATA
from sqx.projects.stage import titles
from ui.daemon.databank import cells, metrics, table
from ui.daemon.workflow import sources

# The top row as the mock fixed it (encargo 22 §4.3, kept by the owner after wave 1), each tab
# with the workflow stage whose task writes its databank and its sub-panels: (name, studies,
# stage of its databank — '' for the build's —, `split` from the data or None). A study key
# of `*` shows every study's verdict beside the metrics.
TABS = [
    # One summary per databank (owner, 2026-10-01): the gate's screens, the real spread and
    # each market are read in the strategy view, not as sub-panels of the databank.
    ("Puerta IS/OOS", [("Resumen", ["*"], "", None)]),
    ("Cross Market", [("Resumen", ["crossmarket"], "crossmarket", None)]),
    ("Cross Timeframe", [("Resumen", ["crossTF"], "crosstf", "crossTF")]),
    ("MC Retest", [("Resumen", ["mcRetest"], "mcretest", None)]),   # tasks: strategy view
    ("SPP", [("IS", ["spp"], "spp", None), ("OOS", ["spp"], "spp.1", None)]),
    # One virtual databank for the whole optimisation stage (owner, 2026-09-30 §2/§8): WFM,
    # WFC, CSCV and Market Surfaces never touch on disk — this groups their tabs in the
    # window only, in the order the owner reads them, Walk Forward Matrix last. cloud, wfc,
    # cscv and marketSurfaces all judge the SAME batch of mothers (the WFC task's own small
    # databank, not the full build): stage "wfc" for all four so `databank()` picks that one
    # instead of falling through to the build's ~300-row roster (H's audit, 2026-09-30).
    # Not the WFC task's own databank, though: `WFC_Build` holds the VARIANTS (S00V000…),
    # never a mother, so every row read unjudged (🔬 2026-10-01). Stage "mothers" picks the
    # smallest databank that holds every mother (`mothers_bank`).
    ("WFM + WFC + CSCV + Market Surfaces", [
        ("Nube de parámetros", ["cloud"], "mothers", None),
        ("WFC", ["wfc"], "mothers", None),
        ("CSCV", ["cscv"], "mothers", None),
        ("Market Surfaces", ["marketSurfaces"], "mothers", None),
        ("Walk Forward Matrix", ["wfm"], "wfm", None)]),
    ("Cierre", [("Análisis conjunto (paso 20)", ["blindJoint"], "", None),
                ("Exposición", ["exposure"], "", None),
                ("Mapa condicional", ["conditionalMap"], "", None),
                ("Estructura", ["structure"], "", None), ("Stop ATR", ["atrCalculator"], "", None),
                ("Edge por coste", ["edgeCost"], "", None)]),
]
# The sub-panels of step 20 and of the three it waits for, locked while the ledger's door is.
LOCKED = {"blindJoint", "wfc", "cscv", "wfm"}


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


def known(project: str, title: str) -> str | None:
    """A databank the data root holds under this task title, for a project no install holds
    any more (its `project.cfx` gone, `outputs` empty): its reports, metrics or raw export."""
    folder = title.replace(" ", "_")
    for root in ("reports", "metrics", "raw"):
        if (DATA / root / project / folder).is_dir():
            return folder
    return None


def mothers_bank(project: str, out: dict) -> str | None:
    """The smallest databank that holds every mother with a variant batch — where the batch
    studies (cloud, wfc, cscv, marketSurfaces) have a row per mother and nothing else.

    Args:
        project: Project name.
        out: What `outputs` read.

    Returns:
        The databank covering the most mothers, the smallest roster breaking ties; None
        when the project has no batch or no databank names any of its mothers.
    """
    # Imported here: batches → cells → results.catalogue → runner → readings → this module.
    from ui.daemon.databank import batches
    wanted = set(batches.mothers(project))
    if not wanted:
        return None
    # The stages the mothers come out of, read first: an MC Retest task's databank can hold
    # every mother too, but its metrics are a perturbed retest, not the strategy's own.
    near = [t for t in titles("wfm") + titles("spp")[::-1]]
    near = list(dict.fromkeys(b for t in near for b in (out.get(t), known(project, t)) if b))
    rest = sorted(set(out.values()) | {p.name for root in ("reports", "metrics")
                                       for p in (DATA / root / project).glob("*")
                                       if p.is_dir()})
    for names in (near, rest):
        best = None
        for name in names:
            frame = metrics.source(project, name)[1]
            if frame is None:
                continue
            held = {cells.norm(n) for n in (frame["name"] if "name" in frame else frame.index)}
            score = (len(wanted & held), -len(held))
            if score[0] and (best is None or score > best[0]):
                best = (score, name)
        if best:
            return best[1]
    return None


def databank(project: str, out: dict, stage: str, studies: list[str]) -> str:
    """Where a sub-panel reads: the databank its study reported on, else the one its stage's
    task writes, else the build's. `spp.1` is the stage's second task (SPP OOS).

    SPP IS and SPP OOS both write a `spp` report, so `reported` — which only breaks ties by
    day, not by which of the two folders — can answer either sub with the SAME databank once
    both reported the same day (🔬 2026-09-30, H's audit). Both SPP subs skip it and go
    straight to `out`, project.cfx's own IS/OOS split.
    """
    if stage == "mothers":
        own = mothers_bank(project, out)
        if own:
            return own
        stage = "wfc"
    own = (reported(project, studies[0])
          if studies != ["*"] and stage not in ("spp", "spp.1") else None)
    if own:
        return own
    name, _, nth = stage.partition(".")
    wanted = titles(name)[int(nth or 0)] if name else titles("build")[0]
    return out.get(wanted) or known(project, wanted) or out.get(titles("build")[0]) or \
        reported(project, "gate") or "Results"


def splits(project: str, bank: str, study: str) -> list[str]:
    """The sub-panels a study's own data names: its tasks, markets or timeframes; none when
    that databank cannot be read. Its own sub-panel says why when opened: one unreadable
    databank (an empty export, 2026-09-29) used to fail the whole tab list, and the window
    stayed on it with no tabs to leave by."""
    try:
        got = table.table(project, bank)
    except Exception:  # noqa: BLE001 — the ui boundary: the tab row must always come back
        return []
    return list(dict.fromkeys(c["sub"] for c in got["columns"]
                              if c.get("study") == study and c["sub"]))


def panels(project: str) -> dict:
    """GET /api/databank/panels: the two tab rows of one project.

    Args:
        project: Project name.

    Returns:
        `tabs` [{tab, subs: [{sub, databank, studies, split, blocked}]}] — `split` the
        sub-key its columns carry (a Cross TF timeframe), `blocked`
        the ledger's sentence while the door holds that sub-panel — and `blind`.
    """
    blind, _ = table.door(project)
    out = outputs(project)
    tabs = []
    for tab, specs in TABS:
        subs = []
        for name, studies, stage, split in specs:
            bank = databank(project, out, stage, studies)
            locked = blind["text"] if blind["sealed"] and LOCKED & set(studies) else None
            row = {"sub": name, "databank": bank, "studies": studies, "split": None,
                   "blocked": locked}
            subs.append(row)
            if split and not locked:
                subs += [{**row, "sub": s, "split": s} for s in splits(project, bank, split)]
        tabs.append({"tab": tab, "subs": subs})
    return {"project": project, "tabs": tabs, "blind": blind}
