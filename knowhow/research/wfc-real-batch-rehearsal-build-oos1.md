---
q: What does the step-17 criterion say on real batches, build in and oos1 out, and what does reading one cost?
kw: wfc rehearsal ensayo build oos1 real batches variant_trades.parquet PASA LIMBO NO PASA nivel nulo p_nivel XAUUSD cost seconds
tag: 🔬  date: 2026-10-14  see: wfc-dependence-moves-missed-pass
---
# The criterion on 29 real batches (build → oos1): 1 PASA, 10 LIMBO, 18 NO PASA
The rehearsal reads every `variant_trades.parquet` under the data root (29 mothers, 5.8 GB, 9
projects), never oos2. PASA 0.03 (0.38 without the level's null), LIMBO 0.34, NO PASA 0.62: the null
on the level turns 10 of 11 would-be PASA into LIMBO, as designed. The one PASA (NIKKEI wf3, p = 0.047)
sits on the alpha. All 16 XAUUSD mothers are NO PASA: the best build variant loses in oos1 (level < 0,
p_nivel 0.55-0.96). The truth of a real batch is unknown, so these are cell shares, not false-PASA
rates; mothers of one project are not independent (about 9 independent groups, not 29). Reading a
batch takes 1-4 s and 2.4 GB peak (cloud report on the largest, 360 MB: 3.7 s, 1.95 GB).

## Evidence
`python3 -m studies.optimisation.wfc.calibrate` (4 min, 8 workers) → `AlgoData/ledger/wfc_calibration.md`
§4. The synthetic rates moved between the 2026-10-07 and 2026-10-14 runs (false PASA 0.02 → 0.033, false
NO PASA 0.22 → 0.127; wfc config hash changed, criteria sha unchanged); both under the caps 0.40 / 0.25.
