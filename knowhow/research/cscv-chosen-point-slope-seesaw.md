---
q: Why is the CSCV chosen-point IS/OOS slope negative even when PBO is low?
kw: CSCV decay panel negative slope good PBO contradiction, chosen variant IS vs OOS regression negative, PBO 7.7% but slope negative is that correct, complementary halves mechanical correlation
tag: 🔬  date: 2026-09-30  see: research/is-optimisation-vs-oos
---
# The CSCV's per-chosen-point IS/OOS slope is negative by construction, more so when the edge is real
A low PBO beside a strongly negative slope on the "decay" scatter (the chosen variant's IS score
against its own OOS score, one point per partition) is not a contradiction. Every partition's two
halves are complementary, so regressing only the *winner*'s two scores is a seesaw: on pure noise
it already reads about -0.57, and it gets *more* negative (to -0.99) the more real the edge is.
Read the **aggregate** degradation line instead (β and adjusted R², facts `cscv.beta` and `cscv.r2`,
`studies/optimisation/cscv/measure/outputs.py`) — it reads ~0 on noise, positive when order survives.

## Evidence
`Strategy_16.9.76` (`Test_USDJPY_donchianUpperCrossUp_H1`, 500 variants, 16 blocks, argmax):
PBO 7.7 %, aggregate slope +0.48 (r² 0.24) — the chosen-point decay scatter's own fit reads
slope -0.90, r -0.82. `carry`'s docstring (the pre-2026-10-07 `measure/cscv.py`, rewritten since): pure noise measures -0.57; "on a panel
with one genuinely good column it reads -0.99 -- more negative where the edge is real."
