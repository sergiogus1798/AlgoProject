---
q: MC Retest RandomizeSpread RandomizeSlippage Min Max units points or multiples; factory default 1-5 0-5; mc_retest block assets; mc_pending; RandomizeMinDistance range; tarea_sin_dispersion; MC draw granularity tick
tag: 🔬  date: 2026-09-27  see: conditions/mc-retest-task, costs/slippage
---
# MC Retest spread/slippage ranges are absolute points, drawn on a ~0.1-point grain
Set the range at the instrument's scale in `assets/symbols/<SYMBOL>.yaml` → `mc_retest`
(`core.assetcheck.mc_pending()` names assets without one). On USDJPY SQX draws in steps of about
0.1 point (one tick): a range spanning k steps gives ~k outcomes. The 1x–4x of a 0.1-point spread
(0.1–0.4) gave 2, of a 0.05 slippage (0.05–0.2) gave 1 → `tarea_sin_dispersion`. Span ≥ 5–10 ticks.

## Evidence
```xml
<Method use="true" type="RandomizeSpread">
  <Params><Param key="Min" type="Double">1.0</Param><Param key="Max" type="Double">5.0</Param></Params>
</Method>
```
- Sweep of every master `project.cfx`: almost every instrument carries factory `spread 1.0-5.0`, `slippage 0.0-5.0` (gold, Nikkei, EURUSD alike).
  `NIKKEI225_DukasM1_Infinox` `defaultSpread` 1100 → perturbed 1–5 points, ~200× cheaper than the backtest's own cost.
- Deliberate ranges sit at scale: `XAUUSD_DukasM1_Infinox` `spread 5-12` (real spread 10); `NIKKEI225_DukasM1_Infinox` `spread 80-200` and `120-400`.
  🤔 Factory value = what an untouched task inherits, not a choice.
- 2026-09-27, `Test_USDJPY_mcrRanges` (3 strategies, 1,000 sims, distinct NetProfit per strategy, same
  for all 3): spread 0.1–2.0 → 17, 0.1–1.0 → 8; slippage 0.05–2.0 → 19, 0.05–0.5 → 4.
- 2026-09-26, `Test_USDJPY_donchianUpperCrossUp_M30` (M30, 8 market-entry strategies), `raw/.../MCR_All/2026-09-26/sims`
  `groupby(['task','strategy']).NetProfit.nunique()`: slippage 1 for all 8, spread 2 for all 8, ohlc/stress ~1000.
  Same `slippage` flag on all 8 of `USDJPY_workflow_profiling_v1` (H1) the same morning.
- `RandomizeMinDistance` same shape, factory `0.0-10.0`; not in `assets/` (owner asked only for spread and slippage).
