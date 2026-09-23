"""Drive the headless worker install. The master's CLI is dead while its GUI is up."""

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
            the export and curation half is tied to Linux. See knowhow/07-practices.md.
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


def start(role: str = "conductor") -> None:
    """Start the worker as a daemon and sync bars from the master.

    Args:
        role: Which headless install to start.
    """
    require_posix()
    subprocess.run([str(WORKER_SH), "--role", role, "start"], check=True)


def stop(role: str = "conductor") -> None:
    """Stop the worker. Always call this when the job is done.

    Args:
        role: Which headless install to stop.
    """
    require_posix()
    subprocess.run([str(WORKER_SH), "--role", role, "stop"], check=True)


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
        Every PID whose command line names that folder. Writing to user/projects while
        one of these is alive is silently undone: SQX rewrites the file on save and exit.
    """
    found = []
    for d in PROC.iterdir():
        if not d.name.isdigit():
            continue
        cmdline = d / "cmdline"
        if cmdline.exists() and str(install) in cmdline.read_bytes().decode("utf-8", "replace"):
            found.append(int(d.name))
    return found
