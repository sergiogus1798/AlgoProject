---
q: parameter cloud smooth but ranking reshuffles each year, in-sample tuning useless, period-to-period Spearman, Sobol DICrossPeriod1, CSCV vs chronological walk-forward correlation f_y rho
tag: 🔬  date: 2026-09-24  see: research/trade-filter-parameter-space, research/is-optimisation-vs-oos
---
# A smooth, profitable cloud can still reshuffle which member is best every year
Smooth within a window does not mean the shape carries into the next. Here the family makes money but which member
is best is noise, so in-sample tuning of this logic buys nothing. CSCV (`walkForwardCorrelation`) is deliberately
blind to chronology; `f_y` and rho are chronological per period — both are needed.

## Evidence
`Strategy 17.9.39` batch (998 variants after the trade floor), per calendar year over build + `oos1` (`oos2` untouched):

| | |
|---|---|
| surface smoothness | r² 0.90 full quadratic; neighbour disagreement 0.15 IQR |
| who moves it | `DICrossPeriod1` alone, Sobol total 0.89 of seven live parameters |
| year-to-year Spearman between variants | median +0.11, negative in 5 of 14 years |
| share of cloud profitable in a year | 0.00 (2009) to 1.00 (2014) |

🤔 Mechanism: one year dominates each window's ranking, so a fitted ranking is mostly "how each variant did in the window's best year".
