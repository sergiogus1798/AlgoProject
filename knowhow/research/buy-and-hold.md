---
q: compare strategy against buy and hold, sizing convention one lot vs mean size vs volatility-matched, benchmark.py, occupancy exposure per day alpha
tag: 🔬  date: 2026-09-24  see: research/random-entry-nulls
---
# Buy and hold is three numbers; name the sizing convention or it is not a result
`studies/closing/exposure/benchmark.py` reports all three and headlines the volatility-matched one (the only one about
edge, not leverage). Report returns per unit of exposure and absolute, never one alone — a per-calendar-day
rate with flat days as zeros divides the edge by ~13.

## Evidence
`Strategy 1.10.39(1)`, XAUUSD `oos1` (2018–2022, M30); the strategy made 9,184 $.

| convention | lots | profit |
|---|---|---|
| one lot, start to end | 1.000 | 50,650 $ |
| strategy's mean position size | 0.903 | 45,711 $ |
| daily P&L volatility = strategy's | 0.141 | 7,133 $ |

"Beat B&H by 29 %" and "made a fifth of B&H" are both true. Occupancy: this strategy holds on 3.7 % of bars (4.2 h/week);
median of 757 `MC Trades` strategies 8.3 %.
