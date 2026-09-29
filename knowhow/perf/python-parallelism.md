---
q: parallelise our Python, how many processes / workers, fork copy-on-write, crossmarket cost per trade, gate cost ATR cache, memory limit stress.py degraded, chunked Monte Carlo exact, filter after compute, count trades before launching, pool.map no progress, PSS vs RSS fork pool
tag: 🔬  date: 2026-09-27  see: perf/monte-carlo-bandwidth, perf/numba-division, perf/yaml-parsing-cost, perf/measuring-project-cost
---
# Parallelise per (strategy, market) with fork, 48 processes after numba; the unit of cost is the trade
- After numba: 48 processes (physical cores), never `os.cpu_count()`; more is slower. `core.fanout` caps every pool at `CORES` (psutil, physical) since 2026-09-26. A pool's RAM is workers × what ONE task holds: cap a module below 48 when its task retains a lot (`export_spp` 16, `mcRetest.report` 16, `tradepack` 8).
- A worker's peak is draws × trades laid out at once, not the data: lay out (draws, trades) matrices by row blocks with the rng drawn up front (`engines/nulls/placement/bootstrap.block_rows`), and cap draws × trades per batch (`nulls.batch_cells`). Only `block_shift` gives the same draws whatever the batch; the other three null models do not.
- `fork`: parent reads export and bars once, children inherit copy-on-write; children return only the verdict row, never the whole `analyse_strategy` record.
- Count trades before launching anything: cost is per trade (strategies in one batch span ×900). Task = (strategy, market), not strategy (longest strategy floors the wall) — in a study's one-strategy path too, not only the batch.
- Chunk a Monte Carlo exactly: draw whole and in the same order (`rng.random((n, k))` by consecutive row blocks = same stream; A,B,C per block ≠ all A, all B, all C).
- Compute only what is asked: look for `{k: all[k] for k in names}` patterns. Pool memory with `fork` = sum of PSS (`/proc/<pid>/smaps_rollup`), not RSS; `/usr/bin/time %M` = largest process only.
Full tables: `docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento).

## Evidence
`PerfUSDJPY_Python_v1`, 500 USDJPY H1 strategies, 96-core box.
- `crossmarket.report` ≈ `(3.36 + 0.00168 × draws)` ms/trade/core, single-core; `np.add.at` →
  `np.bincount` only 1.6–2.5×; `_losing_run` already vectorised.
- Per strategy, 8 strategies: 5,338–43,109 foreign-market trades; step 8 costliest/cheapest 83.4× (r = 0.982 time vs trades).
- Gate: 60 ms/strategy marginal, 500 in 32 s; 88 % is the monkey (28 % recomputing ATR per
  strategy, 13 % filtering trades by an `object` column). Cached ATR + grouping by identity + fork:
  `studies.screening.gate.report` 31.1 → 6.1 s, 500×29 `scorecard` identical.
- `engines/nulls/stats.py:measure()` built all five stats then filtered: 22.45 ms vs 1.75 ms `sharpe` only (12.8×) = 46 % of step 8.
- ⚠️ `crossmarket/simulate/stress.py:degraded()` built 25,000 runs × trades of booleans: 816 MB/market → 94.5 GB (aborted). Chunks of 500 runs: 140 MB; 72 procs 22 GB. Output identical (issue #68, closed).
- Memory binds before time: `gate.harvest` 4.56 GB/1,000 files; `export_retest` 6.3 GB/500 × 9 markets; `retest.ingest` 7.5 GB summed RSS.
- SQX is more efficient with big batches: build 0.32 s/strategy at 50, 0.06 s at 500; crossmarket 9 markets 4.9 s at 17, 0.59 s at 500 → linear extrapolation overestimates SQX 4–8×.
- Per-strategy tasks, 96 strategies: 12 procs 1,041 s (75 % eff.), 24 → 759 (51 %), 48 → 695 (28 %), 72 → 674, 96 → 660 (15 %); serial part 0.83 s; one strategy (12–117,612 trades in batch) = 453 s alone.
- Per (strategy, market) after numba: 12 → 90.8 s, 24 → 52.2, **48 → 44.6**, 72 → 51.7, 96 → 59.4 (two SMT threads of one core get in each other's way).
- ⚠️ Profiling `names[0]` profiles whatever sorts first (2nd cheapest): stats 17.9 % at 5,563 trades vs 33.3 % at 44,771. Profile three sizes or publish no percentages.
- ⚠️ `pool.map` returns in order: 38 min silent on a 499 run, indistinguishable from a hang; `py-spy` needs ptrace, blocked here.
- 🔬 2026-09-26, crossmarket 499 × 9 markets (12.0 M trades) at 10,000 draws: 437 s/26.2 GB tree PSS
  → 376 s/13.1 GB after `block_rows` + `batch_cells`, verdict.csv identical. Per worker ~290 MB
  private, 3.5 GB shared with the parent.
- 🔬 2026-09-26, 500-strategy runs after the changes: gate.report 6.7 s/1.1 GB, snoopingScreen
  6.3 s/0.85 GB, readings/monkey (450 k trades) 4.2 s/1.4 GB, trade pack of 12.0 M rows 28.7 s/1.1 GB
  (the 154 s/6.3 GB of a 500 × 9 `export_retest` is mostly the `orderstocsv` JVM).
- 🔬 `studies.readings.monkey.report` per market (2026-09-26): 499 strategies × 10 markets, 4,897
  pairs, 113 s and 7.3 GB tree PSS.
- 🔬 2026-09-27, one strategy (`crossmarket.one.run`, 9 markets, 25,000 draws): serial 883 s → each
  market + OOS a `core.fanout` task: 116 s, same 3.8 GB peak; at 2,000 draws 136 → 26 s, contract
  JSON `==`. `ui/daemon/jobs.py` weighs jobs on 48 cores (fan-out 24, light 3, none below 20 GB free
  — `perf/ram-budget.md`, since 2026-09-27).
- 🔬 2026-09-29, OPEN #69/#70 re-confirmed on real stored input: `crossmarket.report` batch,
  `Test_USDJPY_donchianUpperCrossUp_M30/Retest_Markets_-_Family/2026-09-28`, 200 real strategies ×
  9 markets, `batch_draws` 10,000, 48 workers — **135 s wall**, 6,121 s CPU (45×). `verdict.csv`
  identical before/after: 200/200 `DESCARTAR`, same reasons. The whole 200-strategy batch today
  (135 s) beats #69's old single-largest-task floor alone (453 s, 96-strategy batch): the per-
  (strategy, market) split in `many.py`/`fanout.run` (`cd4503b`, 2026-09-26) is #69's fix, already
  shipped; `fanout.run`'s `as_completed` (not `pool.map`) already prints `PROGRESS` per strategy as
  it lands — #70's fix, same commit. Both close, not new work. `export_spp`'s offset reader and
  `snoopingScreen`'s single-column bar read (prototypes above) are shipped too
  (`core.barstore.source(feed, ["Close"])`) — nothing left there.
