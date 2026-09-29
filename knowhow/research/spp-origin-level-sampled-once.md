---
q: SPP original tuple level never sampled, theta-zero alone in its cell, SPP step grid misses original value, argmax equals original, plateau width 1 spike, two-parameter surface, marginal profile biased, spp surface grid
tag: 🔬  date: 2026-09-27  see: research/eta-squared-vs-duplicates, research/post-selection-bias
---
# An SPP's step grid can miss θ₀'s own level: then θ₀'s level holds θ₀ alone
SQX lays each parameter's SPP levels on a step grid (±35 % in 18 steps) that need not contain the
original value. When it does not, the only tuple at θ₀'s level is θ₀ itself (permutation −1), and
any aggregate by level — a marginal curve, a two-parameter cell — is the in-sample pick's own score:
θ₀ reads as argmax and a width-1 "plateau" by construction. Leave permutation −1 out of every
aggregate and keep its level on the axis; an empty cell then says "no neighbour was sampled here".

## Evidence
`Test_USDJPY_donchianUpperCrossUp_M30`, `raw/.../SPP_IS|SPP_OOS/2026-09-27/spp`, 3 strategies,
~10,200-11,200 permutations each. Tuples other than θ₀ at θ₀'s level: `BBerDeviation1` (2.9) 0 in all
six runs — its levels run 1.89, 2.01, 2.13 … (step 0.12); `BBerDeviation2` (2.8) 0; and
`CBlc_ClsCrsDCerInt21` (29) 0 on 9.25.72 and 9.27.83. Before the fix, `run.read`'s marginal profiles
on SPP_IS gave for exactly those parameters argmax = original, plateau from = to = original, i.e.
`spike: true` in the design brief — an artefact, not a reading.

Fixed 2026-09-29 (`OPEN.md` #79): `studies/breakage/spp/inputs/export.without_original` is the one
shared exclusion, called by both `run.read` (before `profile.marginal`) and `surface.py`'s cells.
Every brief written before this date was made with the bug and needs re-running from the stored SPP
export.
