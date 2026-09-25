---
q: how long does each workflow step take, MC Retest share of SQX time, MCR 7 OHLC MCR 8 Stress, crossmarket.report bottleneck, retest.ingest memory, custodian stop start cost, startOnlyTask
tag: 🔬  date: 2026-09-24  see: perf/python-parallelism, perf/smt-in-sqx-retest
---
# MC Retest is ~89 % of the chain's SQX time; crossmarket.report the only Python bottleneck
Full table: `docs/manual/12-rendimiento.md`. Measure `retest.ingest` memory before a big run (scales with runs × sims).
Stop+start of the custodian costs ~39 s per stage (screening between steps pays it; `startOnlyTask` runs nothing on this install).

## Evidence
📓 Custodian log + `/usr/bin/time`, full run steps 1→16.5, USDJPY H1.
- MC Retest 1,955 s of 2,202; `MCR 7 OHLC` 695 s + `MCR 8 Stress` 1,022 s = 88 % of it. Measured with FIVE active tasks; seven configured now → more.
- `crossmarket.report`: 13 min at 2,000 draws, > 50 min unfinished at config's 10,000 (8 strategies × 9 markets, one core, before parallelisation — `perf/python-parallelism`). Rest of Python: seconds.
- `retest.ingest` peaks 3.2 GB with 36 runs × 1,000 sims; 800 runs → ~70 GB if proportional.
- Custodian cycle ~39 s, 21.5 s is the CLI answering long after the port does.
- ⚠️ Unmeasured: steps 17, 18, 19 and the variant-batch retest feeding them (likely the costliest: 240 variants × 3 windows × 9 markets).
