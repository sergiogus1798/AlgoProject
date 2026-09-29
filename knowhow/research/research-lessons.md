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
The rules stand on their own; the figures in the Evidence come from the old project's export and
cannot be reproduced from today's data root (OPEN §12, closed 2026-09-29 by this label).

## Evidence
- ATR-stop study (old `archive/studies/atr_stop_study.py`, deleted 2026-09-26, in git history) —
  🤔 **restated 2026-09-29 (issue 13): only the slippage delta is defensible.** `PF 2.09 at
  0.5×ATR` is an **in-sample** number: the pool was selected by SQX search over 2008–2017, the
  script restricts to that same window, and 0.5×ATR is the argmax over an 11-point grid
  (`N_GRID = 0.5…3.0 step 0.25`) landing on the grid's own edge — a selected maximum, with no
  out-of-sample confirmation and no multiple-testing correction, on strategies themselves produced
  by search. Do not quote `PF 2.09`, `PF 1.49` or `−37 %`/`−11 %` as levels. What survives: at a
  single slippage value (`SLIP_REF = 0.25×ATR`, not a curve), the tighter stop degraded **more**
  than the wider one (−37 % vs −11 %) — a within-study *relative* comparison, not a claim about
  either stop's real profit factor. A curve over slippage, out of sample, would be needed before
  this says more than that.
- Range restriction, `XAUUSD/OOS` 10,000 strategies (`AlgoData/metrics/XAUUSD/OOS/metrics.csv`, report
  `AlgoData/reports/XAUUSD/OOS/2026-09-04/`; `python3 -m studies.screening.isOos.report --project XAUUSD --databank OOS`).
  Dedup checked: 10,000 distinct names, 2 byte-identical metric vectors. `Sharpe Ratio (IS)` → `Profit factor (OOS)`
  ρ +0.223 overall, +0.088 inside its own top 20 %, where another metric leads. Hence `studies/screening/isOos/panel.html` recomputes.
- |r| > 0.020 clears two-tailed 5 % at n≈10,000: 19 of 21 IS metrics "pass" vs OOS PF. Use `studies/screening/analysis/correlations.py:discoveries`.
- 🤔 Population was generic strategies, not template-built (owner decision 2026-09-04, `knowhow/sqx-drive/`); untested for template populations.
