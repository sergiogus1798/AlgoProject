---
q: Does the CSCV's LIMBO rule (loss above its null's p95) ever fire on correlated variants?
kw: cscv p_perdida null p95 limbo p_perdida_sobre_p95 p_perdida_null_pct 0.25 cut removed seesaw correlated panel weekly Sharpe 0.03 nulo.p_perdida_p95 never fires
tag: 🔬  date: 2026-10-08  see: cscv-chosen-point-slope-seesaw, post-selection-bias
---
# CSCV LIMBO reads the null's p95, and on correlated variants it almost never fires
Trap: the fixed cut «P(loss) ≥ 0.25» sat below the null's median (0.36–0.38, no-edge, Sharpe 0.03), so seesaw alone gave LIMBO; replaced 2026-10-08 (owner; `state.p_perdida_limbo` gone) by «P(loss) strictly above the p95 of its own null's» (`state.p_perdida_null_pct` = 95, fact `cscv.p_perdida_sobre_p95` = 1, note `cscv.nulo.p_perdida_p95`).
Measured: the null is centred on the panel's own median Sharpe, so the rule fires ~5 % on independent no-edge columns but ~0 % on correlated ones (0.5 % at correlation 0.2, 0 % at 0.6+). Real batches are correlated: LIMBO practically never fires; if the null's p95 ≥ 0.5 it cannot.
NO PASA (`p_perdida` ≥ 0.5) fails 29 % of no-edge correlated panels at Sharpe 0.03, 51 % at 0.

## Evidence
`studies/optimisation/cscv` on synthetic panels (no `variant_trades.parquet` existed under the data root on
2026-10-07, so nothing trade-based has run on a real mother). Without resampling the seesaw alone pushes
the null's P(loss) near 1; with the equalised columns redrawn it sits near 0.5 (POSSIBLE_IMPROVEMENTS §1).
Measured 2026-10-08 (60 variants × 400 weeks, 100 draws, 300–400 panels per row; table and method in
`studies/optimisation/cscv/README.md`; the state rule asserted in `tests/test_cscv.py`):

| panel | over null p95 | LIMBO | NO PASA |
|---|---|---|---|
| no edge, independent, Sharpe 0.10 | 5.2 % | 3.0 % | 6.2 % |
| no edge, correlated 0.2, 0.10 | 0.5 % | 0 % | 6.0 % |
| no edge, correlated 0.6, 0.03 | 0 % | 0 % | 29.3 % |
