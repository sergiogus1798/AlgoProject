---
q: Monte Carlo slow, memory bandwidth bound, max_workers, tiles tile_bytes 4 MB, float32 paths float64 accumulator, chunk bytes budget, parent single-threaded share, n_sims 20000 vs 100000, compare versions without seed
tag: 🔬  date: 2026-09-20  see: perf/server-cores-and-ram, perf/python-parallelism, research/robustness-monte-carlo
---
# Monte Carlo is memory-bandwidth bound: budget in bytes, tile to L3 (4 MB), float32 paths
The old kernel saturated at ~24 processes (DRAM). Fix: draw the batch in tiles with persistent `float32`/`int32` buffers
sized by a byte budget (`tile_bytes` 4 MB on this EPYC) — per-worker memory constant in N, and it scales to 96.
Accumulators must be explicit `float64` (`sum/einsum(..., dtype=np.float64)`). `chunk` bounds simulations, not memory.
`n_sims` 20,000 is the first value meeting the module's 10 % stability tolerance. Compare versions paired (same draws), never by one block of repeats.

## Evidence
`XAUUSD / MC Trades` (757 strategies, median N 1,132 trades), 96-core / 125 GB machine.
- Old kernel (`draws.stationary` + `metrics.paths`, 2,000 paths × 1,132): 8.5× at 8 procs, 16.5× at 24, 17.9× at 95; batch time 175 → 642 ms from 24 to 95, 133 batches/s flat.
- Bytes not FLOPs: `float32` paths, `int32` indices, `metrics.paths` temporaries 7 → 3 arrays: 271,000 → 532,000 paths/s (1.96×), `np.allclose` rtol 1e-9 on all 8 stats.
- `_batch` held 6.1 `(chunk, N)` float64 matrices (tracemalloc, base-matrix units): `draws.stationary` 2.1 · `block_shuffle` 3.2 (fill `argsort`) · `iid_bootstrap` 1.0 · four `stress` 1.1–3.1 · `metrics.paths` 5.1 on top of input.
  `chunk: 2000` = 53 MB (N=542), 111 MB (N=1,132), 337 MB (N=3,437); ×96 = 32.3 GB. Tiles: 12.2/12.1/12.1/12.0 MB for N = 542/1,132/2,374/3,437. Parent ≤ 0.74 GB.
- Paths/s N=1,132, old vs tiles: 24 procs 188,961 vs 333,902 · 48: 191,093 vs 549,773 · 96: 200,602 vs 714,801.
- Tile size: 1 MB 203,057 · 2 MB 494,914 · **4 MB 714,801** · 8 MB 652,162 · 16 MB 481,943 · 32 MB 405,100 (below: interpreter, 36-row tiles; above: out of L3 ~5 MB/core).
  In-command (`montecarlo.analyse` 920 ops / `analyse_long` 3,437 ops): 0.5 MB 13.3/101.7 s · 1 MB 10.6/62.5 · 2 MB 9.2/43.1 · **4 MB 8.7/33.0** · 8 MB 8.8/30.1 · 16 MB 9.6/29.4 · 64 MB 9.9/33.0; tree peak 2,520 → 2,993 MB from 4 to 16 MB.
- float32: veto percentiles match float64 at 4e-8–5e-7 relative; `sweeps.invariant()` on `iid_shuffle` std exactly 0.0 (vs 7.5e-12); with float32 accumulation 7.7e-3 USD.
- ⚠️ "Who restarts" and "where it restarts" need two uniform buffers. Calling `draws.stationary(145, ...)` once per tile (138×) does it:
  consecutive fraction 0.9333 both ways (theory 1 − 1/15), 0.1000 of restarts in first tenth — no start bias.
- Parent single-threaded work = 24 %: `family_d` (`engine.single`) 8.1 s + `_family_b` (`engine.sequential`) and `stitch` 4.6 s of 28.2 s per median strategy.
- `stability.spread()` max relative dispersion: 3.0 % at 100,000, 8.3 % at 20,000, 11.8 % at 10,000; 5.0 s vs 26.1 s.
- In the command (branch `perf/montecarlo-tiles`, `python3 -m perf.catalogue`, tree RSS): pool never saturates — `engine.run` splits into `chunk: 2000` tasks,
  `n_sims: 5000` = 3 tasks. Kernel 3.6× → −13.5 % wall (10.13 → 8.76 s), −14.6 % at 100,000 (24.44 → 20.88 s). Kernel and command are different questions.
- Tree peak (100,000, N=3,437): 19,671 → 8,814 MB (−55 %); the rest is 96 live interpreters (N=920: 8,723 MB). Growth 920→3,437 ops: master +83 %, tiles +1.0 %.
- ⚠️ `net_5` 8 repeats: master −19,678 vs tiles −18,903 (z = +3.3); two more master blocks −18,841, −19,261 → a block mean has 2.2 % own spread; 24 vs 16 → +1.6 % (z = +1.7).
  Paired float64 vs float32 on same draws: `net` p5 6.3e-8, `pf` p5 5.4e-10, `dd_pct` p95 1.0e-8, p99 1.6e-9; `losing_run` bit-identical.
- Later speedups (numba, LPT): `docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento).
