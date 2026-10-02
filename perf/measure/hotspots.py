"""Where one target's time and memory actually go: the functions and the allocation sites."""

import pstats
import tempfile
from pathlib import Path

from core.datapaths import tmp_dir
from perf.measure import harness

SITES = 12


def profile(target: str, cfg: dict, top: int = SITES) -> dict:
    """Profile one target once and read back what dominated it.

    Args:
        target: Target name as the registry spells it.
        cfg: What config.load() returned.
        top: How many functions and allocation sites to report.

    Returns:
        `time`, the functions ranked by time spent in their own body, and `memory`, the
        lines that held the most bytes at the peak. Own time rather than cumulative: the
        cumulative ranking always puts `main` first and says nothing.
    """
    dump = Path(tempfile.mkstemp(suffix=".prof", dir=tmp_dir())[1])
    run = harness.once(target, [], cfg, profile=dump, memtop=top)
    stats = pstats.Stats(str(dump))
    rows = sorted(stats.stats.items(), key=lambda kv: kv[1][2], reverse=True)[:top]
    dump.unlink()
    return {"target": target, "wall_s": run["wall_s"], "memory": run["alloc_top"],
            "time": [{"where": f"{Path(f).name}:{line}({name})", "own_s": v[2],
                      "calls": v[0], "share": v[2] / run["wall_s"]}
                     for (f, line, name), v in rows]}


def text(found: dict) -> str:
    """The profile as a table a report can paste.

    Args:
        found: What profile() returned.

    Returns:
        Two blocks, time first. The share column is of the profiled run's wall time, which
        is longer than an unprofiled one -- read the ranking, not the seconds.
    """
    lines = [f"{found['target']} — {found['wall_s']:.2f} s profiled", "", "TIME (own)"]
    lines += [f"  {r['share']:6.1%}  {r['own_s']:8.3f} s  {r['calls']:>9,}x  {r['where']}"
              for r in found["time"]]
    return "\n".join(lines + ["", "MEMORY (held at peak)"] + [f"  {s}" for s in found["memory"]])
