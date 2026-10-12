# wfc — the choices that had real alternatives

Each section is a decision that moves the answer. All are open (owner, 2026-10-07) unless marked.
The CSCV's old decisions (weekly periods, twelve blocks, …) live in `../cscv/POSSIBLE_IMPROVEMENTS.md`.

## 1. The level carries a null — decided (owner, 2026-10-07, confirmed 2026-10-08)

The table as first written («the top wins» = a median above zero) passes a no-edge family
0.5 × (1 − α) of the time by construction. The criterion asks the median to beat its sign-flip
null too (`p_nivel` ≤ `wfc.level_alpha`); above zero without beating it is LIMBO. The agent of the
night of 2026-10-07 dropped the null and the owner put it back the next day. The table without
the null is the calibration's comparison column (`_sin`).
**Open, the owner's:** the register on disk was measured on 2026-10-07 with a daily null and the
order on net; the code now flips weeks and reads the order on gross (`calibrate/README.md`).

## 1b. Which excess the cloud and its quadrants are drawn on

The proposal reads the order on gross and the level on net, and keeps one figure with the quadrants
and the Spearman line. The code draws the points and counts the quadrants on **net** («gana dentro
y fuera» is money) and labels the line with the **gross** rho. Not asked of the owner yet.

## 1c. What «flat edge» means when variants trade at different frequencies

Same gross level per year, or same gross edge per trade: on gross the order is «positivo» 3 % of
the time under the first and 75 % under the second (`tests/test_wfc_families.py`). Whether «trades
more, earns more» is an order the step should count is the owner's; today it counts.

## 1d. The tolerance of the SQX check

`wfc.sqx_gap_tolerance` (1.0) and `wfc.sqx_gap_relative` (0.01) are combined as max(floor, share x |NetProfit|) (owner, 2026-10-12); the values are still the agent's.

## 2. Which trade count the partial rho controls for

`measure/order.partial` exists and is annotated nowhere on the owner's word: inside trades, outside
trades, or total. Without it a rho can be only «the variants that trade more do better in both».

## 3. The denominator guard of `R_sel`

`level.r_sel_min_gap` (0.05 of the in-sample interquartile range) is provisional: the Council asked for
the guard and gave no number.

## 4. Top of 20 % or of 10 %, and the metric

`wfc.top_share` 0.20 is the proposal's value, not a measurement. The excess per year against the
Sharpe of the excess is open the same way; `calibrate` can run both.

## 5. The calibration's reference cell

2.75 years out, Sharpe 0.5, the worse of «with order» and «without order», and `own_noise` 0.4 are
set in `calibrate/config.yaml#reference` by the agent that built it, not by the owner.

## 6. Nothing here has met a real batch

`inputs/batch.py` reads `variant_trades.parquet`; no real batch with that file exists (OPEN.md, part V
of encargo 48). The rehearsal build → oos1 of `calibrate/` ran only on a synthetic batch.
