---
q: Why can step 10 never give "Pasa"?
kw: crossmarket P1 fixed_distance sin dato, P7 tau_half e_principal, step 10 all limbo, units.py fixed raw project sqx, net_t_pooled negative, fill_mismatch invalid market XCUUSD XAGUSD AUDNZD
tag: 🔬  date: 2026-10-09  see: pipeline/step12-zbuild-not-centred-and-d1-sister-empty
---
# Step 10's P1 and P7 are «sin dato» for every strategy, so every survivor is Limbo
`crossmarket.verdict_csv` `fixed_distance` (P1) and `tau_half`/`e_principal` (P7) were «sin dato» in all
six runs. P1's cause: `studies/transfer/crossmarket/travel/units.py::fixed` looks for the strategies'
`.sqx` under `AlgoData/raw/<project>/`, and at step 10 there are none (0 files; only CrossTF folders
appear later). Not fixed: making P1 measure changes what a rule measures — owner's decision.
Step 10 also judges gross `z_conj`, while net was negative.

## Evidence
- 🔬 `net_t_pooled` negative for every survivor in cal1-cal4 (means -1.7 to -4.1) and for 29 of 33 in cal5 (2026-10-08/09 calibration runs, reports under `AlgoData/reports/Test_<...>_calN/`).
- 🔬 Invalid markets declared in every run that includes them: XCUUSD (fill_mismatch 0.41-0.58 ATR), XAGUSD (0.48-0.68); AUDNZD (0.27) in cal2.
