---
q: Why is a numba loop that sums gains and losses separately slow, and how to fix it bit for bit?
kw: branch misprediction, if p > 0 gain elif loss, profit factor kernel slow, select cmov, numba ternary, engines/nulls/kernel.py, ladder ns per trade
tag: 🔬  date: 2026-10-13  see: perf/numba-division
---
# An `if p > 0: gain += p / elif p < 0: loss -= p` on random P/L costs ~8 ns per trade: write it as a select
The sign of a null trade's P/L is a coin, so the branch mispredicts on half the trades. Write
`gain += p if p > 0.0 else 0.0` and `loss -= p if p < 0.0 else 0.0`: LLVM emits a select, and adding
0.0 leaves the sum as it was (NaN P/L included — do not use `max(p, 0.0)`, which is not NaN-safe),
so the result is bit-identical. In the ladder kernel this, not the sort, was half of what remained.

## Evidence
`engines/nulls/kernel.py` (`runs`, `ladder`), encargo 66 §3.3, measured on leaseWeb under load,
n = 500 trades, ns per trade valuation, kernel only: argsort kernel 51 · bucket ordering with the
branch 23 · bucket ordering with the select 15. `np.array_equal` on the five statistics against the
argsort kernel in every case of `tests/test_perf66_ladder.py`.
