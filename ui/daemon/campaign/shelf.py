"""The campaign's folders as the window reads them: workflows, their strategies and the results the archive cannot pair."""

import json
from pathlib import Path

from core.datapaths import campaign_dir
from ui.daemon.archive import shelf as archive
from ui.daemon.results import catalogue

# Studies of steps 16.5-18.5 kept under `madres/<mother>/estudios/` (the archive pairs by identity, they sign another).
MOTHER_STUDIES = ("wfc", "cscv", "marketSurfaces")


def _folder(name: str) -> Path:
    """One workflow's folder; raises FileNotFoundError for a name that is not a folder of `runs/`."""
    folder = campaign_dir() / "runs" / Path(name).name
    if not (folder / "workflow.json").is_file():
        raise FileNotFoundError(f"No hay un workflow guardado llamado «{name}».")
    return folder


def _doc(name: str) -> dict:
    """A workflow's `workflow.json`."""
    return json.loads((_folder(name) / "workflow.json").read_text(encoding="utf-8"))


def _when(name: str) -> str:
    """`2026-10-05 20:55` from the stamp the folder name ends in."""
    stamp = name.split("_")[-1]
    return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]} {stamp[9:11]}:{stamp[11:13]}"


def workflows() -> list[dict]:
    """Every saved workflow, newest first, as the list shows it.

    Returns:
        `name`, `when`, `template`, `symbol`, `timeframe`, `direction`, `state`, `minutes`,
        `finalists` and `counts` (`A→B` of every step, in order).
    """
    out = []
    for f in sorted((campaign_dir() / "runs").glob("*/workflow.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        out.append({"name": f.parent.name, "when": _when(f.parent.name)} | {
            k: d[k] for k in ("template", "symbol", "timeframe", "direction", "state",
                              "finalists", "counts")} | {"minutes": d.get("steps_minutes", d.get("minutes"))})
    return sorted(out, key=lambda r: r["when"], reverse=True)


def show(name: str) -> dict:
    """One workflow: its header, its funnel and time per step, its strategies and what was not kept.

    Returns:
        The list row, plus `project`, `steps` (`step`, `kind`, `seconds`, `what`, `counts`),
        `strategies` (`name`, `identity`, `version`, `mother`, `mother_identity`,
        `mother_version`, `stop`) and `not_kept` (`path`, `reason`).
    """
    d = _doc(name)
    rows = [{"name": s["strategy"], "identity": s["identity"],
             "version": Path(s["archive"]).name if s.get("archive") else None,
             "mother": s["mother"], "mother_identity": s.get("mother_identity"),
             "mother_version": Path(s["mother_archive"]).name if s.get("mother_archive") else None,
             "stop": s.get("stop")} for s in d["strategies"]]
    head = next(r for r in workflows() if r["name"] == name)
    return head | {"project": d["project"], "steps": d["steps"], "strategies": rows,
                   "not_kept": d.get("not_kept", [])}


def extras(name: str, mother: str) -> list[dict]:
    """The result files of one mother that live in the workflow folder, not in the archive.

    Returns:
        `key` (path under the folder), `study`, `title`, `step`, ordered by step.
    """
    folder = _folder(name)
    found = [p for p in (folder / "madres" / mother / "estudios").glob("*.json") if p.stem in MOTHER_STUDIES]
    found += [p for p in folder.glob(f"*/**/estrategias/{mother}.json") if "run" not in p.relative_to(folder).parts[:1]]
    out = []
    for p in found:
        study = p.stem if p.parent.name == "estudios" else p.parent.parent.name
        fam, _, title, step = catalogue.STUDIES.get(study, ("", "", study, ""))
        rel = p.relative_to(folder)
        pas = next((x for x in rel.parts if x.startswith("pass")), "")
        out.append({"key": str(rel), "study": study, "title": f"{title} ({pas})" if pas else title, "step": step})
    return sorted(out, key=lambda e: (float(e["step"] or 99), e["study"]))


def opened(name: str, strategy: str) -> dict:
    """What the Estrategia page needs to open one finalist: the MOTHER's archived version.

    The studies of steps 8-22 are signed with the mother's identity and the variant has no
    cosecha of its own, so the page reads the mother's version, labelled as hers.

    Returns:
        `archive.show` of the mother (of the finalist itself when the mother was not archived),
        plus `label` (the finalist's name), `banner` (what the owner is looking at), `extras`
        and `workflow`.
    """
    s = next((r for r in show(name)["strategies"] if r["name"] == strategy), None)
    if s is None:
        raise FileNotFoundError(f"El workflow no tiene la estrategia «{strategy}».")
    mother = bool(s["mother_identity"] and s["mother_version"])
    got = archive.show(s["mother_identity"], s["mother_version"]) if mother \
        else archive.show(s["identity"], s["version"])
    stop = s["stop"] or {}
    banner = (f"Esta final es la variante con stop p{stop.get('percentile', '?')} "
              f"(x = {stop.get('x', '?')} ATR) de la madre «{s['mother']}». Las cifras y los estudios "
              "de abajo son los de la madre («de la madre»): la variante no tiene cosecha propia "
              "porque el stop se fabricó después.") if mother else \
        "La madre de esta final no se archivó: solo se ven los estudios de la propia variante."
    return got | {"label": s["name"], "banner": banner, "workflow": name,
                  "extras": extras(name, s["mother"])}


def extra(name: str, key: str) -> dict:
    """One extra result in the shape `/api/result` answers: `result` and `meta`."""
    folder = _folder(name)
    path = (folder / key).resolve()
    if folder.resolve() not in path.parents or path.suffix != ".json":
        raise FileNotFoundError("Ese resultado no está en el workflow.")
    result = json.loads(path.read_text(encoding="utf-8"))
    return {"result": result, "meta": {
        "day": result.get("computed_at", "")[:10], "path": None, "config_hash": result.get("config_hash"),
        "current_hash": result.get("config_hash"), "stale": False, "computed_at": result.get("computed_at"),
        "skipped": [], "elsewhere": None, "other_identity": False, "note": ""}}
