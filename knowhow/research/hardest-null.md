---
q: Does a null that randomises more make the null harder to beat?
kw: which random-entry null is hardest to beat / most conservative, block_shift vs other nulls, crossmarket four nulls, null spread sigma, docstring contradicted by measurement
tag: 🔬  date: 2026-09-15  see: research/bar-file-wider-than-backtest, research/random-entry-nulls
---
# "Randomises more" ≠ "harder to beat": measure each null's spread
`block_shift` (moves each trade within its own six-month block and weekday-hour slot) is the reported model because
it changes exactly one thing — a low p is attributable to entry timing. It is usually, not always, the tightest.
A strategy surviving all four nulls says more than one surviving only it. A measurement contradicting a docstring
may be measuring a bug: ask what else must be true first.

## Evidence
The old `studies/transfer/crossmarket` study's four random-entry nulls (three re-lay the whole run from a random start); that study's code and statistics were retired on 2026-10-07 (encargo 46), the null spreads below are data about the nulls and still stand.
- Unbounded sample: `block_shift` σ 0.073 vs 0.095 on XAGUSD, lowest p everywhere — mostly the wider-bar-file artefact.
- Window bounded: narrowest null in 5 of 8 (strategy, market) pairs, lowest p in 7 of 8.
