---
q: does in-sample parameter optimisation predict OOS? walk-forward correlation rho IS vs OOS, how many parameter tuples, unusable tuples fewer than 30 trades, report interval not coefficient
tag: 🔬  date: 2026-09-22  see: research/cloud-ranking-stability, research/eta-squared-vs-duplicates
---
# In-sample optimisation barely ranks the OOS (rho ≈ 0.19): report the interval, not the coefficient
The IS surface carries some information but not enough to rank on; best-IS-net-profit parameters buy almost nothing OOS.
rho was right at 11 points and useless there — only the interval narrows. About half of any batch is unusable
(< 30 trades in one sample): ask for twice the points you want.

## Evidence
`XAUUSD/Strategy 17.9.39`, M30, IS 2008–2017, OOS 2018–2022, 2,000 tuples across the whole design, all retested for real:

| points asked | usable | rho | 95 % interval | call |
|---|---|---|---|---|
| 11 | 9 | 0.18 | [−0.55, 0.75] | indeciso |
| 150 | 74 | 0.23 | [−0.00, 0.43] | indeciso |
| 600 | 297 | 0.22 | [0.10, 0.32] | indeciso |
| 2,000 | 1,001 | 0.19 | [0.13, 0.25] | no_fiable |

Interval excludes 0 and the 0.30 floor. Unusable tuples come from neighbourhood/coverage strata reaching corners where the strategy stops trading (design property).
- 🤔 Strategy or family? One strategy can't tell; run the unattended chain over the databank.
- ⚠️ PROVISIONAL XAUUSD costs (SQX defaults, not agreed Infinox). Rank correlation is robust to constant cost error but not re-run; `state.json` has `costs_provisional: true`.
