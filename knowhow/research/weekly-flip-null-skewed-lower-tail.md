---
q: Does the weekly sign-flip null keep its size on skewed weekly excess, for a median statistic?
kw: engines weekly flip null over-rejects lower tail median of cells skewed lottery weeks p_menos 13.3 skew_warn wfm L1 straddle two-week blocks sign flip size
tag: 🔬  date: 2026-10-07  see: wfc-top-persistence-sign-flip-null, contemporaneous-dependence-bootstrap
---
# The weekly sign-flip null is exact for Spearman on skewed weeks, but its lower tail over-rejects for a median
Steps 17, 18.5 and 19 flip whole weeks (one sign for every unit). On correlated Gaussian no-edge panels it
holds its nominal 5 % for Spearman (5.1 / 5.0) and for the median of the units' totals (4.6 / 4.6). On a
mean-zero lottery (one week in ten wins 9, the rest lose 1, Student-t(3) sizes) Spearman still holds
(5.3 / 5.1) but the **median's lower tail rejects 13.3 %** (upper 2.2 %). So WFM's L1 `p_menos` (a median) can
call NO PASA on a positively skewed mother by chance alone; `wfm.null.skew_warn` (1.0, provisional)
warns, it does not change the state. Do not read a small `p_menos` of a median without the weekly skewness.

## Evidence
`engines/weekly/README.md` and `tests/test_weekly_flip.py`: 2,000 no-edge panels of 143 weeks × 30 units,
199 draws, nominal 5 %. `facts.asimetria` / `summary.asimetria` of the WFM carries the skewness read.
Not measured: how the size moves with 2-week blocks (`straddle_*`) or with the draws set above 199.

**Drift (decided).** The excess these weeks hold subtracts the PROJECT's drift, not the WFC proposal's formula: the gate's (year the trade
opens in, 1/ATR-weighted blind trade of the same hold), the same as steps 8-14. Owner, 2026-10-08, kept on purpose;
see `engines/weekly/README.md`. Do not "fix" it to the per-bar calendar-year sum.
