---
q: Why does a script print its result and then exit 134 with «terminate called without an active exception»?
kw: Aborted (core dumped); exit 134; SIGABRT; terminate called without an active exception; pd.read_parquet; pyarrow 25.0.1; dataset scanner; thread pool; interpreter exit; teardown; flaky test; test_portfolio_ledger; load average; TODO OK then abort; set_cpu_count
tag: 🔬  date: 2026-10-05  see: eng/tests-are-scripts-run-via-audit-tests
---
# A short process that calls `pd.read_parquet` can abort at interpreter exit when the machine is loaded — its work is done, only the exit code lies
pyarrow 25.0.1, 96 cores: `pd.read_parquet` goes through Arrow's dataset scanner, which starts the CPU
thread pool; a process that exits while those threads are still starting dies in Arrow's teardown
(SIGABRT, no Python frame). 8-15 % of runs at ~96 concurrent processes, 0 of 10 on a quiet machine.
Everything printed before it is valid. It is not our code: no pool or handle of ours is open.
A caller that trusts the exit code (a test runner, the autopilot) must not read 134 after a complete output
as a failed run. The portfolio tests take `pa.set_cpu_count(1)` from `tests/portfolio_planted.py` (OPEN #104-5:
9 of 60 aborts before, 0 of 180 after); nothing central is changed — a project-wide choice (below).

## Evidence
- Reproduction, 96 copies at once: `import sys, pandas as pd; pd.read_parquet(sys.argv[1])` on a
  100-row file → 8, 14, 12 aborts of 96 (three rounds). `tests/test_portfolio_ledger.py`: 8 of 80, 9 of 60.
- `python3 -X faulthandler`: «Fatal Python error: Aborted … Thread … <no Python frame>» after `TODO OK`.
- What removes it: `pa.set_cpu_count(1)` before the read → 0 of 288; `pq.ParquetFile(path).read().to_pandas()`
  (no dataset scanner) → 0 of 288. What does not: `use_threads=False` (1 of 96), `pa.set_cpu_count(8)`
  (12 of 96), `pa.set_io_thread_count(1)` (6 of 96), `atexit.register(pa.set_cpu_count, 1)` (6 of 96).
  Writing a parquet alone, or importing `pyarrow.dataset` alone: 0 of 96.
- Cost of one CPU thread: `bars/USATEC_M1/M1.parquet` (87 MB, 4.2 M rows) read in 0.52 s against 0.27 s.
- 178 `read_parquet(` call sites in the repo, no shared reader.

## Counter-evidence
One machine, one pyarrow version; the native stack was not read (no gdb here) — «threads still
starting» is inferred from which settings remove it.
