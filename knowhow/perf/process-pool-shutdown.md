---
q: orphan forkserver processes, ProcessPoolExecutor never shut down, _POOL global, leaked workers memory, resource_tracker, kill orphans
tag: 🔬  date: 2026-09-19  see: eng/practices-that-bit, perf/python-parallelism
---
# A global pool without shutdown survives its parent: find and kill orphan forkservers by PID
If the parent dies without unwinding (hard Ctrl-C, `kill -9`, Flask panel closed from the terminal), the `forkserver` and its
workers are reparented to systemd and live forever, surviving panel restarts. Kill by PID (children first) the `forkserver` whose PPID is 1. Never `pkill -f python3`.
```bash
ps -eo pid,ppid,etime,rss,cmd | grep -E 'forkserver|resource_tracker' | grep -v grep
```

## Evidence
`strategies/monteCarlo/simulate/engine.py` kept the pool in `_POOL`, no `shutdown()` or `atexit` anywhere in the repo.
Found 68 orphans holding 8.9–9.4 GB (two readings), one nine days old with the pre-reorganisation module path (`strategies.monteCarlo.engine`).
