---
q: Which P(pass) of stage B's winner may be reported — the one that chose it, or a re-draw?
kw: winner's curse, best of many noisy minima, stage B p inflated, p_fresh, selector_p, build_p, shortlist x risk grid, stability mean, common random numbers, funded_b verdict.json
tag: 🔬  date: 2026-10-04  see: research/post-selection-bias, research/selected-null-same-pool
---
# The figure that picks stage B's winner reads high; report its re-draw
`winner["p"]` is the highest of shortlist × risk-setting Monte Carlo estimates, so it carries its own
sampling error upward. Report `winner["p_fresh"]` (the stability re-draws' mean, fresh paths, a spawned
seed); the verdict's `build_p` is that one and `selector_p` keeps the other. The bias only shows when
candidates are close in true P(pass): about one single-estimate standard error. Where one candidate
dominates it is nil — so a real pool's bias is unknown until measured, never assumed zero.
Risk settings of one combination share their paths (one draw per flavour), so the maximum over settings
adds little; the maximum over combinations, drawn apart, is what inflates.

## Evidence
`tests/test_portfolio_fixes_latent.py::test_stage_b_reports_the_winner_on_fresh_paths` (2026-10-04, 400
paths, 8 finalists × 9 settings, single-estimate se 0.021):
- six clones (one true P(pass)), 100 seeds: selector − independent re-draw **+0.0245 ± 0.0012**; re-draw
  against a second re-draw −0.0019 ± 0.0015. Through `funded_b.build`, 30 seeds: +0.0231 ± 0.0018
  before, +0.0019 ± 0.0023 reported.
- five independent noise members, 4 finalists, 150 seeds: +0.0004 ± 0.0018 — one combination wins on
  its realised build drift almost every time, no curse to see.
Both figures are minima over flavours and block lengths, so that (pessimistic) bias cancels in the difference.
