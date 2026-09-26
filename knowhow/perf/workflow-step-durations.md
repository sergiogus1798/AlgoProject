---
q: how long does each workflow step take, MC Retest share of SQX time, MCR 7 OHLC MCR 8 Stress, crossmarket.report bottleneck, retest.ingest memory, custodian stop start cost, startOnlyTask, WFC per-mother cost, WFM duration, crossmarket.report parallel speed
tag: 🔬  date: 2026-09-26  see: perf/python-parallelism, perf/smt-in-sqx-retest
---
# MC Retest is the single biggest SQX cost; WFC's per-mother cost is FIXED (market loading) until the population is large enough to shift it
Full table: `docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento). Measure `retest.ingest` memory before a big run (scales
with runs × sims). Stop+start of the custodian costs ~39 s per stage (screening between steps pays
it; `startOnlyTask` runs nothing on this install).

## Evidence
📓 Custodian log + `/usr/bin/time`. Two runs: 24-09 (steps 1→16.5, 5 of 8 MCR tasks active, 240
variants) and 26-09 (`USDJPY_workflow_profiling_v1`, all 25 steps touched, 7 of 8 MCR tasks, WFC on
1,093-4,999-variant batches, full WFM). The 24-09 card's "unmeasured: 17, 18, 19" is now measured.

- **MC Retest, all 7 configured tasks (MinDist excluded — market entries): 2,580 s.** `MCR 7 OHLC`
  709.7 s + `MCR 8 Stress` 1,030.2 s = 1,740 s, **67 % of the 7-task total** — lower than the 88 % the
  24-09 card measured with only 5 tasks active, because the other tasks now share more of the total,
  not because OHLC/Stress got relatively cheaper. `MCR 2 Spread` 260.1 s, `MCR 3 Slippage` 268.9 s,
  `MCR 6 Exits` 261.5 s, `MCR 1 Bar` 28.1 s, `MCR 5 Params` 21.3 s — for 8 strategies.
- **`crossmarket.report` is fast in wall time once parallel: 28.7 s wall, but 555.0 s of CPU
  (19.3×)** on 8 strategies × 9 markets. The 24-09 estimate (13 min at 2,000 draws, single core,
  before `perf/python-parallelism`) was the *pre-parallel* cost; this is the same study, parallelised,
  on a comparable population — CPU-time-per-unit-of-work did not drop, wall time did.
- **A WFC leg's cost is dominated by loading the 9 cross-check markets, not by the number of
  variants, until the population gets large.** Two mothers, 1,093 and 1,457 variants: `WFC 1 IS`
  350.0 s and 352.0 s (**same**, 1.3 % apart), `WFC 2 OOS1` 176.5 s / 176.8 s, `WFC 3 OOS2` 128.8 s /
  129.0 s — three legs, ~657 s total, for either size. A third mother at 4,999 variants started
  scaling with population (extrapolated ~19 min for `WFC 1 IS` alone from its early rate, vs. 350 s
  for the smaller ones) — the fixed cost stops dominating somewhere between ~1,500 and ~5,000
  variants for a 9-market family. A 12-variant batch (the structural step's ablations) took only
  132 s for all three legs — confirms the floor is the market loading, not a per-variant constant.
- **WFM (30 cells: 6 `runs` × 5 `oos_pct`, 5,000 tests/step, precision 2) took 675 s for 3 strategies
  run together**, with **zero progress signal** from SQX until the whole task finishes (`Running time
  so far` stays `0 ms`, the databank count stays flat) — do not read a flat status as a hang; check
  `ps` CPU time on the `sqcli` process instead.
- `retest.ingest` peaks 3.2 GB with 36 runs × 1,000 sims; 800 runs → ~70 GB if proportional
  (unconfirmed at that scale).
- Custodian cycle ~39 s, 21.5 s is the CLI answering long after the port does.
- SPP: `SPP IS` 161.1 s + `SPP OOS` 82.7 s = 244 s for 8 strategies, tope 15,000 permutations/strategy.
- 🤤 Still unmeasured: CSCV/WFC/WFM at population sizes past ~5,000 variants, and the WFM's own cost
  curve as a function of `MaxTests`/steps/cells — only ever measured at the doctrine's own 5,000/30.
