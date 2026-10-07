---
q: Why does a no-edge cross-timeframe sibling clear z 1.65 so often when its mother did, and how is it corrected?
kw: crossTF sibling z, mother sibling correlation, z_new, lucky mother, false positive 17-31 %, monthly P/L correlation rho, rounding clamped siblings, crosstf.combined.z_new, limbo 1.65 pass 2.33
tag: 🔬  date: 2026-10-02  see: sqx-drive/crosstf-scaling-coefficients, sqx-drive/crosstf-period-source, crossmarket-effective-markets, post-selection-bias
---
# A sibling timeframe is not an independent test of its mother: correct with `z_new`
Given a mother above 1.65 under no edge, a no-edge sibling clears 1.65 in **17-31 %** of cases (z-correlation
0.32-0.48), not 5 %: they trade the same bars. `z_new = (z − ρ·z_mother)/√(1−ρ²)`, ρ = the pair's monthly-P/L
correlation clipped to [0, 0.95], restores ≈ 5 % at every likeness band (2.7-6.3 %; `combined.z_new` > 1.65 in
3.6-5.7 %). Weak spot: pairs with ρ > 0.9 show 10 % given a lucky mother (n = 39). 🔬 Rounding or clamped siblings
do not inflate false positives (z_new > 1.65 in 4.5-5.7 % vs 4.0-5.2 %): no sibling is discarded for rounding.
Proposal (agent's, owner pending): `crossTF.combined.z_new` pass ≥ 2.33, limbo ≥ 1.65. Readings: `unusable` ·
`silent` · `no_data` (< 30 oos1 trades) · `survives` · `inherited` · `fails`.

## Evidence
- 🔬 Replacement built beside (encargo 47, NOT live): mother and siblings share the same random runs, so dependence
  cancels in `z_delta`/`z_build` (`studies/transfer/crossTF/tf/`). Facts to know:
  - Joint null, 300 edgeless mothers: mean z between −0.09 and +0.02, sd 0.93-1.04, rejection at 5 % between 3.0 % and
    5.7 % (`tests/test_crosstf_tf_null.py:30,98`). A calendar cell with a data hole in ANY timeframe is dropped in all
    (`tf/null.py:42`).
  - `ret` is in each timeframe's own R (doctrine sizes with that timeframe's ATR): a sibling with the same price P/L as
    its M30 mother reads ret ≈ 0.57 on H1 and ≈ 1.70 on M15 (encargo 47, synthetic battery). Owner decision K-1 pending.
  - Autopilot facts are numbers: pass = 1, limbo = 0, fail = −1, a missing fact is limbo (`pipeline/autopilot/tffacts.py:8`).
  - A YAML key named `null:` parses as a None key and broke the config fingerprint, hence `tf.runs`.
- 📓 `AlgoData/scratch/calib_step12/report_addendum.md` §C-D, §J; `null12_scale_summary.txt` (68 null jobs, zero-cost twin,
  seed 20261002). The first 8 jobs gave the numbers above; read the summary for the full 68.
- Code: `studies/transfer/crossTF/verdict.py`; facts `crossTF.combined.n_tested`, `.z_new`, `.z_new_max`.
- 🤔 A same-bets M30 sibling adds little by construction; whether it should count is an owner question.
