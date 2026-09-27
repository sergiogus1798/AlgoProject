"""The custodian's pulse: backtests done of total, JVM against its ceiling, CPU, free RAM — files only."""

import os
import re
import time
from datetime import datetime
from pathlib import Path

from core import worker
from core.paths import WORKERS
from ui.daemon import progress
from ui.daemon.jobs import LOGS

FREE_FLOOR_GB = 15          # owner, 2026-09-25: warn below this much MemAvailable
SLOPE_MB = 10               # middle of the 8–12 MB per retest measured on the 5,000-variant run
JVM_CEILING_SHARE = 0.9
FRESH_S = 900               # a job log older than this is not the run in progress
SILENT_S = 600              # a running project whose log is quiet this long is worth a look
CPU_SAMPLE_S = 0.5
DONE_OF = re.compile(r"^PROGRESS \d+ (\d+) de (\d+)")
XMX = re.compile(r"-Xmx(\d+)([gGmM])")
PSS = re.compile(r"^Pss:\s+(\d+) kB", re.M)
GB = 1024 ** 2              # kB in a GB

# In memory on purpose: the slope is a property of the run in progress, and a daemon that
# restarts has lost nothing a few more readings will not measure again.
READINGS: list[dict] = []


def xmx_gb(install: Path) -> float:
    """The heap ceiling an install was given.

    Args:
        install: Its top folder; `sqcli.config` holds the JVM options.

    Returns:
        `-Xmx` in GB.
    """
    m = XMX.search((install / "sqcli.config").read_text(encoding="utf-8"))
    return int(m.group(1)) / (1 if m.group(2) in "gG" else 1024)


def free_gb() -> float:
    """The machine's `MemAvailable`, in GB."""
    text = Path("/proc/meminfo").read_text()
    return int(re.search(r"MemAvailable:\s+(\d+) kB", text).group(1)) / GB


def pss_gb(pids: list[int]) -> float:
    """Proportional memory of these processes, summed.

    Args:
        pids: The install's processes.

    Returns:
        GB of PSS from `smaps_rollup`. PSS and not RSS: RSS counts the shared pages of every
        process that maps them, which overstates a JVM beside the others.
    """
    return sum(int(PSS.search(Path(f"/proc/{p}/smaps_rollup").read_text()).group(1))
               for p in pids) / GB


def cpu_ticks(pids: list[int]) -> int:
    """User plus system clock ticks these processes have used so far."""
    total = 0
    for p in pids:
        fields = Path(f"/proc/{p}/stat").read_text().rsplit(")", 1)[1].split()
        total += int(fields[11]) + int(fields[12])
    return total


def cpu_pct(pids: list[int]) -> float:
    """CPU use over a short sample, in top's units (100 = one core)."""
    before, t0 = cpu_ticks(pids), time.monotonic()
    time.sleep(CPU_SAMPLE_S)
    spent = cpu_ticks(pids) - before
    return spent / os.sysconf("SC_CLK_TCK") / (time.monotonic() - t0) * 100


def job_progress(folder: Path, now: float) -> dict | None:
    """The last `PROGRESS n de N` a recent daemon job printed.

    Args:
        folder: Where the daemon's jobs log.
        now: Epoch seconds.

    Returns:
        `done`, `total` and `log` (its file name) from the newest log touched within
        `FRESH_S`, or None. `sqx.variants.execute` prints these; SQX's own log carries no count.
    """
    fresh = [f for f in folder.glob("*.log") if now - f.stat().st_mtime < FRESH_S]
    for f in sorted(fresh, key=lambda f: f.stat().st_mtime, reverse=True):
        for line in reversed(f.read_text(encoding="utf-8", errors="replace").splitlines()):
            m = DONE_OF.match(line)
            if m:
                return {"done": int(m.group(1)), "total": int(m.group(2)), "log": f.name}
    return None


def project_start(lines: list[str]) -> tuple[str | None, datetime | None]:
    """The last project started in today's log, and when.

    Args:
        lines: The tail of today's SQX log.

    Returns:
        Its name and its start as a datetime today, or (None, None).
    """
    for line in reversed(lines):
        m = progress.STARTING.search(line)
        if m:
            clock = datetime.strptime(line[:8], "%H:%M:%S").time()
            return m.group(1), datetime.combine(datetime.now().date(), clock)
    return None, None


def slope_mb(project: str, done: int | None, jvm: float) -> tuple[float, bool]:
    """MB the JVM grows per backtest, measured over this run's readings when it can be.

    Args:
        project: The running project; readings of another one are dropped.
        done: Backtests done now, or None when no count is known.
        jvm: JVM PSS now, GB.

    Returns:
        The slope and whether it was measured (True) or is the `SLOPE_MB` assumption.
    """
    if READINGS and READINGS[0]["project"] != project:
        READINGS.clear()
    if done is not None:
        READINGS.append({"project": project, "done": done, "jvm": jvm})
    first, last = (READINGS[0], READINGS[-1]) if READINGS else (None, None)
    if first and last["done"] - first["done"] >= 100 and last["jvm"] > first["jvm"]:
        return (last["jvm"] - first["jvm"]) * 1024 / (last["done"] - first["done"]), True
    return SLOPE_MB, False


def warnings(p: dict) -> list[str]:
    """What in one reading deserves colour.

    Args:
        p: A pulse as `custodian` builds it.

    Returns:
        Spanish sentences, empty when all is well.
    """
    out = []
    if p["free_gb"] < FREE_FLOOR_GB:
        out.append(f"RAM libre {p['free_gb']:.0f} GB: por debajo de {FREE_FLOOR_GB} GB")
    if not p["up"]:
        return out
    if p["jvm_gb"] >= JVM_CEILING_SHARE * p["xmx_gb"]:
        out.append(f"JVM al {p['jvm_gb'] / p['xmx_gb']:.0%} de su techo -Xmx{p['xmx_gb']:.0f}g")
    left = p["total"] - p["done"] if p["total"] is not None else None
    if left and p["fits_more"] < left:
        out.append(f"a {p['slope_mb']:.1f} MB por backtest caben {p['fits_more']} y faltan {left}")
    if p["log_silent_s"] is not None and p["log_silent_s"] > SILENT_S:
        out.append(f"el log de SQX lleva {p['log_silent_s'] // 60} min sin escribir")
    return out


def line(p: dict, now: datetime) -> str:
    """The one line the owner reads, in the format he chose on 2026-09-25.

    Args:
        p: A pulse as `custodian` builds it.
        now: The reading's time.

    Returns:
        `13:38:32 3987 de 15000 | JVM 63.2 GB | CPU 6845% | libre 55 GB | caben 900 más`.
    """
    clock = f"{now:%H:%M:%S}"
    if not p["up"]:
        return f"{clock} custodio parado | libre {p['free_gb']:.0f} GB"
    count = f"{p['done']} de {p['total']}" if p["total"] is not None else "avance ?"
    return (f"{clock} {count} | JVM {p['jvm_gb']:.1f} GB | CPU {p['cpu_pct']:.0f}% | "
            f"libre {p['free_gb']:.0f} GB | caben {p['fits_more']} más")


def custodian() -> dict:
    """Everything the pulse line says about the custodian, read from /proc and files only.

    Returns:
        The `/api/pulse` `custodian` block (ui/README.md). Never a command to the install:
        between start and collect it receives nothing but `action=status` (CLAUDE.md rule 3),
        and not even that from here.
    """
    now = datetime.now()
    base = {"up": False, "project": None, "task": None, "done": None, "total": None,
            "rate_per_min": None, "eta_min": None, "jvm_gb": None, "xmx_gb": None,
            "cpu_pct": None, "free_gb": free_gb(), "fits_more": None, "slope_mb": None,
            "slope_measured": False, "progress_from": None, "log_silent_s": None}
    if "custodian" not in WORKERS:
        return base | {"line": f"{now:%H:%M:%S} esta máquina no declara custodio", "warn": []}
    install = WORKERS["custodian"]["path"]
    pids = worker.holding(install)
    p = base | {"xmx_gb": xmx_gb(install), "up": bool(pids)}
    if pids:
        lines, mtime = progress.log_lines(install)
        run = progress.run_state(lines)
        project, started = project_start(lines)
        got = job_progress(LOGS, now.timestamp()) if not run["finished"] else None
        jvm = pss_gb(pids)
        slope, measured = slope_mb(project or "", got["done"] if got else None, jvm)
        p |= {"project": project, "task": run["current"], "jvm_gb": jvm,
              "cpu_pct": cpu_pct(pids), "slope_mb": slope, "slope_measured": measured,
              "fits_more": max(0, int(min(p["xmx_gb"] - jvm, p["free_gb"]) * 1024 / slope)),
              "log_silent_s": None if run["finished"] or not mtime
              else round(now.timestamp() - mtime)}
        if got:
            minutes = (now - started).total_seconds() / 60 if started else None
            rate = got["done"] / minutes if minutes else None
            p |= {"done": got["done"], "total": got["total"], "progress_from": got["log"],
                  "rate_per_min": rate,
                  "eta_min": (got["total"] - got["done"]) / rate if rate else None}
    return p | {"line": line(p, now), "warn": warnings(p)}
