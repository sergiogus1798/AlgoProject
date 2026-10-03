---
q: Why does the funded verdict's selected null find the same portfolio as the real pool?
kw: selected null portfolio verdict; random admissible combinations same pool; monkey portfolio selected the same way; verdict percentile 50 % with real edge; null candidates per search; Q11 funded verdict null; calibration of the verdict under noise; planted edge percentile
tag: 🔬  date: 2026-10-02  see: research/hardest-null, research/post-selection-bias
---
# The selected null of the funded verdict measures the SEARCH, not the pool: with enough candidates it finds the same portfolio
The null of PLAN §14.3 runs the same selection (stage A score, diverse shortlist, stage B) on random admissible combinations
of the same pool, and the chosen combination's figure on oos1+oos2 is ranked among the null winners'. The pool's edge is in
the null too. So the percentile says «did the search choose better than chance among admissible combinations», never «do
these strategies have an edge». When one null search draws enough candidates to cover the pool's combinations it picks the
same portfolio and the percentile is ~50 % whatever the edge. `verdict.null_candidates` (default: as many as stage A
evaluated) is therefore part of the criterion the owner must set with the percentile (Q11) — and a small pool has no
usable selected null at all.

## Evidence
- `tests/test_portfolio_verdict.py`, synthetic pools of one-trade-a-day members, real search = every pair:
  - pure noise, 8 members, 40 seeds × 9 null searches of 28 pairs: mean percentile 0.542 (real path from each start day)
    and 0.465 (most pessimistic Monte Carlo); share at or above 0.9: 0.050 and 0.025 — calibrated.
  - planted pair (+0.3 R a day each, both stretches) among 12: null of **3** candidates → percentile 1.00 on both measures.
  - the same planted pair among 6 (15 pairs), null of **200** candidates → 100 % of the null searches chose that same
    pair; percentile 0.50.
- With stage-A scores saturated at 1.0 the ranking is decided by row order (stable sort): the real search and the null then
  shortlist different tied combinations — a tie-break by order, not a result.
- 🤔 To confirm on a real pool: how many distinct admissible combinations it has against the ~30,000 a GA run evaluates.
