---
q: Cross TF one task per timeframe; CrossTF M30 H4 D1 tasks; CrossTF_D1 databank; D1 MetaTrader 4 engine no session; why not RetestOnAdditionalMarkets for timeframes; crossTF blocks.json databanks; crosstf.engines
tag: 🔬  date: 2026-09-30  see: export/data-all-blocks, sqx-drive/crosstf-input-filled-by-no-task
---
# Cross TF runs one retest per timeframe, never blocks of the cross-check; D1 on the MetaTrader 4 engine
`sqx.projects.crosstf.wire` writes `CrossTF` (the mothers' timeframe, cross-check OFF) and one
«CrossTF <TF>» per `crosstf.timeframes` entry (`crosstfsolo`, copied from `CrossTF`: same window,
costs, precision), each reading `CrossTF_Input` and writing `CrossTF_<TF>`; `crosstf.engines` picks
the engine per timeframe (D1 → `MetaTrader4`). `blocks.json` lists `blocks` and `databanks` in order;
`studies.transfer.crossTF.inputs.gather` reads one export per timeframe as that block. Owner,
2026-09-30: a `data=all` export cannot be split on one symbol (`export/data-all-blocks`), and on the
MT5 engine a D1 strategy enters at 00:00 while a prop firm's session opens at 00:05 — it traded nothing.

## Evidence
- 🔬 2026-09-30, `Test_USDJPY_donchianUpperCrossUp_H1`, 30 mothers + 90 siblings (120 per task):
  `CrossTF` 148,430 trades, all opens on the hour; `CrossTF_M30` 273,513, 52.4 % opening at :30;
  `CrossTF_H4` 42,934, opens only at 4/8/12/16/20 h; `CrossTF_D1` (MetaTrader 4) 8,861, all at 00:00 —
  the mothers alone 1,638 D1 trades. Study cells: baseline H1 32,479 trades = the mothers' rows of
  `CrossTF`; 3 of 90 siblings survive (M30), D1 scaled all `unusable` (periods clamped), D1 unscaled read.
- The four tasks ran in one start of the custodian (`ui.daemon.advance.run` after the Cross Market cut).
