---
q: Where does step 16.5's wall time go on the restart route, and what does the Python side cost?
kw: step 16.5 time split, Fase 4 run, 6138 s, boot 259 s, pilot session 244 s, marketSurfaces 575 s, blind.py parallel mothers, falsePositives many.py fanout, core.fanout
tag: 🔬  date: 2026-10-05  see: perf/variants-batch-size-and-flush, perf/autopilot-dead-time, perf/workflow-step-durations
---
# Step 16.5 (restart route): SQX computing is only 60 % of the wall time; boot, loads and exports are the rest
Fase 4 run, 10 mothers, 20 SQX sessions, 6,138 s: computing 3,670 s (IS 1,889, OOS1 1,116, OOS2 654) · boot 259 · CLI-ready→start
(loads, clears, fixed sleeps) 708 · `Project finished`→Exit app (exports, flush, stop) 1,162 · Python between sessions 339.
Per mother: pilot session 244 s (152 computing), batch session 336 s (215 computing).

## Evidence
🔬 `Test_NIKKEI225_M30_simpleL_auto`, custodian `SQX_w2`, 2026-10-05 (SQX log timestamps).
- Python: step 18.5 (marketSurfaces) ran 10 mothers serially, 575 s; `pipeline/autopilot/blind.py` now runs a blind study's mothers
  at once (not yet timed). `studies/screening/falsePositives/many.py` fans out donors with `core.fanout` (commit ebfbed9): same
  frame, same seed, 10 donors 0.3 s against 1.8 s; it was 192 s of step 8's 289 s for 1,000 donors.
