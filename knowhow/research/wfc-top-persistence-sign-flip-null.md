---
q: Why does step 17's level pass half of the no-edge families, and does its null decide?
kw: wfc level top median excess no null false PASA 0.49 0.44 LIMBO non-significant level sign-flip null on the level p_nivel level_alpha false NO PASA calibrate abre wfc_calibration 2.75 years Sharpe 0.5 persistencia del top retirada
tag: 🔬  date: 2026-10-07  see: wfc-dependence-moves-missed-pass, spp-decay-metrics-zero-edge-null
---
# The level of step 17 passes half of the no-edge families without a null — so the null decides
A no-edge family's median excess is symmetric around zero, so «above zero» holds half the time (0.44–0.49).
A sign-flip null on the level (`p_nivel` = (1 + #draws with top median ≥ observed) / (1 + draws), cut
`wfc.level_alpha`, weekly draws on net excess, the order's own) brings false PASA to 0.02–0.03. **It decides
(owner, 2026-10-08)**: PASA needs median > 0 AND `p_nivel` ≤ alpha; a positive, non-significant level is
LIMBO; a median ≤ 0 is NO PASA. The night of 2026-10-07 the code followed the proposal's table as written
(no null on the level) for one night: false PASA 0.44 against the cap 0.40, reverted. The price: up to 0.60
of Sharpe-0.5 families land in LIMBO. Retired 2026-10-07: the top's persistence and the Sharpe ratio OOS/IS.

## Evidence
`python3 -m studies.optimisation.wfc.calibrate`; table in `AlgoData/ledger/wfc_calibration.md` §1
(1 / 2.75 / 5 years outside): false PASA, written criterion 0.04 / 0.02 / 0.03, without the null on the
level 0.49 / 0.49 / 0.47; false NO PASA at Sharpe 0.5 (worse of with and without order) 0.30 / 0.22 /
0.12 under both. Caps are the Council's (false PASA 0.40, false NO PASA 0.25), not the owner's.
`tests/test_wfc_families.py` holds the families (no edge: «perverso» 0.043, «positivo» 0.050 at
α 0.05; PASA 0.047; flat winner PASA 0.79).
