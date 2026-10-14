# construct/pairs — how alike two strategies' P&L are

Pure functions on two aligned series (NaN = outside history, excluded pairwise). The measures
return the signed value; the admissible graph applies the owner's `|ρ| > 0.30` (Q6). Stress
correlation and effective N are reported, never a filter (Q15).

**Imports from:** numpy, pandas, scipy, numba · **Consumed by:** `search/admissible.py`, the verdict's «did the diversification hold»

| file | what it does | run it | in → out |
|---|---|---|---|
| `measures.py` | Pairwise correlation measures on aligned P&L series, signed, pairwise-finite. | imported | two series → float |
| `rolling.py` | Rolling-window correlation extremes over a pair's aligned series. | imported | two series → maxima |
| `stress.py` | Stress-day selection, stress-day correlation, and effective N of a candidate set. | imported | pool → days, float |
| `table.py` | Long-form pairwise measure table over every pair of build columns, in parallel blocks of pairs. | imported | build matrices → pairs frame |

## Traps
- **The tail measure is biased negative between independent series (≈ −0.46)**: it is filtered
  one-sided (`config.yaml pairs.one_sided`, `knowhow/research/pair-filters-false-rejection.md`).
- **Too little overlap is never 0.0** (AlphaForge's bug): a pair under 24 shared months is rejected
  by the graph, whatever its coefficient.
