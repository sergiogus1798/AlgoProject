"""Drive the headless worker install. The master's CLI is dead while its GUI is up."""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from time import sleep

from core.paths import WORKERS, WORKER_SH

PROC = Path("/proc")


def require_posix() -> None:
    """Refuse to drive SQX from a platform bin/sqx-worker.sh cannot run on.

    Raises:
        RuntimeError: On Windows. Everything that talks to StrategyQuant X goes
            through bin/sqx-worker.sh, which needs rsync, ss, curl and setsid. The
            analysis half of the project reads exported CSVs and runs anywhere; only
            the export and curation half is tied to Linux. See knowhow/eng/windows-portability.md.
    """
    if sys.platform.startswith("win"):
        raise RuntimeError(
            "Driving StrategyQuant X needs bin/sqx-worker.sh, which does not run on "
            "Windows. Export on the Linux machine; analyse the CSVs anywhere.")


def call(command: str, role: str = "conductor") -> str:
    """Send one sqcli command to the running worker.

    Args:
        command: An sqcli command line, e.g. "-databank action=count project=X name=Y".
        role: Which headless install to talk to. The conductor takes every short job; the
            custodian must receive no command between "start" and "collect", because a
            sync deletes on-disk .sqx it does not hold in memory.

    Returns:
        The server's response text. Only spaces are encoded: the server reads the rest of
        the query literally, so parentheses must NOT be percent-encoded.
    """
    port = WORKERS[role]["port"]
    url = f"http://localhost:{port}/call?cmd=" + command.replace(" ", "%20")
    return urllib.request.urlopen(url).read().decode()


def start(role: str = "conductor", owner: str | None = None) -> None:
    """Start the worker as a daemon and sync bars from the master.

    Args:
        role: Which headless install to start.
        owner: Who to record as the holder of `bin/sqx-worker.sh`'s owner lock (OPEN.md
            #32). None leaves it to the script's own default: `$CLAUDE_CODE_SESSION_ID`
            when set (inherited from this process' environment), else `$SQX_OWNER`, else
            "owner" — so every start here goes through the one lock the shell script owns,
            never a second implementation.
    """
    require_posix()
    cmd = [str(WORKER_SH), "--role", role]
    if owner:
        cmd += ["--owner", owner]
    subprocess.run([*cmd, "start"], check=True)


def stop(role: str = "conductor", export: bool = True, force: bool = False) -> None:
    """Stop the worker. Always call this when the job is done.

    Args:
        role: Which headless install to stop.
        export: Export the install's new databanks once it is down (`bin/sqx-worker.sh stop`
            runs `ui.daemon.loader.afterrun`); False inside an export's own start/stop, and on
            a cancel that must end fast.
        force: Stop it even if the owner lock says someone else holds it (`--force`). Only
            for a human who has checked that holder is gone — never set by default.
    """
    require_posix()
    env = None if export else {**os.environ, "ALGO_NO_EXPORT": "1"}
    cmd = [str(WORKER_SH), "--role", role]
    if force:
        cmd += ["--force"]
    subprocess.run([*cmd, "stop"], check=True, env=env)


def lock(install: Path) -> dict | None:
    """Read the owner lock `bin/sqx-worker.sh start` wrote for one install, read-only.

    Args:
        install: Top-level SQX folder, as `holding()` also takes — so a caller that already
            resolved a role to a path (and a test that points it at a scratch one) reads
            the same install it just probed for pids and the port.

    Returns:
        `{"holder", "pid", "since"}`, or None when nothing has locked it. Does not judge
        staleness (a dead PID with a down port): `busy()` callers already probe the port and
        `holding()` for that, and only `bin/sqx-worker.sh` itself clears a stale lock.
    """
    f = install / "user" / "log" / "OWNER"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except ValueError:
        return None


def wait_ready(project: str, databank: str, role: str = "conductor") -> int:
    """Block until the worker can actually see a databank's strategies.

    Args:
        project: Project name on the worker.
        databank: Databank name on the worker.
        role: Which headless install holds it.

    Returns:
        How many records it holds.

    Two separate asynchronous steps make this necessary: the port answers
    "Error: CLI not ready." for ~20 s, and loading strategies from files finishes later
    still. Exporting before this returns writes a header-only CSV with no error.
    """
    while True:
        reply = call(f"-databank action=count project={project} name={databank}", role)
        if "Records:" in reply:
            return int(reply.split("Records:")[1].split()[0])
        sleep(2)

def holding(install: Path) -> list[int]:
    """PIDs of StrategyQuant processes running out of one install.

    Args:
        install: Top-level SQX folder.

    Returns:
        Every PID whose executable lives in that folder — by absolute path, or relative
        (`./sqcli`, `./StrategyQuantX`) with the folder as working directory. Writing to
        user/projects while one of these is alive is silently undone: SQX rewrites the file
        on save and exit.

        🔬 2026-09-25: a worker's JVM runs as `./sqcli` from inside the install, so its
        command line names no folder at all, and this found nothing while the custodian
        held 16.5 GB -- the guard of hard rule 4 was open for every worker.
        🔬 2026-09-27: matching the folder anywhere in the command line took the nightly
        auditor (`claude -p`, whose prompt names the custodian) for a live SQX, and
        `execute --clear` refused for its whole run. Only the executable counts.
    """
    found = []
    for d in PROC.iterdir():
        if not d.name.isdigit():
            continue
        try:
            line = (d / "cmdline").read_bytes().decode("utf-8", "replace")
            here = (d / "cwd").resolve()
        except OSError:
            continue
        exe = line.split("\0")[0]
        if exe.startswith(str(install)) or (here == install.resolve() and not exe.startswith("/")):
            found.append(int(d.name))
    return found
