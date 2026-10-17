"""The one way to run a child process: it always has a deadline, and a failure raises unless asked not to."""

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from core.paths import ROOT

CHILDREN: set[subprocess.Popen] = (
    set()
)  # the `command`s running now, for a cancel to kill


def run(
    cmd: str | Sequence[str | Path],
    *,
    timeout: float,
    check: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """`subprocess.run` with the timeout a required keyword.

    Args:
        cmd: The command, as for `subprocess.run`.
        timeout: Seconds before the child is killed and `subprocess.TimeoutExpired` raised.
        check: Raise `subprocess.CalledProcessError` on a non-zero exit.
        **kwargs: Passed through (`capture_output`, `text`, `cwd`, `env`, `input`…).
    """
    return subprocess.run(cmd, timeout=timeout, check=check, **kwargs)


def command(argv: list[str], tail: int = 4) -> tuple[int, str]:
    """Run one `python3 -m …` to its end; its return code and the tail of what it printed.
    Held in `CHILDREN` while it runs, so a cancel can end it at once.

    Args:
        argv: The arguments after the interpreter.
        tail: How many lines of its output to keep.
    """
    child = subprocess.Popen(
        [sys.executable, *argv],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    CHILDREN.add(child)
    try:
        out, _ = child.communicate()
    finally:
        CHILDREN.discard(child)
    return child.returncode, " / ".join(out.strip().splitlines()[-tail:])
