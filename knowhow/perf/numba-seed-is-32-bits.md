---
q: How many distinct random streams can a numba kernel seeded per path with `np.random.seed` have?
kw: numba np.random.seed uint64 truncated, 2**32 seeds, repeated paths, birthday collision, duplicate Monte Carlo paths, prange seed per row, SeedSequence spawn, path_seeds
tag: 🔬  date: 2026-10-13  see: perf/python-parallelism
---
# numba's `np.random.seed` keeps 32 bits: draw per-path seeds WITHOUT replacement
Inside `@njit`, `np.random.seed(x)` uses only the low 32 bits of `x`, so a `uint64` seed array or a
`SeedSequence.spawn` child buys nothing: there are 2**32 streams. Seeds drawn with replacement
(`rng.integers(0, 2**32, n)`) repeat ~n²/2³³ pairs — ~116 identical paths at a million. Use
`portfolio.common.construct.mc.paths.path_seeds(n, rng)` (`rng.choice(2**32, n, replace=False)`,
36 ms for a million). The per-path seeded kernels today: `mc/lay.py` (`t1`, `t2`) and
`search/stageb_null.py` (`_fill`); both take their seeds from it.

## Evidence
`f = njit(lambda s: (np.random.seed(s), np.random.random())[1])`: `f(5) == f(2**32 + 5) == f(2**33 + 5)`
(numba 0.67). `default_rng(1).integers(0, 2**32, 10**6)` holds 110 repeated values; `path_seeds` none
(`tests/test_perf66_portfolio_mc.py`).
