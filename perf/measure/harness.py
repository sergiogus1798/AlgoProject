"""Run a target in its own process, watch the whole tree's memory, and keep the median run."""

import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import TypedDict

from core.datapaths import tmp_dir
from core.paths import ROOT


class Measured(TypedDict):
    """What the runner reports for one target call."""

    wall_s: float
    cpu_s: float
    alloc_peak_mb: float | None
    alloc_top: list[str]
    self_rss_mb: float
    scale: int
    bytes_in_mb: float


class Run(Measured):
    """A measured run plus the tree-wide memory peak the harness saw."""

    rss_peak_mb: float


class Repeated(Run):
    """The median run plus how far apart the repeats sat."""

    wall_spread_pct: float
    repeats: int


def _pss_mb(pid: int) -> float:
    """Proportional set size of one process: shared pages divided among their sharers."""
    try:
        for line in (
            (Path("/proc") / str(pid) / "smaps_rollup")
            .read_text(encoding="utf-8")
            .splitlines()
        ):
            if line.startswith("Pss:"):
                return int(line.split()[1]) / 1024
    except OSError:  # exited between the listing and the read, or not ours to read
        pass
    return 0.0


def _tree_rss(root_pid: int) -> float:
    """Memory of one process and every descendant, as PSS.

    Args:
        root_pid: The process at the top of the tree.

    Returns:
        Megabytes. Summed RSS counts a page shared by forked workers once per worker (a 200 MB
        array under 4 children reads ~1 GB); PSS counts it once in total. Descendants are
        included because the expensive modules here spawn worker pools. Name kept: `rss_peak_mb`
        is the stored column, now PSS (figures restart on 2026-10-13).
    """
    kids = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            rest = (
                (entry / "stat").read_text(encoding="utf-8").rpartition(")")[2].split()
            )
        except OSError:
            continue
        kids.setdefault(int(rest[1]), []).append(int(entry.name))
    total, stack = 0.0, [root_pid]
    while stack:
        pid = stack.pop()
        total += _pss_mb(pid)
        stack.extend(kids.get(pid, []))
    return total


def once(
    target: str,
    overrides: list[str],
    cfg: dict,
    profile: Path | None = None,
    memtop: int = 0,
) -> Run:
    """One measured run of one target.

    Args:
        target: Target name as the registry spells it.
        overrides: Config overrides passed through to the runner.
        cfg: What config.load() returned.
        profile: Where to dump cProfile statistics, or None to skip profiling. Profiling
            costs roughly a third of the wall time, so a profiled run never enters history.
        memtop: How many allocation sites the runner should report back.

    Returns:
        What the runner reported plus `rss_peak_mb`, the tree-wide peak this process saw.
    """
    out = Path(tempfile.mkstemp(suffix=".json", dir=tmp_dir())[1])
    argv = [sys.executable, "-m", "perf.measure.runner", target, "--out", str(out)]
    argv += ["--profile", str(profile)] if profile else []
    argv += ["--memtop", str(memtop)] if memtop else []
    argv += [arg for o in overrides for arg in ("--set", o)]
    proc = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.DEVNULL)
    peak, deadline = 0.0, time.monotonic() + cfg["harness"]["timeout_s"]
    while proc.poll() is None:
        peak = max(peak, _tree_rss(proc.pid))
        if time.monotonic() > deadline:
            proc.kill()
            raise TimeoutError(f"{target} exceeded harness.timeout_s")
        time.sleep(cfg["harness"]["sample_ms"] / 1000)
    assert proc.returncode == 0, f"{target} failed with exit code {proc.returncode}"
    record = json.loads(out.read_text(encoding="utf-8"))
    out.unlink()
    return Run(**record, rss_peak_mb=peak)


def repeat(target: str, cfg: dict, overrides: list[str] | None = None) -> Repeated:
    """Run a target `harness.repeats` times and keep the middle one.

    Args:
        target: Target name.
        cfg: What config.load() returned.
        overrides: Config overrides passed to every repeat.

    Returns:
        The median run by wall time, carrying `wall_spread_pct` — how far the fastest and
        slowest runs sat apart. A measurement whose spread is wide says the machine was
        busy, and reading a 3% regression off it would be reading noise.
    """
    runs = [
        once(target, overrides or [], cfg) for _ in range(cfg["harness"]["repeats"])
    ]
    runs.sort(key=lambda r: r["wall_s"])
    middle = runs[len(runs) // 2]
    spread = (
        (runs[-1]["wall_s"] - runs[0]["wall_s"])
        / statistics.median([r["wall_s"] for r in runs])
        * 100
    )
    return Repeated(**middle, wall_spread_pct=spread, repeats=len(runs))
