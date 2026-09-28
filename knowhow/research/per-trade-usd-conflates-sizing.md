---
q: compare IS vs OOS trades per trade; per-trade return USD vs percent of balance vs per lot; trade Size changes between samples; money management sizing; MAE MFE histogram IS OOS shift; density histogram two samples
tag: 🔬  date: 2026-09-27  see: research-lessons
---
# A per-trade IS/OOS comparison in USD reads a change of lot size as a change of edge
The harvest's `Profit/Loss`, `MAE ($)` and `MFE ($)` are account money at each trade's own `Size`,
and the size moves between IS and OOS. Before reading a shift in USD, read it also over the lot
(`/ Size`) or over the balance before the trade (`/ (Balance − Profit/Loss)`); if the shift
vanishes there, it was sizing. `studies.screening.isOos` emits all three under the selector
`unidad`. Duration needs none of this.

## Evidence
`harvest/Test_USDJPY_donchianUpperCrossUp_M30/Results/2026-09-27/trades.parquet`, first strategy:
median `Size` 3.32 IS (1,066 trades) against 4.575 OOS (562), median balance 131k against 113k —
the lot grew while the account shrank, so it is not fixed-fractional of balance either. Median
P/L 9.4 USD IS, 58.8 OOS. Also: that harvest's `metrics.parquet` is indexed by `identity` with
a `strategy` column; a density stored at six significant digits keeps its area within 3e-4
(bin edges above 10 lose the fifth decimal), hence the 1e-3 tolerance in `blocks.validate`.
