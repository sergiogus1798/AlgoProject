---
q: How many independent markets are in a cross-market list, and which pooled rules are valid tests?
kw: effective number of markets, 13 forex pairs 4 independent, indices 1.6-1.9, Stouffer inflated variance, count of markets in profit, half the markets at the level of the original, structural list carried luck, step 10 rule, correlated markets
tag: 🔬  date: 2026-10-03  see: crosstf-mother-sibling-dependence, drift-term-biased-by-side, wfm-cells-are-not-independent
---
# Cross-market lists are 2-5 independent tests; «count of markets in profit» and Stouffer are not tests
Effective number (n²/Σρ², daily returns): **13 forex pairs ≈ 4.1-4.7, 7 indices ≈ 1.6-1.9**; structural lists
carry a half to a third of the family's carried luck (metals/crudes 12-13 → 3.0-3.6). Under synchronised timing
Var(Stouffer) = 1.6-2.8, so «Stouffer ≥ 1.65» passes 5-24 % of break-even strategies; «markets in profit» counts the
same bet several times. The weekly pooled t keeps sd 0.83-0.95 and is the usable statistic. With costs a no-edge
strategy fails every t-based rule (0-0.6 %). The owner's «half the markets at the level of the original» passes
**0 % of lucky no-edge strategies at 1.0× and ≤ 0.4-6 % at 0.5×**. Pooling markets that share a side also multiplies
the side bias of the drift term (break-even pooled t +0.4…+0.6, FPR 9-13 % for shorts on index lists).

## Evidence
- 📓 `AlgoData/scratch/calib_step10/report.md` (§ effective number, § null at scale) and `rules_proposal.md`;
  `corr.py` → `out/corr_per_main.csv`. Null: `null10.py`, markers `NULL10_FINAL`.
- The Stouffer, «markets in profit» and «half the markets» rules measured here were retired on 2026-10-07 (encargo 46); step 10 now judges nine facts P1-P9 from one joint year-shift tensor (`studies/transfer/crossmarket/travel/`, `joint-null-year-shift`). The effective-number and dependence findings still stand.
- Side bias: ``drift-term-biased-by-side.md`.
