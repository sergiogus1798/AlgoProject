"""Drive one headless GUI-mode SQX session (`bin/sqx-worker.sh --gui`) through the window's own /project servlet."""

import json
import shutil
import os
import re
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from functools import lru_cache
from pathlib import Path

from core import worker
from core.datapaths import tmp_dir
from core.paths import ROOT, WORKERS
from sqx.projects import cfxio

SCRIPT = ROOT / "bin" / "sqx-worker.sh"
MISSES = 5          # polls in a row the port must refuse before `wait` calls the session dead
END = re.compile(r"Project finished|Project stopped|Error while running project")


def _top(role: str) -> Path:
    """The install folder of a worker role."""
    return WORKERS[role]["path"]


@lru_cache(maxsize=8)
def _settings(role: str, mtime_ns: int) -> str:
    """The install's settings.xml as of one modification time (SQX rewrites it at every GUI start)."""
    return (_top(role) / "user/settings/settings.xml").read_text(encoding="utf-8")


def _setting(role: str, key: str) -> str:
    """One value SQX wrote to the install's settings.xml (port and token: at every GUI start)."""
    text = _settings(role, (_top(role) / "user/settings/settings.xml").stat().st_mtime_ns)
    return re.search(rf"<{key}>([^<]*)", text).group(1)


def _holder() -> str:
    """Who `bin/sqx-lock.sh` records as the holder, resolved the same way."""
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or os.environ.get("SQX_OWNER") or "owner"


def _up(role: str) -> bool:
    """Whether something listens on that worker's port."""
    return worker.listening(WORKERS[role]["port"])


def mine(role: str) -> bool:
    """Whether a GUI session this holder started is up on that worker."""
    top = _top(role)
    lock = top / "user/log/OWNER"
    if not (top / "user/log/XVFB").exists() or not lock.exists():
        return False
    return _up(role) and json.loads(lock.read_text())["holder"] == _holder()


def gui_up(role: str) -> bool:
    """Whether a GUI session, anyone's, is up on that worker: what a reader like the window asks."""
    return _up(role) and (_top(role) / "user/log/XVFB").exists()


def start(role: str) -> None:
    """Start the worker in GUI mode and return once every custom project's databanks are loaded.

    🔬 2026-10-01: a GUI session answers with every databank at 0 records and loads them from
    disk some seconds later; a sync in that gap would mirror the empty memory over the files
    (hard rule 1). Nothing may touch a databank before memory == disk.
    """
    subprocess.run([str(SCRIPT), "--role", role, "--gui", "start"], check=True)
    own = [p["name"] for p in call(role, "list")["projects"]
           if p["name"].startswith(("Test_", "Trade_", "Research_"))]
    for _ in range(300):
        if all(_files(p, role, b) == n for p in own for b, n in records(role, p).items()):
            return
        time.sleep(1)
    raise SystemExit(f"{role}: los databanks no terminaron de cargarse en 5 min; no se toca nada")


def stop(role: str, export: bool = True) -> None:
    """Stop it (`/main/exitapp`); the script exports after the stop unless told not to."""
    env = None if export else {**os.environ, "ALGO_NO_EXPORT": "1"}
    subprocess.run([str(SCRIPT), "--role", role, "stop"], check=True, env=env)


def call(role: str, action: str, **params: str) -> dict:
    """POST one /project/<action>; SystemExit with SQX's own words on an `error` answer."""
    port, token = _setting(role, "WebServerPortUsed"), _setting(role, "BrowserToken")
    req = urllib.request.Request(f"http://localhost:{port}/project/{action}",
                                 data=urllib.parse.urlencode(params, doseq=True).encode(),
                                 headers={"browserToken": token})
    with urllib.request.urlopen(req, timeout=600) as r:
        got = json.loads(r.read().decode("utf-8"))
    if "error" in got:
        raise SystemExit(f"SQX /project/{action}: {got['error']}")
    return got


def _log(role: str) -> Path:
    """SQX's own log of today."""
    return max((_top(role) / "user/log/StrategyQuant").glob("log_*.log"),
               key=lambda p: p.stat().st_mtime)


def mark(role: str) -> tuple[Path, int]:
    """Where SQX's log ends now: `wait` reads only what is written after it."""
    log = _log(role)
    return log, log.stat().st_size


def wait(role: str, since: tuple[Path, int]) -> str:
    """Block until the project started after `since` ends; the line that ended it.

    The agent never reads SQX's log: this does, and returns one line. Nothing here stops a
    build: `/project/stop` does not stop one (🔬), so the build ends on its own `time-limit`.
    SystemExit when the port stays down MISSES polls in a row, or past `worker.MAX_HOURS`.
    """
    log, offset = since
    began, down = time.monotonic(), 0
    while True:
        down = 0 if _up(role) else down + 1           # asked before the read: the last line counts
        with open(log, "rb") as f:
            f.seek(offset)
            chunk = f.read()
        whole = chunk[:chunk.rfind(b"\n") + 1]        # a half-written line waits for its end
        offset += len(whole)
        for line in whole.decode("utf-8", "replace").splitlines():
            if END.search(line):
                return line.strip()
        if not whole and _log(role) != log:           # midnight: its end read, the next day's
            log, offset = _log(role), 0
            continue
        if down >= MISSES:
            raise SystemExit(f"el {role} dejó de escuchar antes de «Project finished» ({log})")
        if time.monotonic() - began > worker.MAX_HOURS * 3600:
            raise SystemExit(f"{role}: sin «Project finished» tras {worker.MAX_HOURS} h ({log})")
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
    new = cfxio.members(staged)
    old = cfxio.members(held)
    extra = added(staged, held)
    if extra:
        raise SystemExit(f"la copia trae ficheros que el proyecto vivo no tiene: {extra}")
    for name in sorted(n for n in new if n != "config.xml" and new[n] != old[n]):
        call(role, "updateTaskXML", projectName=project, taskXMLFile=name,
             xmlConfig=new[name].decode("utf-8"))
    return new["config.xml"].decode("utf-8")


def run(role: str, project: str, config: str) -> str:
    """Start every task `config` leaves active, as the window's Start does, and wait for it."""
    since = mark(role)
    call(role, "start", projectName=project, projectXML=config)
    return wait(role, since)


def records(role: str, project: str) -> dict[str, int]:
    """Strategies in memory per databank."""
    return {d["name"]: d["records"]
            for d in call(role, "databankList", projectName=project)["databanks"]}


def _files(project: str, role: str, bank: str) -> int:
    """.sqx files of one databank on disk."""
    return len(list((_top(role) / "user/projects" / project / "databanks" / bank).glob("*.sqx")))


def sync(role: str, project: str, banks: list[str] | None = None) -> dict[str, int]:
    """Write memory onto disk (a sync mirrors it) and wait until every file count matches.

    A databank SQX keeps on «Auto-sync never» («Last generation», the genetic pool) never
    reaches disk, whatever its config.xml says: it is left out (🔬 2026-10-01).
    """
    listed = call(role, "databankList", projectName=project)["databanks"]
    mem = {d["name"]: d["records"] for d in listed if d["syncType"] != "Auto-sync never"}
    banks = [b for b in banks or mem if b in mem]
    for bank in banks:
        if _files(project, role, bank) != mem[bank]:
            call(role, "synchronizeDatabank", projectName=project, databankName=bank)
    for _ in range(600):
        if all(_files(project, role, b) == mem[b] for b in banks):
            return mem
        time.sleep(0.2)
    raise SystemExit(f"{project}: el disco no llegó a igualar la memoria en 120 s: {mem}")


def cut(role: str, project: str, bank: str, names: list[str]) -> int:
    """Drop strategies from a databank by name, live, then mirror it to disk; how many went."""
    before = records(role, project)[bank]
    after = call(role, "removeReports", projectName=project, databankName=bank,
                 strategies=",".join(names))["records"]
    sync(role, project, [bank])
    return before - after


def load(role: str, project: str, bank: str) -> int:
    """Make memory hold exactly the .sqx a fill just wrote into the databank's folder.

    A file written beside a live databank and never loaded is deleted by its next sync (hard
    rule 1), so the folder is copied aside, the databank cleared and refilled from the copy.
    A load that has not finished in 120 s raises BEFORE any sync and leaves the copy on disk.
    """
    folder = _top(role) / "user/projects" / project / "databanks" / bank
    want = len(list(folder.glob("*.sqx")))
    tmp = tempfile.mkdtemp(dir=tmp_dir())
    for f in folder.glob("*.sqx"):
        shutil.copy2(f, tmp)
    call(role, "loadFilesToDatabank", projectName=project, databankName=bank, folder=tmp,
         clear="true", all="true")
    for _ in range(600):
        got = records(role, project)[bank]
        if got == want:
            break
        time.sleep(0.2)
    if got != want:
        raise SystemExit(f"{bank}: {got} en memoria tras 120 s cargando {want} ficheros; no se "
                         f"sincroniza (un sync borraría los que faltan). Su copia queda en {tmp}")
    shutil.rmtree(tmp)
    sync(role, project, [bank])
    return got
