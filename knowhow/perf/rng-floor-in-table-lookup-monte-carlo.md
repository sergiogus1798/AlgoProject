---
q: Why is numpy's rng.random the floor of a table-lookup Monte Carlo kernel, and how to beat it bit for bit?
kw: PCG64 in numba, rng.random 3.15 ns, bit_generator.state, advance, reduceat pairwise, q_null, windowed gather, monte carlo kernel
tag: 🔬  date: 2026-10-12  see: perf/numba-division
---
# `rng.random` costs 3.15 ns per uniform and is the floor of a table-lookup kernel; PCG64 inside numba gives the same stream at 2.24 ns
Once draws are table lookups (`engines/nulls/windowed.py:121`), numpy's uniform is 3.15 of the kernel's 4.07 ns. Re-implement PCG64 in numba from `rng.bit_generator.state` and `advance()` the generator afterwards: identical stream, 2.24 ns. Numba's own generator is slower (5.86 ns) and changes the stream. To match numpy bit for bit in `q_null` (`studies/screening/analysis/resample.py:60-67`): `reduceat` sums `a[0] + pairwise(rest)`; `.sum(axis=1)` is pairwise over the row. Prototype only (scratchpad `p5py/`), not in the repo.

## Evidence
- 🔬 n=300, 100,000 draws, synthetic trades on real XAUUSD H1: `timing` 4.07 -> 2.24 ns, `timing_holds`/`free` 10.9 -> 6.8 ns; `array_equal=True` vs the table gather. float32 2.09 ns and SFC64 1.77 ns change the stream.
- 🔬 `q_null` shuffle in place: 12-17 -> 8.1-8.6 ns per element, bit for bit, n=17..3000.
- 🤔 1 M draws x 4 rungs: 9.0 -> 5.4 s per strategy-core (estimate).
- Source: `findings-PY5.md` NEW-1, NEW-3.
