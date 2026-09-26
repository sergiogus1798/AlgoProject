---
q: cross-market cross-timeframe check acceptance conditions empty; crossmarket.conditions crosstf.conditions _build.yaml; silence whole task; Setup missing dateFrom fails task; crossTF block names LOM
tag: 🔬  date: 2026-09-24  see: conditions/retest-additional-markets, conditions/active-conditions-in-crosschecks
---
# Cross-market / crossTF checks run with zero conditions; the verdict is taken in Python
- Doctrine: `crossmarket.conditions: []`, `crosstf.conditions: []` in `assets/_build.yaml`; verdict applied with `/curate`.
  `sqx/projects/crosschecks.silence()` enforces it over the WHOLE task (since 2026-09-25: a cloned task carried live conditions outside the check) and reports the count; both commands refuse if the list is not empty.
- ⚠️ Every field a `<Setup>` inherits must still be present as an attribute (`dateFrom`/`dateTo` etc.); the mask picks the winner, not which exist.
- 🤔 With zero live conditions `MinConditions`/`MinMarkets` are left untouched (WFM precedent: score 100 → all pass). Unverified here — check output count = input count on the first real run.

## Evidence
- Donor `Retest-Task3.xml` ("Retest Markets - Family"): `<Check>all</Check>`, `<MinConditions>2</MinConditions>` (one condition defined → never satisfiable),
  `<MinMarkets>1</MinMarkets>`, `ReturnDDRatio > 1` (`market="0"`, `subresult="30"`). `DeleteFailedStrategies=false` protects only the INPUT databank;
  a live condition still keeps a failing strategy out of the OUTPUT (`Cross Check filter`, as for the WFM in `assets/_build.yaml`).
- Why: Python never seeing SQX's dropped strategies can't say which market killed which, nor compute a p-value.
- 🔬 `XAU_crosstf_probe` (custodian, M30, 6 strategies, 17 ms each), two extra Setups at H1, H4 on the same symbol:
  `<MainTestValues timeframe="false">` honoured; blocks `Results/Main: <feed>_LOM_M30`, `Results/AdditionalMarket: <feed>_LOM_H1: …`, `…_LOM_H4: …`;
  distinct backtests (one strategy −1,653 M30, −8,574 H1, −758 H4).
- 🔬 Missing `dateFrom`/`dateTo` error: `Cannot start project … Cannot load settings of Cross check 'RetestOnAdditionalMarkets'. Cannot invoke 'String.length()' because 'text' is null`.
- 🤔 Daily-curve lengths differ over one window (1,312 M30 / 1,334 H1 / 1,458 H4) — probably first-to-last-trade spans; unmeasured. Check before length-sensitive comparisons.
