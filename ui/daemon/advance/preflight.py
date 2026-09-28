"""Whether «Continuar workflow» may touch a project's install now, and every reason it may not."""

import socket
import time
from pathlib import Path

from core import sqxfile, worker
from core.datapaths import project_registry
from core.paths import MASTER, WORKERS, databank_dir, project_dir
from sqx.projects import registry, stage
from sqx.projects.configure import BY_TASK, DEFAULT_SEGMENT
from ui.daemon import progress
from ui.daemon.filters import discards
from ui.daemon.workflow.steps import STEPS

RECENT_H = 24       # another project of the worker touched this recently: someone works there
QUIET_MIN = 15      # the install's SQX log written this recently: it just ran or is running
# Where a cut's .sqx are copied before they go (owner, Q7): <P>/<D>/<stamp>/.
DISCARDS = project_registry().parent / "discards"
# (path, size, mtime) → identity. ~1 ms a file, but the window re-checks every 20 s.
_IDS: dict[tuple, str] = {}


def where(project: str) -> dict:
    """The install `registry.csv` puts a project on, and the role that drives it.

    Args:
        project: Project name.

    Returns:
        `install` (folder name), `role`, `row`; or `refuse` with the one reason, the
        master's first — the window never touches the owner's install (hard rule 3).
    """
    live = [r for r in registry.rows() if r["name"] == project and not r["retired"]]
    installs = {r["install"] for r in live}
    if MASTER.name in installs:
        return {"refuse": f"{project} vive en el maestro ({MASTER.name}): la ventana nunca "
                          "toca el install del dueño"}
    if not live:
        return {"refuse": f"{project} no está en registry.csv (o está retirado): solo se "
                          "continúa un proyecto creado por sqx.projects.builder"}
    if len(installs) > 1:
        return {"refuse": f"{project} figura vivo en {', '.join(sorted(installs))}: no se sabe "
                          "cuál tocar"}
    install = installs.pop()
    role = next((r for r, w in WORKERS.items() if w["path"].name == install), None)
    if role is None:
        return {"refuse": f"{install} no es ningún worker de config/machine.yaml"}
    return {"install": install, "role": role, "row": live[-1]}


def busy(role: str, project: str) -> list[str]:
    """Why the worker cannot be taken now: every sign that someone else is on it.

    Args:
        role: A worker role.
        project: The project about to run; its own recent changes do not count.

    Returns:
        The reasons, empty when the install is free. Read-only: a socket probe, /proc and
        file dates. A worker that is up is refused, never stopped (owner, Q6): a `stop`
        kills anyone's run (OPEN.md §32).
    """
    top, port = WORKERS[role]["path"], WORKERS[role]["port"]
    out = []
    with socket.socket() as s:
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            out.append(f"install ocupado: el puerto {port} de {top.name} responde")
    pids = worker.holding(top)
    if pids:
        out.append(f"install ocupado: {len(pids)} proceso(s) de SQX trabajan desde {top.name} "
                   f"(PID {', '.join(map(str, pids))})")
    now = time.time()
    for cfx in sorted((top / "user" / "projects").glob("*/project.cfx")):
        folder = cfx.parent
        newest = max([folder.stat().st_mtime, cfx.stat().st_mtime]
                     + [p.stat().st_mtime for sub in ("log", "databanks")
                        for p in (folder / sub).glob("*")])
        if folder.name != project and now - newest < RECENT_H * 3600:
            out.append(f"{folder.name} se modificó en {top.name} hace "
                       f"{(now - newest) / 3600:.1f} h: puede ser de otra sesión")
    lines, mtime = progress.log_lines(top)
    run = progress.run_state(lines)
    if mtime and now - mtime < QUIET_MIN * 60:
        out.append(f"el log de hoy de {top.name} se escribió hace {(now - mtime) / 60:.0f} "
                   f"min (< {QUIET_MIN})")
    if run["project"] and not run["finished"]:
        out.append(f"el log de {top.name} dice que {run['project']} empezó y no ha terminado")
    return out


def by_identity(source: Path) -> dict[str, list[Path]]:
    """A databank's files grouped by identity; SQX can hold one strategy under two names.

    Args:
        source: The databank folder.

    Returns:
        Identity → its files. Hashes are cached per path, size and mtime.
    """
    out: dict[str, list[Path]] = {}
    for f in sorted(source.glob("*.sqx")):
        st = f.stat()
        key = (str(f), st.st_size, st.st_mtime_ns)
        if key not in _IDS:
            _IDS[key] = sqxfile.identity(f)
        out.setdefault(_IDS[key], []).append(f)
    return out


def step_of(title: str) -> dict | None:
    """The workflow step (a row of `steps.STEPS`) whose SQX stage runs this task title."""
    return next((s for s in STEPS if "stage" in s and title in stage.titles(s["stage"])), None)


def next_task(tasks: list[dict], databank: str) -> dict:
    """The task «Continuar» launches after cutting a databank.

    Args:
        tasks: The project's chain, as `progress.tasks` reads it.
        databank: The databank being cut.

    Returns:
        `producer` (the task writing the databank), `step` (its workflow step), `segment`
        (the one it was priced on, `sqx.projects.configure`), `task` (the next task's
        title), `stage` and `skip` (the stage's other titles, left off); or `refuse`.
        The next task is the first one, in WORKFLOW.md's order after the producer's step,
        that reads this databank: a task that reads another would not see the cut.
    """
    producer = next((t for t in tasks if t["output"] == databank), None)
    here = step_of(producer["title"]) if producer else None
    if here is None:
        return {"refuse": f"ninguna tarea de un paso del workflow escribe «{databank}»"}
    later = STEPS[STEPS.index(here) + 1:]
    for s in [s for s in later if "stage" in s]:
        titles = stage.titles(s["stage"])
        hit = next((t for t in tasks if t["title"] in titles and t["input"] == databank), None)
        if hit:
            return {"producer": producer["title"], "step": here["n"],
                    "segment": BY_TASK.get(producer["type"], DEFAULT_SEGMENT),
                    "task": hit["title"], "stage": s["stage"],
                    "skip": [t for t in titles if t != hit["title"]]}
    return {"refuse": f"ninguna tarea posterior a «{producer['title']}» lee «{databank}»"}


def check(project: str, databank: str) -> dict:
    """Every precondition of «Continuar workflow», in the plan's order.

    Args:
        project: Project name.
        databank: The databank whose discards would be deleted.

    Returns:
        `ok`, `reasons` (empty when ok), and what the confirmation and the run need:
        `role`, `install`, `row`, `cfx`, `databank` (as SQX spells it), `source`, `n`
        (distinct identities discarded), `files` (their .sqx on disk, ≥ n), `discards`, and
        the `next_task` fields.
    """
    got = where(project)
    if "refuse" in got:
        return {"ok": False, "reasons": [got["refuse"]]}
    reasons = busy(got["role"], project)
    top = WORKERS[got["role"]]["path"]
    cfx = project_dir(project, top) / "project.cfx"
    if not cfx.exists():
        return {"ok": False, "reasons": reasons + [f"{project} no está en {top.name}"]}
    tasks = progress.tasks(cfx)
    # The window may send either spelling; the install's folder is the one SQX writes.
    databank = next((t["output"] for t in tasks
                     if t["output"].replace(" ", "_") == databank.replace(" ", "_")), databank)
    source = databank_dir(project, databank, top)
    rows = discards.live(project, databank)
    n = len({r["identity"] for r in rows})
    if not n:
        reasons.append(f"no hay descartes de «{databank}»: filtra o borra a mano primero")
    held = by_identity(source)
    if not held:
        reasons.append(f"«{databank}» no tiene ningún .sqx en {top.name}: no hay nada que "
                       "borrar (¿Auto-sync never, o el databank no es de este install?)")
    ids = {r["identity"] for r in rows}
    gone = ids - set(held)
    if held and gone:
        reasons.append(f"{len(gone)} de {n} descartes ya no están en «{databank}»: el databank "
                       "cambió desde el filtro. Quita los filtros y vuelve a filtrar")
    files = sum(len(held.get(i, [])) for i in ids)
    following = next_task(tasks, databank)
    if "refuse" in following:
        reasons.append(following.pop("refuse"))
    return {"ok": not reasons, "reasons": reasons, **got, "cfx": cfx, "databank": databank,
            "source": source, "n": n, "files": files, "discards": rows, **following}
