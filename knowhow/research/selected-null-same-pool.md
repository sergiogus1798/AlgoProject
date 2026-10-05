---
q: Why does the funded verdict's selected null find the same portfolio as the real pool?
kw: selected null portfolio verdict; no discrimina; NO SE PUEDE JUZGAR; fewer than 20 admissible combinations; null of size K; random admissible combinations same pool; monkey portfolio selected the same way; verdict percentile 50 % with real edge; null candidates per search; Q11 funded verdict null; calibration of the verdict under noise; planted edge percentile
tag: 🔬  date: 2026-10-02  see: research/hardest-null, research/post-selection-bias
---
# The selected null of the funded verdict measures the SEARCH, not the pool: with enough candidates it finds the same portfolio
The null of PLAN §14.3 runs the same selection (stage A score, diverse shortlist, stage B) on random admissible combinations
of the same pool, and the chosen combination's figure on oos1 (oos1+oos2 pooled until 2026-10-05) is ranked among the null winners'. The pool's edge is in
the null too. So the percentile says «did the search choose better than chance among admissible combinations», never «do
these strategies have an edge». When one null search draws enough candidates to cover the pool's combinations it picks the
same portfolio and the percentile is ~50 % whatever the edge. `verdict.null_candidates` (default: as many as stage A evaluated)
is therefore part of the criterion the owner sets with the percentile (Q11) — and a small pool has no usable selected null: on the
real path (random combinations of the chosen K) under 20 admissible ones → `verdict/null.py::bar` says `no_discrimina`.

## Evidence
- Real path's floor: with D < 20 distinct admissible combinations of size K the chosen one is ≥ 5 % of the draws, so the
  95th percentile is its own figure; the verdict is «NO SE PUEDE JUZGAR», neither pass nor fail (K = 1 needs > 20 members).
  Funded analogue (`decide.funded_oos1`): the share of null searches choosing the same combination ≥ 1 − the bar.
- `tests/test_portfolio_verdict.py`, synthetic pools of one-trade-a-day members, real search = every pair:
  - pure noise, 8 members, 40 seeds × 9 null searches of 28 pairs: mean percentile 0.542 (real path from each start day)
    and 0.465 (most pessimistic Monte Carlo); share at or above 0.9: 0.050 and 0.025 — calibrated.
  - planted pair (+0.3 R a day each, both stretches) among 12: null of **3** candidates → percentile 1.00 on both measures.
  - the same planted pair among 6 (15 pairs), null of **200** candidates → 100 % of the null searches chose that same
    pair; percentile 0.50.
- With stage-A scores saturated at 1.0 the ranking is decided by row order (stable sort): the real search and the null then
  shortlist different tied combinations — a tie-break by order, not a result.
- 🔬 2026-10-05, `Test_nikkei_ref` in the test root (10 near-clone members, pair thresholds relaxed to 0.90, not a result):
  K = 1 → 10 admissible singles, the chosen one 9.8 % of 10,000 draws → `no_discrimina`; a forced K = 3 → 37 admissible
  trios, judged (percentile 91.6 %, under the bar). `tests/test_portfolio_verdict_real.py`: a random trio of 12 noise members
  passes in 5.0 % of 200 seeds; 4 members at K = 2 (6 pairs) → `no_discrimina`.
- 🤔 To confirm on a real pool: how many distinct admissible combinations it has against the ~30,000 a GA run evaluates.
