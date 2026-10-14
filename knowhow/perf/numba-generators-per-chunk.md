---
q: How does a numba prange kernel draw from numpy Generators without a seed per path?
kw: numba Generator prange, np.random.seed in njit, list of Generators, path_gens, CHUNKS, per-path default_rng slow, thread count reproducible
tag: 🔬  date: 2026-10-14  see: perf/python-parallelism
---
# numba takes a LIST of Generators: one per fixed chunk of rows, not one per row
numba 0.67 accepts a `list` of `np.random.Generator` as an argument (`integers`, `random`,
`geometric`, `permutation`, `shuffle` all work in nopython). One Generator per row is 40x slower than
the kernel (200k rows: 2.5 s to build, 3.9 s to unbox, against 0.15 s). So
`mc.paths.path_gens(rng)` spawns `CHUNKS = 1024` generators; a kernel runs chunk `c` in `prange` and
its rows `c, c+k, …` in order. The draws depend on `rng` alone, never on the thread count.
Replaced `np.random.seed` per row (32 bits only, so seeds had to be drawn without replacement).
Kernels: `mc/lay.py` (`t1`, `t2`), `search/stageb_null.py` (`_fill`).

## Evidence
Measured 2026-10-14 on 6 members, 60 days: `t1` 200k paths 0.159 → 0.285 s, `t2` 0.131 → 0.199 s,
`stageb_null.candidates` 1M 0.093 → 0.115 s (`tests/test_perf66_portfolio_mc.py`).
