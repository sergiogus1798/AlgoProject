# construct/pairs — how alike two strategies' P&L are

Pure functions on two aligned series (NaN = outside history, excluded pairwise). The measures
return the signed value; the admissible graph applies the owner's `|ρ| > 0.30` (Q6). Stress
correlation and effective N are reported, never a filter (Q15).

**Imports from:** numpy, pandas, scipy, numba · **Consumed by:** `search/admissible.py`, the verdict's «did the diversification hold»

| file | what it does | run it | in → out |
|---|---|---|---|
| `measures.py` | The `MEASURES` registry — Pearson, Spearman, co-loss, tail — and the overlap count | imported | two series → float |
| `rolling.py` | The largest coefficient over every 60-month window, whole build and recent windows | imported | two series → maxima |
| `table.py` | Every measure over every pair of the pool on the build slice, chunked, long form | imported | build matrices → pairs frame |
| `stress.py` | The pool's stress days, correlation on them, and effective N by two formulas | imported | pool → days, float |

## Traps
- **The tail measure is biased negative between independent series (≈ −0.46)**: it is filtered
  one-sided (`config.yaml pairs.one_sided`, `knowhow/research/pair-filters-false-rejection.md`).
- **Too little overlap is never 0.0** (AlphaForge's bug): a pair under 24 shared months is rejected
  by the graph, whatever its coefficient.
