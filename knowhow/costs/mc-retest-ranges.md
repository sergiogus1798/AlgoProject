---
q: MC Retest RandomizeSpread RandomizeSlippage Min Max units points or multiples; factory default 1-5 0-5; mc_retest block assets; mc_pending; RandomizeMinDistance range
tag: 🔬  date: 2026-09-22  see: conditions/mc-retest-task, costs/slippage
---
# MC Retest spread/slippage ranges are absolute points; the factory 1–5 / 0–5 fits no instrument
Set the range at the instrument's scale in `assets/symbols/<SYMBOL>.yaml` → `mc_retest` block. `core.assetcheck.mc_pending()` names assets still without one.

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
- `RandomizeMinDistance` same shape, factory `0.0-10.0`; not in `assets/` (owner asked only for spread and slippage).
