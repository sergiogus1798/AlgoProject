"""The one way to run a child process: it always has a deadline, and a failure raises unless asked not to."""

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any


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
