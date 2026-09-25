---
q: stop-fill slippage assumption, ATR stop study, stop commission round trips, pooling two populations one databank, range restriction conditioning on a metric, significance at n=10000, FDR effect size
tag: 🔬  date: 2026-09-04  see: research/post-selection-bias, research/is-proxies-top-decile
---
# Research lessons: stop fills, range restriction, p at large n
- Never present an MAE-threshold stop simulation without slippage sensitivity; the tighter the stop, the more the answer is the assumption.
- A stop moves an exit, it adds no round trips: commission is constant in the number of trades.
- Check a databank for two structurally different populations before pooling exit stats (`knowhow/locations/`).
- A predictor ranking from the full population doesn't say what to filter on second: recompute inside the survivors.
- At n≈10,000 report FDR/family-wise correction and argue from effect size, never from p.

## Evidence
- ATR-stop study (`archive/studies/atr_stop_study.py`): fill at stop → PF 2.09 at 0.5×ATR; 0.25×ATR slippage → PF 1.49, net −37 %; a 3×ATR stop lost only 11 %.
- Range restriction, `XAUUSD/OOS` 10,000 strategies (`AlgoData/metrics/XAUUSD/OOS/metrics.csv`, report
  `AlgoData/reports/XAUUSD/OOS/2026-09-04/`; `python3 -m tasks.reports.is_oos --project XAUUSD --databank OOS`).
  Dedup checked: 10,000 distinct names, 2 byte-identical metric vectors. `Sharpe Ratio (IS)` → `Profit factor (OOS)`
  ρ +0.223 overall, +0.088 inside its own top 20 %, where another metric leads. Hence `tasks/reports/panel.html` recomputes.
- |r| > 0.020 clears two-tailed 5 % at n≈10,000: 19 of 21 IS metrics "pass" vs OOS PF. Use `tasks/analysis/correlations.py:discoveries`.
- 🤔 Population was generic strategies, not template-built (owner decision 2026-09-04, `knowhow/sqx-drive/`); untested for template populations.
