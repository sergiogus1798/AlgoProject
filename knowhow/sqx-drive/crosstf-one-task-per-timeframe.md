---
q: How is Cross TF wired: one retest task per timeframe, and what happened to D1?
kw: Cross TF one task per timeframe; CrossTF M30 H4 tasks; D1 removed from crossTF 2026-10-09; no MetaTrader 4 engine for D1; why not RetestOnAdditionalMarkets for timeframes; crossTF blocks.json databanks
tag: 🔬  date: 2026-10-09  see: export/data-all-blocks, sqx-drive/crosstf-scaling-coefficients, sqx-drive/crosstf-input-filled-by-no-task
---
# Cross TF runs one retest per timeframe, never blocks of the cross-check; D1 was removed (2026-10-09)
`sqx.projects.crosstf.wire` writes `CrossTF` (the mothers' timeframe, cross-check OFF) and one
«CrossTF <TF>» per `crosstf.timeframes` entry (`crosstfsolo`, copied from `CrossTF`: same window,
costs, precision), each reading `CrossTF_Input` and writing `CrossTF_<TF>`, all on the doctrine's
engine. `blocks.json` lists `blocks` and `databanks` in order;
`studies.transfer.crossTF.inputs.gather` reads one export per timeframe as that block. Owner,
2026-09-30: a `data=all` export cannot be split on one symbol (`export/data-all-blocks`). D1 (own task on
the MetaTrader 4 engine, 2026-09-30) was removed by the owner on 2026-10-09: no D1 sibling, task or engine entry.

## Evidence
- 🔬 Phase 2 (encargo 47): per sibling timeframe a twin task «CrossTF <TF> build» → databank `CrossTF_<TF>_build`
  (`sqx/projects/workflow.py` `CROSSTF_BUILD`), on the `build` window, read by step 11.7. It is deliberately NOT in
  `stages.yaml`: it is selected with `stage.just` (`crosstfload.phase2_tasks`), and `afterrun` exports its databank
  with no extra wiring. Sisters per mother (`assets/_build.yaml` `crosstf.timeframes`, owner 2026-10-09): M15 → M10, M30, H1 · M30 → M15, H1, H4 · H1 → M30, H4 · H4 → M30, H1, H12 (H12 over H8: Claude's pick, SQX and the scaler already ran H12). A mother timeframe missing there is refused by `sqx.projects.crosstfsolo.planned`.
- 🔬 M10 as a sister: run `Test_USATEC_M15_doubleROCL_chk9`, 3 mothers → 12 strategies in `CrossTF`, databanks `CrossTF M10 build`, `CrossTF M30 build`, `CrossTF H1 build` 12 each; step 12 had M10 cells with 784 trades.
- 🔬 2026-09-30, `Test_USDJPY_donchianUpperCrossUp_H1`, 30 mothers + 90 siblings (120 per task):
  `CrossTF` 148,430 trades, all opens on the hour; `CrossTF_M30` 273,513, 52.4 % opening at :30;
  `CrossTF_H4` 42,934, opens only at 4/8/12/16/20 h; `CrossTF_D1` (MetaTrader 4) 8,861, all at 00:00 —
  the mothers alone 1,638 D1 trades. Study cells: baseline H1 32,479 trades = the mothers' rows of
  `CrossTF`; 3 of 90 siblings survive (M30), D1 scaled all `unusable` (periods clamped), D1 unscaled read.
- The four tasks ran in one start of the custodian (`ui.daemon.advance.run` after the Cross Market cut).
