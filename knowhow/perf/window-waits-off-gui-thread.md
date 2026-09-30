---
q: why does the desktop window freeze while Python analyses run, ui lag, GUI thread, one process per strategy, idle cores in a population run
tag: 🔬  date: 2026-09-28  see: python-parallelism, ram-budget
---
# The window froze on its own reloads, not on data: never wait on the daemon from the GUI thread
Every daemon call a timer or a finished job triggers goes through `ui/desktop/background.py`
(answer lands on the GUI thread); a batch of ended jobs is repainted once, at most every 20 s
(`railwatch.REPAINT_S`). A population run of a one-strategy study is ONE `batchrun` job forking
over physical cores − 4 at `nice 10`, not one process per strategy.

## Evidence
Test_USDJPY_donchianUpperCrossUp_M30, 200 strategies, scratch daemon, offscreen window
(`scratchpad/lag.py`: a 50 ms QTimer, gaps recorded).
- Before: `panel.refresh` 3.4 s, `funnel.load` 0.6 s, `rail.load` 1.2 s, all `recv()` on the
  GUI thread (cProfile); `rail.poll` emitted `finished` per ended job → 16 × ~4 s ≈ 1 min frozen.
  `/api/databank/table` itself: 0.1-0.3 s. Opening the project: 4.4 s blocked.
- Before: profitShape "population" = 207 jobs, LIGHT weight 3 → 16 at once; one job ≈ 1 s, of
  which 0.7 s is importing pandas + the study (`-X importtime`) and the rest re-reading the 12 MB
  trades parquet. 207 jobs: 43 s (log mtimes 19:33:30 → 19:34:13).
- After: fill returns in 0.006 s; 200 strategies in one batch of 44 workers: ~9 s; worst event-loop
  gap during the batch 320 ms (once), p99 182 ms.
