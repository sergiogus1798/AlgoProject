---
q: Why does the portfolio rank search (M3) pick a single strategy, K = 1, on a pool of similar strategies?
kw: real.py K=1; CARTERA ELEGIDA K=1; rank score ranks4; RAR of a combination is the mean of its members; regression slope linear; equal weight never beats best member on RAR; near-clones pool; Test_nikkei_ref; signed ranks Q10; diversification only through R-cubed gain-to-pain P(losing year)
tag: 🔬  date: 2026-10-05  see: research/selected-null-same-pool, research/pair-filters-false-rejection
---
# An equal-weighted combination's RAR is exactly the mean of its members' RARs: one of the four ranks can never prefer a combination to its best member
RAR is the slope of a line fitted to the cumulative P&L, and a slope is linear in the path. A combination
therefore never outranks its best member on RAR, and the Q10 score lets it win only through R-cubed,
gain-to-pain and P(losing year, mostly ties under `calendar`): joining must cut the drawdowns by more than
the RAR it gives up. Near-clones do not, and the search answers K = 1 — the objective working, not a bug
in the pair screen. Rewarding diversification as such would be a change to Q10 (the owner's), not a knob.

## Evidence
- `Test_nikkei_ref` (test root, six pair thresholds relaxed to 0.90, 2026-10-05): 10 members, monthly |ρ|
  0.64-0.97; 103 admissible combinations (10 singles, 29 pairs, 37 of 3, 22 of 4, 5 of 5); chosen
  `c9b701e7` alone, score 0.871; the best pair 0.864, the best trio 0.837. (`real.shift_minimum:
  metric`, the owner's; the unchosen `score` reading gave the same order before it was removed.) `--base` on that single: 0 of 9 enter (every finite Sharpe increment < 0).
- `tests/test_portfolio_planted.py`: with two good, nearly independent members the pair wins (top R-cubed,
  top gain-to-pain, lowest P(losing year)) and exactly the singles can sit above it on RAR.
- Linearity: `metrics.table` computes `rar = (equity - mean) @ centred / (centred @ centred)` and
  `equity = cumsum(weights @ unit)`.
