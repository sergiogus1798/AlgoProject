---
q: H12 custom timeframe SQX retest Setup timeframe="H12"; cross-timeframe H1 to H4 and H12; H8 H12 support; 12h resample
tag: 🔬  date: 2026-09-26  see: sqx-drive/running-a-task-headless, conditions/crossmarket-crosstf-no-conditions
---
# SQX runs a custom timeframe like H12 when a task's `<Setup>` just names it
`<Chart symbol="…" timeframe="H12">` in a cross-timeframe `<Setup>` is enough: SQX builds the bars
itself from M1, no GUI step. The Python side resamples M1 with pandas `12h` (`core.barstore.RULE`).
Default cross-timeframe targets (owner): from M30 → H1, H4; from H1 → H4, H12.

## Evidence
- 2026-09-26, custodian, project `USDJPY_emaCross_H1`, task CrossTF with blocks H1/H4/H12: log
  `Loading backtest data for Backtests on additional markets - USDJPY_DukasM1_the5ers / H12`, task
  finished in 24.8 s, 6 of 6 strategies back, export 28,414 trades in 3 blocks, study read block 2 = H12.
- 🤔 Bar alignment of H12 against SQX unverified: P/L reconstruction correlates 0.982 — the same
  shortfall as H4 (0.976), so it is not H12-specific. Scaling ÷12 clamps short periods (2 of 2).
