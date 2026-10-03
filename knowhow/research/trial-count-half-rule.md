---
q: When does trials.independent over-count the independent trials of a family?
kw: number of independent trials wrong, core.surface.trials.independent inflates count, half rule no cluster above half, dominant family of variants, one blob 16 clusters, silhouette 0.01, n_eff too high deflated Sharpe too harsh, cluster_k_max too small ValueError max() arg is an empty sequence, jsharpe number_of_clusters unstable seed
tag: 🔬  date: 2026-10-02  see: research/psr-dsr-two-conventions-jsharpe
---
# `trials.independent` is exact on balanced families and over-counts when one family holds more than half
On panels of equal blocks it returns the true count (2, 4, 8) where jsharpe's k-means flips with its seed (8 blocks: 4, 8, 8, 2, 8, 4, 8, 4). But its rule «no cluster above half the variants» forbids the true answer whenever one family dominates, and it then cuts that family until the rule holds: 30+5+5 variants read **14** trials (silhouette 0.147; the true split scores 0.531 and is refused), a single blob of 40 reads **16** (silhouette 0.014). The error is on the harsh side — a larger N raises the deflated Sharpe's benchmark — which is the side the docstring chose, but the count is then an artefact, and **the returned `silhouette` is the tell: below ~0.2 there is no structure behind the number.** **Owner decided 2026-10-02: the rule stays** (count unchanged); with a small `k_max` and no admissible split (one blob, `k_max=10`) it now raises a clear `ValueError` naming k_max and the dominant family instead of `max() arg is an empty sequence`; `cscv`'s 40 hides that.

## Evidence
`python3 tests/test_inference_vs_jsharpe.py` (panels: 300 weeks × 40 variants, ρ=0.8 inside a
block, 0 across, seed 42; `K_MAX=40`). Ours / jsharpe over 8 seeds / truth: two_blocks 2 / 2 / 2;
four_blocks 4 / 4 / 4; eight_blocks 8 / [4,8,8,2,8,4,8,4] / 8; one_dominant 14 / 3 / 3; one_blob
16 / 39 / 1. one_dominant by k: silhouette 0.465 (k=2), 0.531 (k=3), then 0.164…0.143 with the
largest cluster 29→20; first admissible k is 10. Effect on the bar: `expected_max_sharpe(σ, 3)` =
0.85 σ, `(σ, 14)` = 1.74 σ. The error text is pinned in the same test (OPEN.md #96).
