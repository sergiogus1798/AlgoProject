---
q: which window was a strategy selected on; is 2018-2022 out of sample; untouched data start 2023; selection bias cross-market retest as filter; sampleType per resultType Build task
tag: 🔬  date: 2026-09-17  see: conditions/retest-additional-markets, conditions/crossmarket-crosstf-no-conditions
---
# XAUUSD Build selection touches every window; untouched data starts 2023-01-01
- 2018–2022 is NOT virgin for databanks built by this task: it enters via every `sampleType=127` condition and the WFM OOS `NetProfit > 0`.
- `RetestOnAdditionalMarkets` can be a selection filter too — check which task wrote a databank before calling a cross-market result untouched.
- Strict OOS = retest over 2023-01-01 → today (base and additional markets).
- A p-value inside a selected window speaks about that window's mechanics, not unseen data; across a selected population it is biased low.

## Evidence
`XAUUSD/project.cfx`, `Build-Task3.xml`, `use="true"` only:

| resultType | sampleType | active |
|---|---|---|
| `main`, `WhatIf`, `RetestWithHigherPrecision`, `MonteCarloRetest` | 127 (2008–2022) | 8 |
| `WalkForwardOptimization`, `MonteCarloManipulation` | 10 (IS) | 10 |
| `WalkForwardMatrix` | 20 (OOS) | 2 — `NetProfit > 0` |
| `RetestOnAdditionalMarkets` | 127 | 1 — `ProfitFactor > 1.5` |

- 30 of 30 of the `Retest Markets - Family` sample are profitable on gold 2018–2022 — shape of a selected window.
- Every `dateTo` in build/retest tasks is `2022.12.31`; bars run to 2026-01-16 (XAUUSD, XAGUSD), 2026-06-01 (BRENT).
