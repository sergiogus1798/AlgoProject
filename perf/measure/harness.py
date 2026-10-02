"""Run a target in its own process, watch the whole tree's memory, and keep the median run."""

import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from core.datapaths import tmp_dir
from core.paths import ROOT

PAGE_MB = 4096 / (1024 * 1024)


def _tree_rss(root_pid: int) -> float:
    """Resident memory of one process and every descendant.

    Args:
        root_pid: The process at the top of the tree.

    Returns:
        Megabytes. Descendants are included because the expensive modules here spawn worker
        pools, and `ru_maxrss` of the children reports the largest single child rather than
        their sum. A process that exits between the listing and the read is normal, not an
        error, so it is skipped.
    """
    rss, kids = {}, {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            rest = (entry / "stat").read_text(encoding="utf-8").rpartition(")")[2].split()
        except OSError:
            continue
        pid = int(entry.name)
        kids.setdefault(int(rest[1]), []).append(pid)
        rss[pid] = int(rest[21]) * PAGE_MB
    total, stack = 0.0, [root_pid]
    while stack:
        pid = stack.pop()
        total += rss.get(pid, 0.0)
        stack.extend(kids.get(pid, []))
    return total


def once(target: str, overrides: list[str], cfg: dict,
         profile: Path | None = None, memtop: int = 0) -> dict:
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
    return record | {"rss_peak_mb": peak}


def repeat(target: str, cfg: dict, overrides: list[str] | None = None) -> dict:
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
    runs = [once(target, overrides or [], cfg) for _ in range(cfg["harness"]["repeats"])]
    runs.sort(key=lambda r: r["wall_s"])
    middle = runs[len(runs) // 2]
    spread = (runs[-1]["wall_s"] - runs[0]["wall_s"]) / statistics.median(
        [r["wall_s"] for r in runs]) * 100
    return middle | {"wall_spread_pct": spread, "repeats": len(runs)}
