---
q: Where does our CSCV differ from the published Bailey/Lopez de Prado statistic?
kw: CSCV ties, duplicate variants raise PBO, odd number of blocks partitions, first column wins tie, inf NaN huge level tiny variance, near-duplicate variants omega, pbo_p
tag: 🤔  date: 2026-10-13  see: research/cscv-daily-returns, research/cscv-chosen-point-slope-seesaw
---
# The CSCV has three deviations from the published statistic (read from the code; the odd-blocks one is now refused)
1. Ties score lowest: near-duplicate variants push PBO up (`pbo_p` is less affected). 🔬 Two identical best columns versus one give omega x 24/25.
2. On a tie in the in-sample pick, the first column wins. 🤔
3. ~~An odd number of blocks~~ — refused since 2026-10-13 (owner, encargo 66 P8): `partitions()` raises `ValueError`; `tests/test_perf66_cscv.py`. Deviation gone. 🔬
4. A column with an enormous level and tiny variance can give inf or NaN. 🤔
Would confirm 2 and 4: a minimal panel per case through `measure/cscv.py`. Correcting either changes stored numbers (encargo 66, question 9).

## Evidence
Found by the fourth independent review of encargo 66 (2026-10-13) reading the CSCV code; only the tie case (1) was run, on a synthetic panel.
