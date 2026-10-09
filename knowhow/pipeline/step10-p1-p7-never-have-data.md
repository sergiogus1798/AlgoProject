---
q: Why can step 10 never give "Pasa"?
kw: crossmarket P1 fixed_distance sin dato, P7 tau_half e_principal, step 10 all limbo, units.py fixed raw project sqx, net_t_pooled negative, fill_mismatch invalid market XCUUSD XAGUSD AUDNZD
tag: 🔬  date: 2026-10-09  see: pipeline/step12-zbuild-not-centred-and-d1-sister-empty
---
# Step 10's P1 and P7 were «sin dato» for every strategy until 2026-10-09, so every survivor was Limbo
`crossmarket.verdict_csv` `fixed_distance` (P1) and `tau_half`/`e_principal` (P7) were «sin dato» in all
six runs. P1: `studies/transfer/crossmarket/travel/units.py::fixed` looked for the `.sqx` only under
`AlgoData/raw/<project>/`, where at step 10 there are none; it now also reads the project's databanks
on the workers. P7 waited for a step-8 producer of `e_principal` that was never written; crossmarket
now computes it itself (`travel/run.py::_e_principal`): the main market priced and shifted like any
other, `rules.per_market`'s e over V2. Both fixes are the owner's yes; both seen inside a run on 2026-10-09 (Evidence).
With data almost nobody passes P7 either. Step 10 also judges gross `z_conj`, while net was negative.

## Evidence
- 🔬 Inside a run (EURUSD H1, `Test_EURUSD_H1_tendenciaL_chk8`, 2026-10-09): `fixed_distance` 0, `e_principal` 0.10-0.11, `tau_half` 0.13 / -0.07 / 0.07: both now carry data.
- 🔬 P7 recomputed on the kept step-9 exports (2026-10-09): cal5 DAX40 M30, 25 strategies — `e_principal` 0.09-0.30 R/trade (median 0.20), `tau_half` median 0.19, max 0.53: 1 pass, 24 limbo, 0 fail. cal4 GBPUSD H1, 17 — `e_principal` median 0.14, `tau_half` median 0.08, max 0.19: 0 pass, 15 limbo, 2 fail.
- 🔬 `net_t_pooled` negative for every survivor in cal1-cal4 (means -1.7 to -4.1) and for 29 of 33 in cal5 (2026-10-08/09 calibration runs, reports under `AlgoData/reports/Test_<...>_calN/`).
- 🔬 Invalid markets declared in every run that includes them: XCUUSD (fill_mismatch 0.41-0.58 ATR), XAGUSD (0.48-0.68); AUDNZD (0.27) in cal2.
