"""What of a databank is loaded, what is stale, and the commands that bring it up to date."""

from typing import Any
from pathlib import Path

from core.paths import export_dir, harvest_dir, metrics_export
from ui.daemon import jobs
from ui.daemon.loader import find
from ui.daemon.loader.fingerprint import fingerprint

# The three products a databank's page reads, by what they unlock on screen.
PIECES = {
    "metrics": "métricas de cada estrategia (se leen del .sqx, sin SQX)",
    "trades": "operaciones una a una (el .abk de la sesión viva, o orderstocsv con SQX parado)",
    "harvest": "cosecha IS+OOS emparejada: la Ficha y la puerta (el .abk de la sesión viva, o orderstocsv con SQX parado)",
}


def newest(folder: Path, pattern: str) -> Path | None:
    """The newest dated export under a folder: `<day>/<pattern>`.

    Args:
        folder: `raw/<P>/<D>` or `harvest/<P>/<D>`.
        pattern: The file whose presence makes a day complete, e.g. `manifest.json`.

    Returns:
        That file in the newest complete day, or None.
    """
    days = (
        sorted(d for d in folder.glob("*") if (d / pattern).exists())
        if folder.is_dir()
        else []
    )
    return days[-1] / pattern if days else None


def age(done: Path | None, sources: list[Path]) -> str:
    """Whether an export is missing, older than the strategies it was made from, or fresh.

    Args:
        done: The export's marker (its manifest, or the folder that makes it complete).
        sources: The .sqx files it reads.

    Returns:
        `missing`, `stale` or `fresh`. A strategy added, curated away or retested after the
        export moves a file's time past the marker's; a time moved by SQX's resave alone
        does not: the export's `<marker>.sources.sig`, written the first time it is seen
        fresh, still matches `fingerprint`. Without that every worker stop re-exported every
        databank of the install (📓 2026-09-29: 8 min after a 20-min SPP run).
    """
    if done is None:
        return "missing"
    touched = max((f.stat().st_mtime for f in sources), default=0.0)
    folder = max(
        (f.parent.stat().st_mtime for f in sources), default=0.0
    )  # a file removed
    sig = done.parent / f"{done.name}.sources.sig"
    if max(touched, folder) <= done.stat().st_mtime:
        now = fingerprint(sources)
        if not sig.exists() or sig.read_text() != now:
            sig.write_text(now)
        return "fresh"
    return (
        "fresh" if sig.exists() and sig.read_text() == fingerprint(sources) else "stale"
    )


def trades_age(project: str, databank: str, own: list[Path]) -> str:
    """`age` of a databank's newest trade export against its files."""
    return age(newest(export_dir(project, databank, "x").parent, "manifest.json"), own)


def status(project: str, databank: str) -> dict[str, Any]:
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
        return {
            "databank": db,
            "error": f"{project} / {db} no está en ninguna instalación",
        }
    role, top = where
    own = find.files(top, project, db)
    other = find.partner(top, project, db)
    theirs = find.files(top, project, other) if other else []
    metrics = metrics_export(project, db) / "manifest.json"
    states = {
        "metrics": age(metrics if metrics.exists() else None, own),
        "trades": trades_age(project, db, own),
        "harvest": (
            age(
                newest(harvest_dir(project, db, "x").parent, "manifest.json"),
                own + theirs,
            )
            if other
            else "none"
        ),
    }
    why = {}
    # The newest loader job of each piece decides over the files: running is `loading`, and a
    # failure stays `failed` — never queued again on its own, or a conductor that refuses
    # would be asked every few seconds for ever — until the owner presses retry.
    last = {
        j["loader"]: j
        for j in jobs.listing()  # oldest first: the newest wins
        if j.get("loader") and j["project"] == project and j["databank"] == db
    }
    for piece, job in last.items():
        if job["rc"] is None:
            states[piece] = "loading"
        elif job["rc"] != 0 and not job["cancelled"]:
            states[piece] = "failed"
            why[piece] = " / ".join(job["tail"][-3:])
    return {
        "databank": db,
        "role": role,
        "partner": other,
        "strategies": len(own),
        "writing": find.writing(top, project),
        "pieces": {
            k: {"state": v, "what": PIECES[k], **({"why": why[k]} if k in why else {})}
            for k, v in states.items()
        },
    }


def commands(
    project: str, now: dict, exports: bool = True
) -> dict[str, tuple[str, list[str]]]:
    """The command that refreshes each missing or stale piece, with the lane it runs in.

    Args:
        project: Project name.
        now: What `status()` returned.
        exports: Let a stale harvest also write the databanks' own trade exports (`--exports`)
            when either side's trades are stale: one `orderstocsv` pass instead of
            three (🔬 2026-10-12, 206 s a run). It writes a side only when the pairing took
            the whole databank, so a caller that ran it asks `status` again for the trades.
            Never for a databank (or partner) carrying cross-check markets: its export is
            `export_retest`'s shape.

    Returns:
        Piece → (lane, argv after `python3`), the harvest before the trades. Nothing when
        SQX is writing the project: its files are half-written, and the next selection after
        it finishes loads them.
    """
    if now.get("error") or now["writing"]:
        return {}
    db, role = now["databank"], now["role"]
    top = find.top_of(project, db)
    at = [] if role == "master" else ["--role", role]
    want = {k for k, v in now["pieces"].items() if v["state"] in ("missing", "stale")}
    out = {}
    if "metrics" in want:
        out["metrics"] = (
            "python",
            [
                "-m",
                "sqx.export.export_metrics",
                "--project",
                project,
                "--databank",
                db,
                *at,
            ],
        )
    files = find.files(top, project, db)
    if "harvest" in want:
        other = find.files(top, project, now["partner"])
        due = "trades" in want or trades_age(project, now["partner"], other) != "fresh"
        carry = exports and due and not find.cross_market(files + other)
        out["harvest"] = (
            "conductor",
            [
                "-m",
                "studies.screening.gate.harvest",
                "--project",
                project,
                "--databank",
                db,
                "--oos-databank",
                now["partner"],
                *at,
                *(["--exports"] if carry else []),
            ],
        )
    if "trades" in want and files:
        out["trades"] = (
            "conductor",
            (
                [
                    "-m",
                    "sqx.export.export_retest",
                    "--project",
                    project,
                    "--databank",
                    db,
                    *at,
                ]
                if find.cross_market(files)
                else [
                    "-m",
                    "sqx.export.export_trades",
                    "--project",
                    project,
                    "--databank",
                    db,
                    "--symbol",
                    find.feed(files[0]),
                    *at,
                ]
            ),
        )
    return out


def covers(project: str, now: dict) -> bool:
    """Whether a harvest of this databank pairs every strategy of both sides, so `--exports` leaves none out.

    Identity sets equal and no two files sharing one: otherwise a side is not exported whole and
    the trades job must still run (the window posts only on a selection change).
    """
    if not now.get("partner") or now.get("error"):
        return False
    top = find.top_of(project, now["databank"])
    own, other = (find.roster(project, d) for d in (now["databank"], now["partner"]))
    return (
        bool(own)
        and set(own) == set(other)
        and len(own) == now["strategies"]
        and len(other) == len(find.files(top, project, now["partner"]))
    )


def load(project: str, databank: str, retry: bool = False) -> dict[str, Any]:
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
        now["pieces"] = {
            k: {**v, "state": "missing" if v["state"] == "failed" else v["state"]}
            for k, v in now["pieces"].items()
        }
    todo = commands(project, now, exports=covers(project, now))
    if "--exports" in todo.get("harvest", ("", []))[1]:
        todo.pop(
            "trades", None
        )  # the harvest writes them: it covers the whole databank
    for piece, (lane, argv) in todo.items():
        jobs.start(
            f"cargar {piece}",
            argv,
            {
                "project": project,
                "databank": now["databank"],
                "strategy": "",
                "study": f"cargar {piece}",
                "scope": "many",
                "loader": piece,
            },
            lane=lane,
        )
    return {**status(project, databank), "queued": sorted(todo)}
