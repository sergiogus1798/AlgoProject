---
q: Does making the variants more alike change the WFC's false PASA or its missed PASA?
kw: wfc calibration own_noise dependence between variants null deviation rho 0.26 sd of rho sign-flip missed PASA false PASA batch real alike
tag: 🔬  date: 2026-10-07  see: wfc-top-persistence-sign-flip-null
---
# Dependence between variants moves the missed-PASA rate, not the false-PASA rate
Variants that are copies of one another widen the null of rho (sd 0.08 at own-noise 1.0, 0.23 at 0.4,
0.48 at 0.2), so a real edge is harder to tell from it; the false PASA of the written criterion does
not move (0.52 / 0.49 / 0.49). A family generator must reproduce the real dependence: own-noise 0.4
gives a null deviation of rho of 0.23 (5–95 % of families: 0.05 to 0.43), the real batches' 0.26
(0.09 to 0.41). Checking it is `AlgoData/ledger/wfc_calibration.md` §3.

## Evidence
`studies/optimisation/wfc/calibrate/config.yaml` (`family.own_noise`, `sensitivity.own_noise`).
Sharpe-0.5 edge without order, PASA (a): 0.89 at own-noise 1.0, 0.75 at 0.4, 0.78 at 0.2; with
order 0.97 / – / 0.93. The 0.26 comes from the reference run's real batches (proposal of step 17,
§4.2). Families of `tests/test_wfc_families.py` use 1.0 (the least alike).
