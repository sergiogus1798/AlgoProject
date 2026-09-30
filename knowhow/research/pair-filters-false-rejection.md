---
q: correlation filter rejects independent strategies, tail correlation negative bias Berkson, rolling window max correlation inflated, co-loss threshold 0.30 independent, how many independent pairs pass the portfolio pair filters, clique size of independent strategies, AlphaForge tail filter abs
tag: 🔬  date: 2026-09-30  see: research/post-selection-bias, sqx-format/daily-equity-bin
---
# Pair filters reject INDEPENDENT strategies: tail by construction, rolling maxima and co-loss by chance
- **Tail** = Pearson on the months where *either* series is in its worst 30 %: between two independent
  series it reads ≈ **−0.46** (selecting on "either is low" induces it — Berkson). Under `|ρ| > 0.30` it
  rejects 96 % of independent pairs over 10 years, 100 % over longer. The engine applies it one-sided
  (reject only ρ > 0.30; owner 2026-09-30, `config.yaml pairs.one_sided`). AlphaForge's `abs()` had the bug.
- **Rolling maxima and co-loss** at the owner's 0.30, on a 10-year build: only **75 %** of independent
  pairs pass every filter; K independent strategies form an admissible clique with ≈ 0.75^(K(K−1)/2) —
  K = 4 → 18 %, K = 6 → 1.5 %. A small admissible portfolio is partly the filters' noise, not redundancy.

## Evidence
- `pairs/measures.tail`, 2,000 independent normal pairs: mean −0.460 (36 obs), −0.456 (120), −0.455 (1,000);
  P(|tail| > 0.3) 0.85 / 0.96 / 1.00. Co-loss mean 0.25; P(> 0.30) 0.27 at 36 months, 0.09 at 120.
- 30 independent strategies, 120 months × 21 days (`pairs.table` + `search.admissible`, real config):
  328 / 435 pairs admissible (0.754). Share of pairs failing each filter: rolling Spearman whole 0.138,
  rolling Pearson whole 0.122, rolling Spearman recent 0.090, co-loss 0.083, rolling Pearson recent
  0.071, monthly Pearson/Spearman 0.002, daily 0. Rolling max |ρ| over 61 windows of 60 months > 0.30 in
  12.8 % of independent pairs (recent 9.2 %) vs 0.3 % for the whole-period monthly Pearson.
- Known-answer tests: `tests/test_portfolio_pairs.py` (tail never rejects 20 independent strategies).
