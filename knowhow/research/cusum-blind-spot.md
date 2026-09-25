---
q: CUSUM stability test did not reject but halves differ, OLS-CUSUM break, profitShape, non-rejection is not stability, concentration few_periods
tag: 🔬  date: 2026-09-24  see: research/entry-vs-chance
---
# A CUSUM non-rejection is not evidence of stability; print the split table with the verdict
With per-trade P&L (std of hundreds of $) the OLS-CUSUM has little power except against huge shifts. Always print
the two-sided before/after table next to the verdict, never instead of it (alone it reads as a found break).
`stable` here and `few_periods` in the concentration test are compatible.

## Evidence
`Strategy 35.44.31`, OOS1, 1,119 trades (`strategies/profitShape/`): candidate break at trade 277, supremum 1.01 vs 5 % critical 1.36 (not rejected).

| segment | n | mean per trade | Sharpe per trade |
|---|---|---|---|
| before | 278 | +82.5 | +0.165 |
| after | 841 | −5.1 | −0.009 |

Best year carried 99 % of the profit.
