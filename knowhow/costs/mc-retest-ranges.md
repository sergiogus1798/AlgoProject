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
- 🔬 2026-09-30: the SAME "span ≥ 5–10 ticks" trap now shows up on the cheap side too. `onboard.plan()`'s
  `mc_spread` is `verdict.mc_multiples()`'s day-to-day quantile ratios (≈0.65×–1.47×) times the segment's
  OWN base spread — a multiplicative band, so its absolute point-span shrinks with the base spread.
  USDJPY (`spread_is` 0.49): mc_retest.spread `0.32–0.72`, span 0.4 pt = **4** of the ~0.1-pt draw
  steps → only ~5 distinct spreads, which reads as "MCR results all land within 35.000–39.000" (too few
  simulations differ). AUDJPY (`spread_is` 1.61): `0.95–2.35`, span 1.4 pt = 14 steps → healthy.
  **Fixed** (`studies.data.spread.onboard.mc_range`, `config.yaml` → `mc.grain`/`mc.min_steps`, 10
  steps of 0.1 pt = a 1.0 pt floor, widened around the band's own centre so the multiplicative
  quantiles still say what they said): dry-run (`--write` NOT passed) before → after, 2026-09-30 —
  USDJPY `0.32–0.72` (0.40 pt, 4 steps) → `0.02–1.02` (1.00 pt, 10 steps); EURUSD `0.36–0.86`
  (0.50 pt, 5 steps) → `0.11–1.11` (1.00 pt, 10 steps); AUDJPY `0.95–2.35` (1.40 pt, 14 steps) →
  unchanged, already above the floor; XAUUSD `8.68–31.92` (23.25 pt, 232 steps) → unchanged.
  `mc_retest.slippage.{min,max}` is now also computed — half of the (already floored) spread band,
  same multiples, same convention as the declared `slippage_*` costs — and `apply()` writes both;
  USDJPY comes out `0.01–0.51`. Nothing has been written to `assets/`: the owner decides the ranges
  in the morning, this only fixes the computation.
