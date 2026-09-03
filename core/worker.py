"""Drive the headless worker install. The master's CLI is dead while its GUI is up."""

import subprocess
import urllib.request
from time import sleep

from core.paths import WORKER_PORT, WORKER_SH


def call(command: str) -> str:
    """Send one sqcli command to the running worker.

    Args:
        command: An sqcli command line, e.g. "-databank action=count project=X name=Y".

    Returns:
        The server's response text. Only spaces are encoded: the server reads the rest of
        the query literally, so parentheses must NOT be percent-encoded.
    """
    url = f"http://localhost:{WORKER_PORT}/call?cmd=" + command.replace(" ", "%20")
    return urllib.request.urlopen(url).read().decode()


def start() -> None:
    """Start the worker as a daemon and sync bars from the master."""
    subprocess.run([str(WORKER_SH), "start"], check=True)


def stop() -> None:
    """Stop the worker. Always call this when the job is done."""
    subprocess.run([str(WORKER_SH), "stop"], check=True)


def wait_ready(project: str, databank: str) -> int:
    """Block until the worker can actually see a databank's strategies.

    Args:
        project: Project name on the worker.
        databank: Databank name on the worker.

    Returns:
        How many records it holds.

    Two separate asynchronous steps make this necessary: the port answers
    "Error: CLI not ready." for ~20 s, and loading strategies from files finishes later
    still. Exporting before this returns writes a header-only CSV with no error.
    """
    while True:
        reply = call(f"-databank action=count project={project} name={databank}")
        if "Records:" in reply:
            return int(reply.split("Records:")[1].split()[0])
        sleep(2)
