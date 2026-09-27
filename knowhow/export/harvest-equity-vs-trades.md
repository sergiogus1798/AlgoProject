---
q: harvest equity.parquet final value differs from sum of trades Profit/Loss; daily curve vs trade list mismatch; which total to show; tearsheet totals
tag: 🔬  date: 2026-09-27  see: sqx-format/leg-curve-warmup, sqx-format/daily-equity-bin
---
# A harvest's daily curve and its trade list do not end at the same total
In `harvest/<P>/<D>/<day>/`, the last `equity` of a (strategy, sample) in `equity.parquet` (SQX's
daily curve from the `.sqx`) differs from the sum of `Profit/Loss` in `trades.parquet` for about
half the pairs, by up to ~1.5 k$. Never reconcile one against the other as a check; name the source
of every total you show (the Ficha shows both). Cause not investigated 🤔 (last-day cut, swaps or
an open trade are candidates).

## Evidence
`USDJPY_workflow_profiling_v1/Results/2026-09-26`, 400 (identity, sample) pairs: |diff| median
0.20 $, p90 740 $, max 1,566 $, 49 % above 1 $. Strategy 22.18.65 IS 59,291.63 vs 59,690.75;
Strategy 1.23.51 OOS 8,473.36 vs 8,473.42 (found building `ui/daemon/tearsheet/`, 2026-09-27).
