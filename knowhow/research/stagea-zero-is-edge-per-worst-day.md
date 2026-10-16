---
q: Why does funded stage A give P(pass) = 0 for every combination and risk level — bug or result?
kw: P(pass) 0.000 everywhere, stage A all zero, best_score 0.0, hantec enhanced, risk_grid quota, open_risk_cap 0.5, worst_day units, target not reached in 126 days, all starts open, outcome -1, USATEC H1 pool
tag: 🔬  date: 2026-10-16  see: sqx-format/money-management-atr-fixed-risk, research/stageb-selector-p-reads-high
---
# Stage A's exact zero is a result: the edge per worst day is too small for the target in 126 days
With `factor = 1 / worst_day` a member's P&L is in «worst build days»; at level r the plan's target
needs `target / r` of them. The open-risk cap (`0.5 x daily_loss`) lets one member reach at most
r = 2.5 % on Hantec Enhanced (q = 0.5), so phase 1 alone needs 4 units and both phases 6, inside the
126-day horizon. Every start then ends **open** (target never met), never failed — the zero is the
count of passes, not a NaN or a breach. Combinations cannot help: the cap sums members' worst days, so
K members at q/K earn the average of their units, not more. Check first: a member's best 126-day
build gain in units against `(phase targets summed) / r_max`; below it, stage A is 0 by construction.

## Evidence
`Trade_USATEC_H1_pool_leaseWeb_20261016`, 6 members, 1,955 build days, 1,830 starts each, 2026-10-16:
best 126-day closed gain 2.0-4.0 units (whole build 7.6-14.1 units, ~1-2 units a year); worst closed
day 0.81-1.00 units and worst M5 low 0.60-0.91, so the MAE sizing is not what is off. At q = 0.5:
pass 0 / fail 0 / open 1,830 for every member. Lifting the cap: q = 1 (r = 5 %) gives P = 0-0.027 at
126 days and 0-0.24 at 252; q = 2 (r = 10 %) 0.05-0.12 at 126 days. Pre-e7f8d65 grid (r <= 1 %) is
q <= 0.2, further from the target. SQX lots fall 22 -> 10 over 2012-2019 (fixed $ risk / ATR), so the
dollar P&L is not compounded and the units are comparable across years.
