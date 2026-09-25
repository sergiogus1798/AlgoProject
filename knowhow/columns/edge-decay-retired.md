---
q: EdgeDecayRatio EdgeDecayFilter, edge decay score IS vs OOS, net profit decay calendar artifact, decay ratio near zero, why edge decay retired
tag: 🔬  date: 2026-09-06  see: columns/custom-columns-stored
---
# `EdgeDecayRatio` / `EdgeDecayFilter` are retired — do decay work in Python over exported CSVs
Four independent disqualifying defects. Never put net profit in a decay ratio (unequal IS/OOS lengths);
use only length-robust quantities (PF, Sharpe, Sortino, Calmar, Win %). ⚠️ `EdgeDecayFilter` is wired into
`AUDJPY`, `EURUSD`, `USDJPY`, `XAUUSD`: removing the `.java` before it is unwired in the GUI leaves those
tasks pointing at a missing method.

## Evidence
Reconstructed over 10,000 rows of `metrics/XAUUSD/OOS/metrics.csv` (snippet formula, `avgTrade` neutral
— not exported):
- **Calendar artifact:** `npDecay = (1 − NP_oos/NP_is)·100` on 10-y IS (2008-01-02…2017-12-29) vs 5-y OOS
  (2018-01-02…2022-12-30); zero decay → `npDecay = 50` → 14.3/100. 177 strategies with flat PF (1.150 →
  1.160): median `npDecay` **56.1 %**.
- **Inverts near zero:** 144 rows scoring ≥ 65 with NP(OOS) > 0 have median `sharpeDecay` **−136 %** at
  median Sharpe (IS) 0.24. rho(PF_IS, pfDecay) = **+0.62** — mostly regression to the mean.
- **Not a decay score:** only 20 % weight (pillar 4) + 9 % of pillar 2 compare samples; 71 % reads the
  OOS absolutely. Spearman vs NP (OOS) **+0.78**, Sharpe (OOS) **+0.75**, own pillar 4 +0.53.
- **Three implementations:** `compute()` (sorts/filters) weights pillar 4 40/30/30 with a `medianXS`
  MFE/MAE term, reads `Stability`/`PctDrawdown`/`ReturnDDRatio` from the full sample, builds a per-trade
  Sharpe against annualised thresholds, defaults `pfDecay` 0 (best) with no IS; `getValue()` (displayed)
  weights 50/50, no `medianXS`, reads OOS only, defaults 100 (worst).
- Not in `Export Data View`, so no metrics export ever carried it.
