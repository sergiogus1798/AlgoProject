---
q: Why does the monkey's repriced net exceed SQX's P/L, and what convention reproduces SQX from bars?
kw: monkey real_net higher than SQX; 45464 vs 38465; 6999 USD gap; repricing audit; calibrate.charged; open-open convention; fill offset; swap per night; triple swap Friday 23:00; rollover boundary; reprice.py tolerance; half-tick rounding
tag: 🔬  date: 2026-10-12  see: export/fill-and-pricing, costs/per-task-costs, costs/where-the-spread-is
---
# The monkey never charges spread or slippage: they sit in SQX's fill prices, not in its residual "cost"
- `calibrate.charged()` = `v·size·(Close price − Open price) − P/L` is taken from SQX's **fills**, so it holds only swap (+ commission). `kernel.runs` then moves **bar open to bar open**. Gap = `v·size·(spread + 2·slippage)` per trade, exactly; the real run and every null are under-charged alike. Closed for the gate only (`engines/nulls/windowed.py`); the `engines/nulls` simulate path and its ~35 importers still charge none.
- SQX, long, market orders, reproduced from bars + the task's declared costs alone:
  `entry = round(Open[entry bar] + spread + slippage, tick)` · `exit = round(Open[exit bar] − slippage, tick)` ·
  `swap = PV·size·entry_fill·(pct/100/360)·nights` · `P/L = round(PV·size·(exit − entry) − swap, 0.01)`.
- `nights` = rollovers T (declared hour, Mon–Fri) with `open ≤ T < close`; the triple night counts 3. Card values, not fitted: 23:00, FRIDAY, PV 0.063137.
- Tolerance per trade: `0.02 USD + 2·tick·PV·size` (cents + one tick per fill); the tick term is spent only when a declared cost falls within ~0.1 tick of a half tick (build: 304.11+106.44 → x.55, 106.44 → x.44); SQX lands on either side.
- 🔬 Verified 2026-10-12: shorts, swap in points, SizeBased commission, EndTest (a bug, fixed: fills at SQX's price). Unverified: short SL, PT, PercentageBased commission. Non-repricer gaps: see Evidence.


## Evidence

### 2026-10-12 reconciliation, encargo 65 §8 (whole exports, no SQX touched)
  - Shorts (`raw/Test_USDJPY_donchianUpperCrossUp_M30`, 47,610 trades): one PV for both sides; SQX **sells at the bar open and buys back at open + spread**, so the spread sits on the BUY fill (a short's exit), not on its entry as `pnl()` puts it. Same P/L (99.994 % within 0.02 USD); only a short stop would tell them apart.
  - Swap in points: short -10.4 pt/night recovered as -10.400 (5 %-95 % -10.403/-10.397), long 0 as 0.000, triple night on WEDNESDAY = 3 x; unit = tick_step x PV x lots.
  - SizeBased commission 5 USD/lot: 522,000 longs of `Test_USDJPY_M30_doubleROCLong_10k` reproduced to 0.01 USD (|err| p99 = 0).
  - **EndTest was a bug**: the trade still open when the window ends is closed at SQX's own price, not a bar open (`AT_PRICE` now). USA500 batch: 1,001 of 1,004 variants, 240 USD off each -> 0.27 (2 ticks); that alone was `descuadre_sqx` 0.244 -> 0.0 on its build leg and DAX40 0.088 -> 0.003.
  - **Not repricer bugs** (reported, not fudged): (a) the 10k USDJPY batch's `variant_trades.parquet` (pre c443f1d) tags 16 foreign symbols as `Main` and real USDJPY as `USDJPY_M1`; `NetProfit` = all `Symbol == USDJPY_M1` rows (1004/1004), `Main` alone misses 85 %. (b) XAUUSD oos1 0.59 / 0.45 / 0.28 and USA500 oos1 0.14-0.15: SQX's fills land on the two ticks around the declared unrounded cost (XAU in 0.2286: .23 87 % / .22 13 %; USA500 .6797: .68 95 % / .67 5 %), mean = declared; the bars sit on the tick grid so the split cannot be reproduced, and rounding the fill leaves -0.2 USD/trade bias. (c) `Test_NIKKEI225_M30_volatilidad_wf3` build: every trade -0.279 USD per lot (corr -1.000 with size, 0 nights too) = 4.42 points: the task ran with a round-trip cost of ~5.2 points, the card says 9.60.
  - Not verifiable from disk: PT exits (the only PT export, `raw/USDJPY/WFM_Stability/2026-09-28`, mixes timeframes), short SL, PercentageBased commission. Smallest ground truth: `Test_` on USDJPY M30, SHORT only, one SL + one PT, ~300 trades, SizeBased 5 + a PercentageBased task, swap in points.
`scratch/encargo44/{audit,swap,reprice_check}.py`, `Trade_NIKKEI225_M30_volatilidadL`, oos1, trades from
`reports/…/Results/2026-10-04/spread/trades.parquet` (C equals the raw `OOS` export; A and B have none left).

| USD | A 4.9.301 | B 16.11.437 | C 14.3.479 |
|---|---|---|---|
| SQX net / monkey `real_net` | 38,465.41 / 45,464.33 | 31,861.96 / 38,815.62 | 4,689.84 / 8,173.60 |
| gap | 6,998.92 | 6,953.66 | 3,483.76 |
| spread in the entry fill (4.7491) | 4,123.47 | 4,095.51 | 2,052.67 |
| slippage, entry (1.6622) | 1,443.23 | 1,433.44 | 718.44 |
| slippage, exit (1.6622) | 1,443.23 | 1,433.44 | 718.44 |
| tick rounding of the fills | −3.04 | −3.02 | −1.51 |
| point value by regression (0.06306–0.06309 vs 0.063137) | −7.97 | −5.71 | −4.27 |
| bar, lots, commission, swap, side; unexplained | 0 | 0 | 0 |

- Swap sits inside the monkey's residual, so it adds 0 to the gap (1,227 / 1,231 / 197 USD).
- Independent rebuild vs SQX: oos1 sums within ±0.10 USD, build ±0.53.
- Rejected: rollover 22:00 (28–30 USD/trade); 00:00 with Monday triple (fails build by 18–22 USD); `open < T ≤ close` (16 USD off); notional at the exit price (0.75 USD).
- Build fill offsets split (entry 4.10 / 4.11, exit 1.06 / 1.07); oos1 is 6.41 and 1.66 on all 487. Seven float32 rounding recipes failed.

### 2026-10-12 `descuadre_sqx` per asset under the rule max(1 USD, 1 % x |NetProfit|) (owner), build / oos1 / oos2
Rule in `engines/weekly/panel.py::sqx_gap`. USDJPY 0 / 0 / 0 · USATEC 0 / 0 / 0 · NIKKEI225 wf3 0 / 0 / 0.002 and 0 / 0 / 0 · DAX40 0 / 0.011 / 0.007 · USA500 0 / 0.154 / 0.015 and 0 / 0.157 / 0.011 · XAUUSD 0.001 / 0.461 / 0 and 0.253 / 0.284 / 0. What is left (XAU, USA500, DAX40 oos1) is the split-fill cause above: the bars cannot say which tick SQX filled, so small-NetProfit variants miss by cents x trades. `<` 0.01 holds on USDJPY, USATEC and NIKKEI225 only.
- Ground truth for short SL / PT could not be built: the simple short builder on USDJPY draws no SL/PT (`StopLoss`, `ProfitTarget` `use="false"`). Short SL, PT and PercentageBased stay UNVERIFIED.
