---
q: How does SQX run a custom timeframe like H12 or M10 in a task's `<Setup>`?
kw: H12 custom timeframe SQX retest Setup timeframe="H12"; cross-timeframe H1 to H4 and H12; H8 H12 support; M10 custom timeframe; 12h resample
tag: 🔬  date: 2026-10-09  see: sqx-drive/running-a-task-headless, conditions/crossmarket-crosstf-no-conditions
---
# SQX runs a custom timeframe like H12 when a task's `<Setup>` just names it
`<Chart symbol="…" timeframe="H12">` in a cross-timeframe `<Setup>` is enough: SQX builds the bars
itself from M1, no GUI step. The Python side resamples M1 with pandas `12h` (`core.barstore.RULE`).
M10 works the same (verified 2026-10-09; Python side: `scale.MINUTES`, `core.barstore.RULE`). Default sisters per mother: `assets/_build.yaml` `crosstf.timeframes` (M15 → M10, M30, H1 · M30 → M15, H1, H4 · H1 → M30, H4 · H4 → M30, H1, H12).
⚠️ Two timeframe lists in code: `sqx.projects.buildrules.TF_MINUTES` (what a project may be BUILT on:
no H12, has H2) and `sqx.variants.scale.MINUTES` (what CrossTF rescales to: has H12, no H2). A CrossTF
target list offered from `TF_MINUTES` cannot hold H12 — use `scale.MINUTES` (as the Configuración SQX zone does).

## Evidence
- 🔬 M10: run `Test_USATEC_M15_doubleROCL_chk9` (USATEC M15), CrossTF databanks `CrossTF M10 build` etc. 12 strategies each, step 12 M10 cells with 784 trades; only the Setup named M10.
- 2026-09-26, custodian, project `USDJPY_emaCross_H1`, task CrossTF with blocks H1/H4/H12: log
  `Loading backtest data for Backtests on additional markets - USDJPY_DukasM1_the5ers / H12`, task
  finished in 24.8 s, 6 of 6 strategies back, export 28,414 trades in 3 blocks, study read block 2 = H12.
- 🤔 Bar alignment of H12 against SQX unverified: P/L reconstruction correlates 0.982 — the same
  shortfall as H4 (0.976), so it is not H12-specific. Scaling ÷12 clamps short periods (2 of 2).
