---
q: Why do random-entry monkeys fail the floating-risk rules (worst MAE, worst day in R) far more than real strategies?
kw: monkey MAE 5R, oos_worst_trade_mae_r, oos_worst_day_r, falsePositives sizing donor atr, matched size leaks ATR of real entry, size fitted to volatility, monos mueren por riesgo flotante, CV size x ATR
tag: 🔬  date: 2026-10-04  see: nulls-seed-fresh-per-run
---
# A monkey that keeps its donor's size is mis-sized, and the floating-risk rules measure that
A real trade's size is `c / ATR(entry)`. Moved to a random bar it keeps the size and meets another
volatility, so its floating loss in R is no longer bounded by any sizing rule. Reading
`oos_worst_trade_mae_r` or `oos_worst_day_r` on such a monkey understates the false-positive rate
of the chain. `studies/screening/falsePositives` offers `monkeys.sizing=atr` (re-sized at the
monkey's own entry, engine ATR 14); report both and let the owner pick. Rules on net, t and trade
count are barely moved by it.

🔬 2026-10-06 On a 90-trade strategy (USA500 H1) real lots average 19.4 and ATR-sized draws 31.1, because it enters in high volatility: the ATR-sized draw matches the median risk, not the mean lots.

## Evidence
`Test_XAUUSD_donchianUpperCrossUp2_H1/Results` harvest 2026-10-01, 300 donors x 10 monkeys, seed 9,
criteria.yaml of 2026-10-04 (H1: t >= 1.65 is limbo, no pass):
`python3 -m studies.screening.falsePositives.report --project Test_XAUUSD_donchianUpperCrossUp2_H1 --databank Results --feed XAUUSD_M1 --seed 9 --set monkeys.per_donor=10 [monkeys.sizing=atr] [monkeys.rung=timing]`

| rung, sizing | fail worst MAE >= -5R | fail worst day >= -5R | t >= 1.65 | alive after step 8 |
|---|---|---|---|---|
| real donors | 4 / 300 | 0 / 300 | 0 / 300 | 0 / 300 |
| free, donor | 2,172 / 3,000 | 1,435 | 31 | 14 |
| timing, donor | 2,369 | 1,747 | 29 | 17 |
| free, atr | 538 | 520 | 40 | 36 |

One donor's OOS trades: CV(size) 0.43, CV(size x ATR14) 0.13 — sized by volatility. The bar-based
MAE the monkey gets is sound: on the donor's real trades it correlates 0.9998 with SQX's, median
ratio 0.94. What is left under `atr` (18 % fail) is the ATR period not being the strategy's, the
resampled holds and the Friday close the monkey does not have.
