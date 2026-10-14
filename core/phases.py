"""Wall clock of a named sub-phase, appended to the CSV `ALGO_PHASES` names; nothing without it."""

import contextlib
import csv
import os
import time
from collections.abc import Iterator

ENV = "ALGO_PHASES"
COLUMNS = ("began", "seconds", "phase", "detail", "pid")


def row(name: str, detail: str, seconds: float) -> None:
    """Append one row for a block that has just ended and lasted `seconds`."""
    path = os.environ.get(ENV)
    if path:
        with open(path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [
                    f"{time.time() - seconds:.3f}",
                    f"{seconds:.3f}",
                    name,
                    detail,
                    os.getpid(),
                ]
            )


def note(name: str, detail: str) -> None:
    """Append a zero-duration row: an event, not a block (`fallback`: the fast route was refused)."""
    row(name, detail, 0.0)


@contextlib.contextmanager
def phase(name: str, detail: str = "") -> Iterator[None]:
    """Time the block and append one row; phases nest, and subprocesses inherit the file.

    Args:
        name: What the block is — `sqx`, `start`, `stop`, `export`, `sync`, `snapshot`…
        detail: Which one (a task, a databank, a study).
    """
    began = time.monotonic()
    try:
        yield
    finally:
        row(name, detail, time.monotonic() - began)
