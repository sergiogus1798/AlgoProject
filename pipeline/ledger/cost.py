"""What a stage cost: wall time, the RAM of both process trees, and the bytes it left behind."""

import subprocess
import threading
import time
from pathlib import Path

MB = 1 << 20
# The JVM SQX runs in is a separate process tree that this pipeline never owns, so its
# memory cannot be read off getrusage: it has to be sampled from the outside while the
# stage runs. Matched on the launcher name, never on a pattern that could match our shell.
SQX = "sqcli"


def _rss_mb(pattern: str) -> float:
    """Resident memory of every process whose command line matches, in MB.

    Args:
        pattern: What to look for in the command line.

    Returns:
        The sum, or 0.0 when nothing matches. `ps` rather than /proc so that a process
        exiting mid-scan is ps's problem and not a traceback here.
    """
    out = subprocess.run(["ps", "-eo", "rss,args"], capture_output=True, text=True).stdout
    total = sum(int(line.split(maxsplit=1)[0])
                for line in out.splitlines()[1:]
                if pattern in line and "ps -eo" not in line)
    return total / 1024


def bytes_of(where: Path) -> int:
    """Total size of a directory tree.

    Args:
        where: Directory; need not exist.

    Returns:
        Bytes in every file below it, 0 when it is not there yet.
    """
    if not where.exists():
        return 0
    return sum(p.stat().st_size for p in where.rglob("*") if p.is_file())


class Watch:
    """Samples both process trees' memory for as long as a stage runs.

    A stage is a subprocess that in turn drives a JVM, so there are two peaks worth
    knowing and neither is visible from inside this process. Sampling is the only way,
    and a peak is the only summary worth keeping: the mean of a run that spends four
    minutes idle and twenty seconds at 40 GB says nothing useful.
    """

    def __init__(self, work: Path, every: float = 2.0) -> None:
        """Set up a watch over one work directory.

        Args:
            work: The strategy's work directory, measured before and after.
            every: Seconds between samples.
        """
        self.work, self.every = work, every
        self.stop = threading.Event()
        self.peak_sqx = self.peak_py = 0.0
        self.started = self.bytes_before = 0

    def _loop(self) -> None:
        """Sample until told to stop."""
        while not self.stop.wait(self.every):
            self.peak_sqx = max(self.peak_sqx, _rss_mb(SQX))
            self.peak_py = max(self.peak_py, _rss_mb("python3 -m"))

    def __enter__(self) -> "Watch":
        """Start the clock and the sampler.

        Returns:
            Itself, so the caller can read the result after the block.
        """
        self.started = time.perf_counter()
        self.bytes_before = bytes_of(self.work)
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_) -> None:
        """Stop sampling. Exceptions are not swallowed."""
        self.stop.set()
        self.thread.join(timeout=self.every * 2)

    def result(self) -> dict:
        """What the stage cost.

        Returns:
            Wall seconds, the peak RSS of each tree in MB, and how many bytes the work
            directory grew by. A negative delta is a stage that deleted more than it
            wrote, which is what the cleanup step is supposed to do.
        """
        return {"wall_s": round(time.perf_counter() - self.started, 2),
                "rss_sqx_mb": round(self.peak_sqx),
                "rss_py_mb": round(self.peak_py),
                "bytes_delta": bytes_of(self.work) - self.bytes_before}
