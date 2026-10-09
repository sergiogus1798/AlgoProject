"""Stop a GUI session with a task still running: ask it to exit, let every other project save, then kill by PID."""

import contextlib
import os
import re
import signal
import time
import urllib.request

from core import worker
from core.paths import WORKERS
from sqx.projects import live

SAVED = re.compile(r"Databank '([^/']+)/([^']+)' saved .* Sync triggered by 'Save all strategies before exiting")
PATIENCE = 15 * 60     # s the other projects' saves may take; past it nothing is killed and the script waits
GRACE, LAST = 10, 30   # s after the last save before the kill; s SIGTERM gets before SIGKILL


def banks(role: str, running: str) -> set[tuple[str, str]]:
    """(project, databank) pairs with strategies on disk, the running project's aside: what the exit saves."""
    root = WORKERS[role]["path"] / "user/projects"
    return {(p.name, b.name) for p in root.iterdir() if p.name != running
            for b in (p / "databanks").glob("*") if any(b.glob("*.sqx"))}


def stop(role: str, running: str) -> str:
    """Exit the session with `running` mid-task; one line saying how it went down.

    `/main/exitapp` makes SQX save every project's databanks while the running task goes on
    at full CPU to its own end — a build to its time-limit (🔬 2026-10-06: 15 min, 180 in a
    real run) — so the owner's stop freed nothing. Owner, 2026-10-06: once every other
    project's databank on disk has been saved again, the JVM is killed by PID; what the
    running project held only in memory is lost and its step is run again on resume.
    A databank never synced (no file on disk) is not waited for: `# ponytail:` the exit saves
    it too, and a kill while it writes leaves it partial — none of a finished project's are.
    """
    top, log = WORKERS[role]["path"], live.mark(role)
    port, token = live._setting(role, "WebServerPortUsed"), live._setting(role, "BrowserToken")
    urllib.request.urlopen(urllib.request.Request(f"http://localhost:{port}/main/exitapp",
                                                  headers={"browserToken": token}), timeout=30).read()
    pending, began = banks(role, running), time.monotonic()
    while pending and worker.holding(top) and time.monotonic() - began < PATIENCE:
        time.sleep(2)
        with open(log[0], "rb") as f:
            f.seek(log[1])
            pending -= {m.groups() for m in SAVED.finditer(f.read().decode("utf-8", "replace"))}
    pids = worker.holding(top)
    if not pids:
        return f"{role}: salió solo en {time.monotonic() - began:.0f} s"
    if pending:
        return (f"{role}: {len(pending)} databank(s) de otros proyectos sin guardar tras {PATIENCE // 60} "
                f"min ({sorted(pending)[:3]}…): no se mata, se espera a que salga")
    time.sleep(GRACE)
    for pid in pids:
        with contextlib.suppress(ProcessLookupError):   # it exited during GRACE (🔬 2026-10-06)
            os.kill(pid, signal.SIGTERM)
    for _ in range(LAST):
        if not worker.holding(top):
            break
        time.sleep(1)
    for pid in worker.holding(top):
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
    return (f"{role}: los demás proyectos guardados en {time.monotonic() - began:.0f} s; «{running}» "
            f"seguía con su tarea y se mató por PID {pids} (su memoria se pierde, el paso se repite)")
