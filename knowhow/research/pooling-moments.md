---
q: pool variance of many searches, mixture variance from counts means spreads, ddof conversion, ledger trials.accumulated, deflated Sharpe sigma
tag: 🔬  date: 2026-09-24  see: research/gates-are-owner-decisions
---
# Pool search moments exactly, converting ddof=1 spreads in and out
Stored spreads are `ddof=1` (correct: what the deflated Sharpe wants). Pooling is exact only on population spreads:
`sigma_pop² = sigma²·(n−1)/n` in, `× N/(N−1)` out. That sigma is the denominator of the whole overfitting correction;
feeding one batch's spread instead of the study's errs large and always flattering.

## Evidence
`ledger/trials.accumulated` (how many candidates ever scored and their spread, without keeping them):
```
grand   = sum(n_i * mu_i) / N
var_pop = sum(n_i * (sigma_pop_i^2 + mu_i^2)) / N - grand^2
```
⚠️ Skipping a conversion looks like rounding (0.8357 vs 0.8354 on the first test), passes eyeballing, grows as search sizes differ.
