"""What of a databank is loaded, what is stale, and the commands that bring it up to date."""

from pathlib import Path

from core.paths import export_dir, harvest_dir, metrics_export
from ui.daemon import jobs
from ui.daemon.loader import find

# The three products a databank's page reads, by what they unlock on screen.
PIECES = {"metrics": "métricas de cada estrategia (se leen del .sqx, sin SQX)",
          "trades": "operaciones una a una (orderstocsv en el conductor)",
          "harvest": "cosecha IS+OOS emparejada: la Ficha y la puerta (orderstocsv en el conductor)"}


def newest(folder: Path, pattern: str) -> Path | None:
    """The newest dated export under a folder: `<day>/<pattern>`.

    Args:
        folder: `raw/<P>/<D>` or `harvest/<P>/<D>`.
        pattern: The file whose presence makes a day complete, e.g. `manifest.json`.

    Returns:
        That file in the newest complete day, or None.
    """
    days = sorted(d for d in folder.glob("*") if (d / pattern).exists()) if folder.is_dir() else []
    return days[-1] / pattern if days else None


def age(done: Path | None, sources: list[Path]) -> str:
    """Whether an export is missing, older than the files it was made from, or fresh.

    Args:
        done: The export's manifest, or None.
        sources: The .sqx files it reads.

    Returns:
        `missing`, `stale` or `fresh`. A strategy added, curated away or retested after the
        export moves a file's time past the manifest's.
    """
    if done is None:
        return "missing"
    touched = max((f.stat().st_mtime for f in sources), default=0.0)
    folder = max((f.parent.stat().st_mtime for f in sources), default=0.0)   # a file removed
    return "stale" if max(touched, folder) > done.stat().st_mtime else "fresh"


def status(project: str, databank: str) -> dict:
    """Everything the window says about one databank's data, and why.

    Args:
        project: Project name.
        databank: Either spelling of the databank.

    Returns:
        `databank` as SQX spells it, `role`, `partner`, `strategies`, `writing`, and per
        piece its `state` (fresh | stale | missing | loading | none) and `what` it unlocks.
        `none` is a piece this databank does not have — a harvest needs a build databank.
    """
    db = find.spelled(project, databank)
    where = find.install_of(project, db)
    if where is None:
        return {"databank": db, "error": f"{project} / {db} no está en ninguna instalación"}
    role, top = where
    own = find.files(top, project, db)
    other = find.partner(top, project, db)
    theirs = find.files(top, project, other) if other else []
    metrics = metrics_export(project, db) / "manifest.json"
    states = {"metrics": age(metrics if metrics.exists() else None, own),
              "trades": age(newest(export_dir(project, db, "x").parent, "manifest.json"), own),
              "harvest": (age(newest(harvest_dir(project, db, "x").parent, "manifest.json"),
                              own + theirs) if other else "none")}
    why = {}
    # The newest loader job of each piece decides over the files: running is `loading`, and a
    # failure stays `failed` — never queued again on its own, or a conductor that refuses
    # would be asked every few seconds for ever — until the owner presses retry.
    last = {j["loader"]: j for j in jobs.listing()      # oldest first: the newest wins
            if j.get("loader") and j["project"] == project and j["databank"] == db}
    for piece, job in last.items():
        if job["rc"] is None:
            states[piece] = "loading"
        elif job["rc"] != 0 and not job["cancelled"]:
            states[piece] = "failed"
            why[piece] = " / ".join(job["tail"][-3:])
    return {"databank": db, "role": role, "partner": other, "strategies": len(own),
            "writing": find.writing(top, project),
            "pieces": {k: {"state": v, "what": PIECES[k], **({"why": why[k]} if k in why else {})}
                       for k, v in states.items()}}


def commands(project: str, now: dict) -> dict[str, tuple[str, list[str]]]:
    """The command that refreshes each missing or stale piece, with the lane it runs in.

    Args:
        project: Project name.
        now: What `status()` returned.

    Returns:
        Piece → (lane, argv after `python3`). Nothing when SQX is writing the project: its
        files are half-written, and the next selection after it finishes loads them.
    """
    if now.get("error") or now["writing"]:
        return {}
    db, role = now["databank"], now["role"]
    top = find.install_of(project, db)[1]
    at = [] if role == "master" else ["--role", role]
    want = {k for k, v in now["pieces"].items() if v["state"] in ("missing", "stale")}
    out = {}
    if "metrics" in want:
        out["metrics"] = ("python", ["-m", "sqx.export.export_metrics", "--project", project,
                                     "--databank", db, *at])
    first = find.files(top, project, db)[:1]
    if "trades" in want and first:
        out["trades"] = ("conductor", (
            ["-m", "sqx.export.export_retest", "--project", project, "--databank", db, *at]
            if find.cross_market(first[0]) else
            ["-m", "sqx.export.export_trades", "--project", project, "--databank", db,
             "--symbol", find.feed(first[0]), *at]))
    if "harvest" in want:
        out["harvest"] = ("conductor", ["-m", "studies.screening.gate.harvest", "--project",
                                        project, "--databank", db, "--oos-databank",
                                        now["partner"], *at])
    return out


def load(project: str, databank: str, retry: bool = False) -> dict:
    """Queue whatever this databank is missing, once, and say where it stands.

    Args:
        project: Project name.
        databank: Either spelling.
        retry: Queue the pieces whose last load failed as well.

    Returns:
        `status()` after queueing, with `queued`: the pieces this call started.
    """
    now = status(project, databank)
    if retry:
        now["pieces"] = {k: {**v, "state": "missing" if v["state"] == "failed" else v["state"]}
                         for k, v in now["pieces"].items()}
    todo = commands(project, now)
    for piece, (lane, argv) in todo.items():
        jobs.start(f"cargar {piece}", argv,
                   {"project": project, "databank": now["databank"], "strategy": "",
                    "study": f"cargar {piece}", "scope": "many", "loader": piece}, lane=lane)
    return {**status(project, databank), "queued": sorted(todo)}
