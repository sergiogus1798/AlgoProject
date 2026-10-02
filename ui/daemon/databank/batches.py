"""The studies that write into a mother's variant batch: cloud, wfc (and its compositions),
cscv, marketSurfaces."""

from collections import defaultdict
from pathlib import Path

from core.datapaths import variants_dir
from pipeline.ledger.state import work_dir
from ui.daemon.databank.cells import norm
from ui.daemon.results import store

# marketSurfaces was missing here until 2026-09-30 (FEEDBACK §8.5): its report writes
# `estudios/marketSurfaces.json` beside cloud/wfc/cscv, but `/api/result` looked for it under
# `reports/<P>/<D>/`, where it never lands — the run finished, the databank never got it.
STUDIES = ("cloud", "wfc", "cscv", "marketSurfaces")


def batches(project: str) -> dict[str, list[Path]]:
    """Every batch folder of a project that holds studies, by the mother's name.

    Args:
        project: Project name.

    Returns:
        norm name → the folders found, from the factory and from the pipeline. Two of them
        is a mother the window will not choose for the owner, as `runner/where.batch` says.
    """
    found = defaultdict(list)
    for root in (variants_dir(project, "x").parent, work_dir(project, "x").parent):
        for folder in sorted(root.glob("*/estudios")) if root.is_dir() else []:
            found[norm(folder.parent.name)].append(folder.parent)
    return found


def summary(got: dict) -> dict[tuple[str, str], object]:
    """The flat part of a result's `summary`: numbers and words, lists joined, dicts left out."""
    out = {}
    for key, value in (got.get("summary") or {}).items():
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        if not isinstance(value, dict):
            out[("", key)] = value
    return out


def entry(path: Path) -> dict | None:
    """One batch study result as a table entry, or None when it is not a contract result.

    Cached by the file's version: `marketSurfaces` and `cloud` JSONs run to megabytes, and
    every databank table read ~230 of them afresh — 2.8 s per call, three calls per tab list,
    past the window's 20-s timeout («El demonio no responde», 🔬 2026-10-01).

    Args:
        path: `estudios/<study>.json` or `estudios/wfc_<composition>.json`.
    """
    return store.cached(path, _entry)


def _entry(path: Path) -> dict | None:
    """`entry`, uncached."""
    got, _ = store.load(path)
    if got is None:
        return None
    said = got.get("verdict") or {}
    fields = summary(got)
    if said.get("score") is not None:
        fields[("", "score")] = said["score"]
    return {"identity": None, "verdict": said.get("label"), "state": said.get("state", "info"),
            "states": {}, "fields": fields, "day": (got.get("computed_at") or "")[:10]}


def mothers(project: str) -> dict[str, dict]:
    """Each mother's batch studies, as table entries keyed by her name.

    Args:
        project: Project name.

    Returns:
        norm name → {study: entry}. Each `wfc_<composition>.json` lands under `wfc` as its
        own sub-panel (`verdict` and `score` of that composition). A mother with two batches
        gets one entry per study that says so instead of a figure.
    """
    out: dict[str, dict] = {}
    for name, folders in batches(project).items():
        if len(folders) > 1:
            twice = {"identity": None, "verdict": "dos lotes", "state": "none", "states": {},
                     "fields": {}, "day": ""}
            out[name] = {s: twice for s in STUDIES}
            continue
        mine = out.setdefault(name, {})
        for study in STUDIES:
            path = folders[0] / "estudios" / f"{study}.json"
            if path.is_file() and (got := entry(path)):     # a copy: the cached one stays clean
                mine[study] = {**got, "fields": dict(got["fields"]), "states": dict(got["states"])}
        for path in sorted((folders[0] / "estudios").glob("wfc_*.json")):
            got = entry(path)
            if got is None:
                continue
            wfc = mine.setdefault("wfc", {**got, "verdict": None, "fields": {}, "states": {}})
            comp = path.stem.removeprefix("wfc_")
            wfc["fields"][(comp, "verdict")] = got["verdict"]
            wfc["fields"][(comp, "score")] = got["fields"].get(("", "score"))
            wfc["states"][comp] = got["state"]
    return out

