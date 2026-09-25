---
q: CalmarRatio formula, CalmarRatio AnnualPctReturnDDRatio identical, RExpectancyScore meaning, UlcerPerformanceIndex reconstruct, SQX metric definitions SPP export
tag: 🔬  date: 2026-09-21  see: sqx-format/mc-retest-reconstruction, sqx-format/sqstats-blob
---
# Calmar = CAGR / DrawdownPct (= AnnualPctReturnDDRatio); UlcerPerformanceIndex is not reconstructible
`CalmarRatio?` and `AnnualPctReturnDDRatio?` are one column under two names — store one.
`RExpectancyScore` ≈ `RExpectancy` weighted by √trades (t-statistic-like; not redundant — it penalises
few-trade regions). `UlcerPerformanceIndex` ∝ `AnnualPctReturn / UlcerIndex` but its constant drifts:
export SQX's column, never compute an analogue.

## Evidence
- SPP export, XAUUSD, 20,554 rows with > 50 trades: Calmar = CAGR/DrawdownPct, 1.9 % median rel. error
  entirely 2-decimal storage (2.20/5.52 = 0.3986 → 0.40; 0.59/9.11 = 0.0648 → 0.06). Calmar vs
  AnnualPctReturnDDRatio: rel. error 0.00e+00, rho 1.0000.
- `RExpectancyScore` tracks `RExpectancy·sqrt(n)` at rho +0.89..+0.99 across five strategies, scale factor
  2.0–3.6 per strategy (exact formula unknown). rho with `RExpectancy` +0.856..+0.976.
- UPI over 21,179 SPP permutations: rho +0.998 with `AnnualPctReturn/UlcerIndex` (+0.9993 with
  `AHPR/UlcerIndex`). Constant median exactly 16.0000 over 1,440 rows with `UlcerIndex` ≥ 0.5, but rows
  where both are large give median 16.53, sd 3.36 (worse, not better); residual correlates with
  `NumberOfTrades` (+0.52) and `DataLength` (+0.50) → a time/observation term not among the 152 stored
  columns, consistent with `UlcerIndex` on the daily curve. Joins Sharpe, Sortino, Ulcer, RSquared,
  Stability as non-reconstructible.
- Do not name the ~16 constant: sqrt(252) = 15.87 and 16 both sit inside the spread.
