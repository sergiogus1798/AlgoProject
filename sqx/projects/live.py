"""Drive one headless GUI-mode SQX session (`bin/sqx-worker.sh --gui`) through the window's own /project servlet."""

import contextlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from core import worker
from core.datapaths import tmp_dir
from core.paths import ROOT, WORKERS
from sqx.projects import cfxio, loadwait, presaving, taskcap
from sqx.projects.liveapi import _setting, call, kill  # noqa: F401  (`exiting` reads the token here)

SCRIPT = ROOT / "bin" / "sqx-worker.sh"
MISSES = 5  # polls in a row the port must refuse before `wait` calls the session dead
END = re.compile(r"Project finished")
BAD = re.compile(
    r"Project stopped|Error while running project|Exception in task|OutOfMemory"
)  # as wait.sh's


def _top(role: str) -> Path:
    """The install folder of a worker role."""
    return WORKERS[role]["path"]


def _up(role: str) -> bool:
    """Whether something listens on that worker's port."""
    return worker.listening(WORKERS[role]["port"])


def mine(role: str) -> bool:
    """Whether a GUI session this holder started is up on that worker."""
    top, lock = _top(role), _top(role) / "user/log/OWNER"
    if not (top / "user/log/XVFB").exists() or not lock.exists():
        return False
    return _up(role) and json.loads(lock.read_text())["holder"] == worker.holder()


def gui_up(role: str) -> bool:
    """Whether a GUI session, anyone's, is up on that worker."""
    return _up(role) and (_top(role) / "user/log/XVFB").exists()


def start(role: str, project: str | None = None) -> None:
    """Start the worker in GUI mode; return once `project`'s databanks (default: every custom project's) are loaded.

    🔬 2026-10-01: memory == disk before any sync, or it mirrors empty memory over the files (rule 1).
    With `project`, the others load in the background and `stop` waits and the background thread saves them in parallel (§7.1/7.4b, always on since 2026-10-13).
    """
    if pids := worker.holding(_top(role)):
        raise SystemExit(
            f"{role} ya está arrancado (PID {pids}): no se arranca ni se mata"
        )
    loadwait.booted(
        role,
        lambda: subprocess.run(
            [str(SCRIPT), "--role", role, "--gui", "start"], check=True
        ),
    )
    own = (
        [project]
        if project
        else [
            p["name"]
            for p in call(role, "list")["projects"]
            if p["name"].startswith(("Test_", "Trade_", "Research_"))
        ]
    )
    for _ in range(300):
        off = [
            f"{p}/{b}: {_files(p, role, b)} ficheros, {n} en memoria"
            for p in own
            for b, n in records(role, p).items()
            if _files(p, role, b) != n
        ]
        if not off:
            break
        time.sleep(1)
    else:
        kill(role)
        raise SystemExit(
            f"{role}: los databanks no cargaron en 5 min; sesión matada por PID, ficheros intactos: "
            + "; ".join(off)
        )
    if project:
        presaving.begin(role, project, _files, _log)


def stop(role: str, export: bool = True) -> None:
    """Stop it (`/main/exitapp`) once every databank has loaded; the script exports after unless told not to."""
    presaving.settle(role)
    env = None if export else {**os.environ, "ALGO_NO_EXPORT": "1"}
    subprocess.run([str(SCRIPT), "--role", role, "stop"], check=True, env=env)


def _log(role: str) -> Path:
    """SQX's own log of today."""
    return max(
        (_top(role) / "user/log/StrategyQuant").glob("log_*.log"),
        key=lambda p: p.stat().st_mtime,
    )


def _files(project: str, role: str, bank: str) -> int:
    """.sqx files of one databank on disk."""
    return len(
        list(
            (_top(role) / "user/projects" / project / "databanks" / bank).glob("*.sqx")
        )
    )


def mark(role: str) -> tuple[Path, int]:
    """Where SQX's log ends now: `wait` reads only what is written after it."""
    return (log := _log(role)), log.stat().st_size


def wait(role: str, since: tuple[Path, int]) -> str:
    """Block until the project started after `since` ends; the line that ended it.

    A build ends on its own `time-limit` (`/project/stop` does not stop one, 🔬). SystemExit on an
    abort line (`BAD`), a task past its deadline (`taskcap`), the port down MISSES polls, or `worker.MAX_HOURS`."""
    (log, offset), (began, down, cap) = since, (time.monotonic(), 0, taskcap.fresh())
    while True:
        down = (
            0 if _up(role) else down + 1
        )  # asked before the read: the last line counts
        with open(log, "rb") as f:
            f.seek(offset)
            chunk = f.read()
        whole = chunk[: chunk.rfind(b"\n") + 1]  # a half-written line waits for its end
        offset += len(whole)
        for line in whole.decode("utf-8", "replace").splitlines():
            taskcap.note(cap, line)
            if END.search(line):
                return line.strip()
            if BAD.search(line):  # the abort line: «Project finished» never comes
                raise SystemExit(
                    f"{role}: SQX abortó la corrida: {line.strip()[:200]} ({log})"
                )
        taskcap.enforce(cap, role, log)
        if not whole and _log(role) != log:  # midnight: its end read, the next day's
            log, offset = _log(role), 0
            continue
        if down >= MISSES:
            raise SystemExit(
                f"el {role} dejó de escuchar antes de «Project finished» ({log})"
            )
        if time.monotonic() - began > worker.MAX_HOURS * 3600:
            raise SystemExit(
                f"{role}: sin «Project finished» tras {worker.MAX_HOURS} h ({log})"
            )
        time.sleep(1)


def added(staged: Path, held: Path) -> list[str]:
    """Members `staged` has and `held` does not: new tasks, which a live session cannot take."""
    with zipfile.ZipFile(staged) as a, zipfile.ZipFile(held) as b:
        return sorted(set(a.namelist()) - set(b.namelist()))


def push(role: str, project: str, staged: Path, held: Path) -> str:
    """Send SQX every task XML a configurator changed in `staged`; its config.xml, to start with.

    Args:
        staged: The copy of `held` the configurators and `stage.just` wrote.
        held: The project.cfx the running install holds (hard rule 4: never written here).
    """
    new, old, extra = cfxio.members(staged), cfxio.members(held), added(staged, held)
    if extra:
        raise SystemExit(
            f"la copia trae ficheros que el proyecto vivo no tiene: {extra}"
        )
    for name in sorted(n for n in new if n != "config.xml" and new[n] != old[n]):
        call(
            role,
            "updateTaskXML",
            projectName=project,
            taskXMLFile=name,
            xmlConfig=new[name].decode("utf-8"),
        )
    return new["config.xml"].decode("utf-8")


def run(role: str, project: str, config: str) -> str:
    """Start every task `config` leaves active, as the window's Start does, and wait for it."""
    since = mark(role)
    call(role, "start", projectName=project, projectXML=config)
    return wait(role, since)


def records(role: str, project: str) -> dict[str, int]:
    """Strategies in memory per databank."""
    return {
        d["name"]: d["records"]
        for d in call(role, "databankList", projectName=project)["databanks"]
    }


def _newest(project: str, role: str, bank: str) -> int:
    """When a databank's files were last written: what moves while SQX rewrites them at one count."""
    stamp = 0
    for f in (_top(role) / "user/projects" / project / "databanks" / bank).glob(
        "*.sqx"
    ):
        with contextlib.suppress(
            FileNotFoundError
        ):  # SQX may be replacing it this instant
            stamp = max(stamp, f.stat().st_mtime_ns)
    return stamp


def tail(role: str, since: tuple[Path, int]) -> str:
    """SQX's log past `since`, and the next day's whole past midnight."""
    parts = []
    for log, offset in dict([(_log(role), 0), since]).items():
        with open(log, "rb") as f:
            f.seek(offset)
            parts.append(f.read().decode("utf-8", "replace"))
    return "".join(parts)


def _saved(role: str, since: tuple[Path, int], project: str) -> set[str]:
    """The project's databanks whose API sync SQX's log says, past `since`, has ended (🔬 2026-10-13)."""
    return set(
        re.findall(
            rf"Databank '{re.escape(project)}/([^']+)' saved [^\n]*API request",
            tail(role, since),
        )
    )


def sync(
    role: str,
    project: str,
    banks: list[str] | None = None,
    force: frozenset[str] | set[str] = frozenset(),
) -> dict[str, int]:
    """Write memory onto disk (a sync mirrors it) and wait until every file count matches.

    A databank SQX keeps on «Auto-sync never» («Last generation», the genetic pool) never
    reaches disk, whatever its config.xml says: it is left out (🔬 2026-10-01). `force` names the
    ones synced even when files == memory (a count cannot tell): their end is SQX's own «saved …
    API request» line. SystemExit on a name SQX does not hold.

    SQX's saver is serial (🔬 2026-10-13): a queued forced bank sits untouched, so only its line ends it."""
    listed = call(role, "databankList", projectName=project)["databanks"]
    mem = {
        d["name"]: d["records"] for d in listed if d["syncType"] != "Auto-sync never"
    }
    if lost := sorted({*(banks or ()), *force} - {d["name"] for d in listed}):
        raise SystemExit(
            f"{project}: SQX no tiene en memoria {lost}; tiene {sorted(d['name'] for d in listed)}"
        )
    forced, since = (
        {b for b in force if mem.get(b)},
        mark(role),
    )  # an empty one writes nothing, and no «saved» line
    banks = [b for b in mem if b in forced or b in (banks or mem)]
    stale = [b for b in banks if b in forced or _files(project, role, b) != mem[b]]
    # At once: SQX writes ~9 MB/s per databank, and three together went at 17 (🔬 2026-10-05).
    with ThreadPoolExecutor(len(stale) or 1) as pool:
        list(
            pool.map(
                lambda b: call(
                    role, "synchronizeDatabank", projectName=project, databankName=b
                ),
                stale,
            )
        )
    last, idle = None, 0
    while (
        idle < 600
    ):  # 120 s with no new file: a 15,000-strategy flush takes longer than that
        disk = {b: _files(project, role, b) for b in banks}
        if all(disk[b] == mem[b] for b in banks) and (
            not forced or forced <= _saved(role, since, project)
        ):
            return mem
        now = (disk, [_newest(project, role, b) for b in forced])
        moved = now != last
        idle, last = (0, now) if moved else (idle + 1, last)
        time.sleep(0.2)
    raise SystemExit(
        f"{project}: el disco se paró 120 s sin igualar la memoria: disco {disk}, memoria "
        f"{ ({b: mem[b] for b in banks}) }, sin «saved» en el log {sorted(forced - _saved(role, since, project))}"
    )


def cut(role: str, project: str, bank: str, names: list[str]) -> int:
    """Drop strategies from a databank by name, live, then mirror it to disk; how many went."""
    before = records(role, project)[bank]
    after = call(
        role,
        "removeReports",
        projectName=project,
        databankName=bank,
        strategies=",".join(names),
    )["records"]
    sync(role, project, [bank])
    if before - after < len(
        set(names)
    ):  # as `apply_verdict`: a name SQX did not hold stayed
        raise SystemExit(
            f"{project}/{bank}: se pidió quitar {len(names)} y salieron {before - after} ({before} → {after})"
        )
    return before - after


def load(role: str, project: str, bank: str) -> int:
    """Make memory hold exactly the .sqx a fill just wrote into the databank's folder.

    A file never loaded is deleted by the next sync (rule 1): the folder is copied aside, memory
    cut to nothing (`clear="true"` does NOT empty it, 🔬 2026-10-06) and refilled from the copy;
    a load not done in 120 s raises BEFORE any sync, copy kept."""
    folder = _top(role) / "user/projects" / project / "databanks" / bank
    want = len(list(folder.glob("*.sqx")))
    tmp = tempfile.mkdtemp(dir=tmp_dir())
    for f in folder.glob("*.sqx"):
        shutil.copy2(f, tmp)
    stale = call(role, "listStrategies", projectName=project, databankName=bank)[
        "strategies"
    ]
    if stale:
        cut(role, project, bank, stale)
    call(
        role,
        "loadFilesToDatabank",
        projectName=project,
        databankName=bank,
        folder=tmp,
        clear="true",
        all="true",
    )
    for _ in range(600):
        got = records(role, project)[bank]
        if got == want:
            break
        time.sleep(0.2)
    if got != want:
        raise SystemExit(
            f"{bank}: {got} en memoria tras 120 s cargando {want} ficheros; no se "
            f"sincroniza (un sync borraría los que faltan). Su copia queda en {tmp}"
        )
    shutil.rmtree(tmp)
    sync(role, project, [bank])
    return got
