---
q: Why does the monkey's repriced net exceed SQX's P/L, and what convention reproduces SQX from bars?
kw: monkey real_net higher than SQX; 45464 vs 38465; 6999 USD gap; repricing audit; residual cost misses spread and slippage; calibrate.charged; open-open convention; fill offset; swap per night notional entry fill; triple swap Friday 23:00; rollover boundary; reprice.py tolerance; half-tick rounding
tag: 🔬  date: 2026-10-06  see: export/fill-and-pricing, costs/per-task-costs, costs/where-the-spread-is
---
# The monkey never charges spread or slippage: they sit in SQX's fill prices, not in its residual "cost"
- `calibrate.charged()` = `v·size·(Close price − Open price) − P/L` is taken from SQX's **fills**, so it holds only swap (+ commission). `kernel.runs` then moves **bar open to bar open**. Gap = `v·size·(spread + 2·slippage)` per trade, exactly; the real run and every null are under-charged alike.
- SQX, long, market orders, reproduced from bars + the task's declared costs alone:
  `entry = round(Open[entry bar] + spread + slippage, tick)` · `exit = round(Open[exit bar] − slippage, tick)` ·
  `swap = PV·size·entry_fill·(pct/100/360)·nights` · `P/L = round(PV·size·(exit − entry) − swap, 0.01)`.
- `nights` = rollovers T (declared hour, Mon–Fri) with `open ≤ T < close`; the triple night counts 3. Card values, not fitted: 23:00, FRIDAY, PV 0.063137.
- Tolerance per trade: `0.02 USD + 2·tick·PV·size` (cents rounding + one tick per fill). The tick term is only spent when a declared cost falls within ~0.1 tick of a half tick (build: 304.11+106.44 → x.55, 106.44 → x.44); SQX then lands on either side, not reproduced bit for bit.
- Not measured here: shorts (all 1,312 trades are Buy), a non-zero commission, stops/targets, stamps off the bar grid (0 seen).

## Evidence
`scratch/encargo44/{audit,swap,reprice_check}.py` (`PYTHONPATH=. python3 …`), `Trade_NIKKEI225_M30_volatilidadL`, oos1, trades from
`reports/…/Results/2026-10-04/spread/trades.parquet` (C equals the raw `OOS` export field by field; A and B have no raw oos1 export left).

| USD | A 4.9.301 | B 16.11.437 | C 14.3.479 |
|---|---|---|---|
| SQX net / monkey `real_net` | 38,465.41 / 45,464.33 | 31,861.96 / 38,815.62 | 4,689.84 / 8,173.60 |
| gap | 6,998.92 | 6,953.66 | 3,483.76 |
| spread in the entry fill (4.7491) | 4,123.47 | 4,095.51 | 2,052.67 |
| slippage, entry (1.6622) | 1,443.23 | 1,433.44 | 718.44 |
| slippage, exit (1.6622) | 1,443.23 | 1,433.44 | 718.44 |
| tick rounding of the fills (6.41, 1.66) | −3.04 | −3.02 | −1.51 |
| point value by regression (0.06306–0.06309 vs 0.063137) | −7.97 | −5.71 | −4.27 |
| bar mislocated, lots, commission, swap, side | 0 | 0 | 0 |
| unexplained | 0.00 | 0.00 | 0.00 |

- Swap is inside the monkey's residual, so it adds 0 to the gap: 1,227.38 / 1,231.13 / 196.82 USD (6.26 / 6.38 / 2.01 per trade).
- Independent rebuild (no SQX price read) vs SQX, sum and worst trade: oos1 A +0.05 / 0.01, B −0.10 / 0.02, C +0.02 / 0.02; build A +0.24 / 0.18, B +0.53 / 0.15, C −0.46 / 0.15 (825 trades).
- Rejected: rollover 22:00 (28–30 USD/trade); 00:00 with Monday triple fits oos1 but fails build by 18–22 USD on B, C; `open < T ≤ close` fails by 16 USD (19 closes and 12 opens sit exactly on 23:00); notional at the exit price 0.75 USD.
- Build fill offsets: entry 4.10 (434) / 4.11 (391), exit 1.06 (385) / 1.07 (440); oos1 6.41 and 1.66 on all 487. Seven float32 rounding recipes tried, none reproduces the build split.
