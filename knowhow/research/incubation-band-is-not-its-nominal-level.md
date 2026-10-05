---
q: How often does M9's band of equal-length windows flag a healthy portfolio, and how soon a broken one?
kw: incubation; paper OOS; band of equal-length windows; own history; percentile 5; false alarm; independent windows; overlapping windows; monthly readings; repeated looks; edge removed; power; M9; portfolio/common/construct/incubation
tag: 🔬  date: 2026-10-05  see: research/selected-null-same-pool
---
# The band's «5th percentile» flags a healthy 12-month stretch about 10 % of the time, and 12 monthly looks flag it at least once in 1 of 4
PLAN §14.5 reads the fresh stretch against the band of equal-length windows of the portfolio's own
history. Ten years of history hold only ten independent 12-month windows: the percentile is estimated
from them, the overlapping count (thousands) is not the sample. One history's band is off by its own
luck in either direction. Read `independent` in the output, not `windows`; do not act on one flag;
any stopping rule must count the monthly looks. A lost edge needs a long stretch to show unless it was large.

## Evidence
`tests/test_portfolio_incubation.py`, figure `pnl`, band [5, 100], history 2,608 iid days at daily
Sharpe 0.2, 300 histories each with its own fresh stretch:
- healthy (same law), 12-month reading: flagged 9.7 % (nominal 5 %); flagged at least once in 12
  monthly cumulative readings: 24.3 %.
- edge removed (mean 0): flagged at 12 months 94.0 %; at least once in 12 readings 96.3 %.
- one history at a time, 400 fresh stretches each: real level 2.3 %, 5.8 %, 6.3 %, 12.0 % on four histories;
  fresh stretches resampled from the history's own days: 3.5-10.5 %.

## Counter-evidence
iid normal days and a very high edge (daily Sharpe 0.2 ≈ 3.2 a year): at a realistic 0.05 the 12-month
z-score of a vanished edge is 0.8 and the power is far lower — not measured. Real paths are autocorrelated.
