---
q: progress bar percent window jobs strip PROGRESS line, SQX task progress, custodian pulse avance ?, run started from terminal no count, Strategies generated action=status, build no total, profitShape stuck at 0 %
tag: 🔬  date: 2026-09-28  see: eng/stale-ui-daemon
---
# Where every progress figure of the window comes from — and which runs have none
- **A Python job's bar** is its last `PROGRESS <0-100> <state>` stdout line (`ui/daemon/jobs.py`); 100 once it exits 0. A study that never prints one (`profitShape`) sits at **0 % until it ends** — not stuck.
- **An SQX task's bar**: SQX's own percent exists only in the compute-thread name of walk-forward tasks (`progress.PERCENT`); otherwise done ÷ total from the worker's status line (`Strategies generated`) over the task's input databank. **A build has no total**: indeterminate bar.
- **The custodian pulse's whole-run count** exists only for window jobs that print `PROGRESS n de N` (`sqx.variants.execute`). A run started from a terminal gets the running **task**'s count from `-project action=status` — no rate, no ETA (OPEN §55).
- The status line is asked only while the install's log says a project runs; the master is never asked.

## Evidence
- 🔬 2026-09-28, daemon on :8777: `POST /api/workflow/run` profitShape × 3 on `Test_USDJPY_donchianUpperCrossUp_M30/OOS` → `/api/jobs` percent 0,0,0 for ~9 s, then 100 «terminado»; its log holds no PROGRESS line. isOos printed only `1 leyendo` → `100 hecho`; gate printed `5 200 emparejadas…` then `mono i/160` lines.
- `ui/daemon/ops/runs.py` `count()`, `ui/daemon/ops/pulse.py` `custodian()`; checked with fakes: `7 de 20 … estado del custodio · MCR 3` and, for a build, `140 hechos`.
