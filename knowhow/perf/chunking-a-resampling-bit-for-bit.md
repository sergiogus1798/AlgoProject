---
q: Which numpy operations give the same bits when a resampling is cut into blocks of draws, and which do not?
kw: chunk draws, array_equal, rng.integers int8 buffer, np.add.at bincount order, signs @ weeks matmul differs, OpenBLAS dgemm, numba cache recursion segfault, pairwise sum, reduceat, q_null, footprint, wfc measure
tag: 🔬  date: 2026-10-13  see: perf/rng-floor-in-table-lookup-monte-carlo
---
# Cutting a resampling into blocks keeps the bits for row-wise numpy work, never for a BLAS product
Same bits in blocks: `rng.integers(0, high, (rows, k))` (int64) and `rng.random` — the half word a 32-bit range leaves over lives in the generator and carries to the next call; any row-wise reduction (`median`, `mean`, `sum(axis=1)`, `rankdata(axis=-1)`). A `np.bincount(index, weights)` over all draws becomes `np.add.at(running, index, weights)` block after block: both add in index order, a sum of per-block bincounts does not. `rng.integers(..., dtype=np.int8)` keeps its spare bytes inside ONE call: blocks match only when each holds a multiple of 4 values. **`signs @ panel` does not survive**: OpenBLAS sums an edge row in another order than an inner one, so the product of a block differs in the last bit from the same rows of the whole — a draws x variants null that goes through `@` cannot be cut bit for bit. In numba, to sum as numpy does: `reduceat` and `sum` are `a[0] + pairwise(rest)` and `0 + pairwise(row)`, 8 running sums up to 128 values, halves (rounded down to 8) above; write the halving with a stack — a self-recursive `@njit(cache=True)` function segfaults when loaded from the cache.

## Evidence
- 🔬 `tests/test_perf66_resample.py`: `drawdowns` (335 cases), `q_null` (525 + edges), `improvement._resampled`, `footprint` in blocks of 1 draw to all, `array_equal` and generator state against the code replaced.
- 🔬 `flip.signs` (int8) against blocks drawn from one generator, 1,800 shapes: equal whenever rows per block is a multiple of 4; 936 differ otherwise.
- 🔬 `whole @ panel` against `concatenate(block @ panel)`, OpenBLAS 0.3.29 Haswell, 1 thread and all: 506 of 3,600 cases differ with the signs equal (e.g. 5,001 x 261 weeks x 120 variants, blocks of 1,000). So `wfc/measure/reading.py` was left whole (encargo 66 §3.9d).
- 🔬 `permuted._pairwise` written recursively: first run (compiled) passes, second run (from `__pycache__`) dies with SIGSEGV inside the kernel; numba 0.67.0.
