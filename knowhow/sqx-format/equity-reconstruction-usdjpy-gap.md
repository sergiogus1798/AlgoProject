---
q: Why did the equity rebuild from trades and M1 miss SQX's daily curve on USDJPY, and what makes it reconcile?
kw: exit at 02:00 flat day gap, SQX low sampled only while open, days.low_open, paths.py reconstruction does not reconcile USDJPY, equity rebuild vs dailyEquity.bin gap, commission while position open, 5 $ per lot gap, commission charged at entry floating equity, swap not in floating, MAE MFE without commission, USA500 97 % within 1 $, point value 653.92 vs 631.34 card recalibrated, closecurve.measured, la curva reconstruida no reproduce la de SQX, DST weeks March October gap EET EETUS feed clock changed
tag: 🔬  date: 2026-10-04  see: sqx-format/daily-equity-bin, research/gate-t-scales, export/mae-mfe-from-m1
---
# SQX's daily curve carries the whole round-turn commission from the ENTRY; the rebuild booked it at the close
Pass `commission` to `equity/paths.minute_path` (or use `equity/closecurve.panel`, which does): 🔬 SQX takes the full round-turn commission off the
floating equity from the entry minute — gap = 5.000 $ × lots on USDJPY, no dependence on nights held (swap is NOT in floating; `MAE ($)`/`MFE ($)`
carry neither). Read point value and commission off the trades (`closecurve.measured`), not the card: a recalibrated card is not the build's. A
population built on a feed whose clock later changed still fails in the DST weeks — refuse it, or rebuild it on bars re-stamped to its own clock
(`clock.reclock`, 🔬 100 %: `export/archived-trades-vs-reclocked-bars`). A broker debits the commission at the deal: SQX is the right side. Step 20's
guard (`blindJoint/inputs.tolerance`, owner R4=A) allows each day max(1 $, half the export's last price decimal x point value x the most lots open at
once that day): SQX fills gold at half a cent but exports 2 decimals, so each open lot is up to 0.5 $ off.

## Evidence
- 🔬 2026-10-16, XAUUSD (price decimals 2, point value 100), days within tolerance: build 99.46 % -> 99.61 %, oos1
  98.70 % (16 of 1232 fail) -> 99.35 % with the lots-scaled tolerance (max allowed 1.87 $).
- 🔬 2026-10-06 (the rebuild took a level SQX never samples — `sqx-format/daily-equity-bin`), `Test_USA500_H1_indicesIBS`, 3 mothers, oos2, refused at 98.56 %: all 10 gap days (2.5-58 $) were
  days whose only trade exited at 02:00 and left the strategy flat; SQX = the worst wick of 01:00-01:59 (±0.15 $),
  the rebuild = the realised level after the exit, lower by swap + slippage. With `days.low_open`: 100 % (max 0.18 $),
  USDJPY M30 still 100 %.
`AlgoData/scratch/close-curve-2026-10-04/`: `g1_gap_cause.py` (cause), `g2_reconcile.py` + `g2_run.log` (after).
- Cause, 400 strategies of `Test_Calib_USDJPY_H1_momentumL`, oos1, 514,381 strategy-days: flat days 100 % within
  1 $; of 182,389 days whose low falls with a position open, 0 %. gap ÷ lots at the low minute: median 5.000,
  p5 4.958, p95 5.039; OLS through the origin c = 5.0000, R² = 1.0000; per-lot gap flat across lot quintiles
  (4.985 … 5.004). Charging 2.5 $/lot: 0 of 400 licensed; 5 $/lot: 400 of 400.
- Trades: same-day trades pay exactly 5.000 $/lot inside `Profit/Loss`; overnight ones 5 − swap (3.38 one night).
- After, whole populations, share of strategies with ≥ 99 % of days within 1 $: USDJPY **0 of 3,732 → 3,729
  (99.9 %)**, median day share 0.722 → 0.9992; `Test_Calib_USA500_H1_pullbackL_rnd` (commission 0) **3,683 of
  3,786 (97.3 %) → the same**, median 0.9970.
- `Test_USDJPY_donchianUpperCrossUp_H1` (built 2026-09-30): its trades give point value 653.92, the card 631.34;
  with the measured value median day share 0.577 → 0.986, 10 of 60 licensed. Of the 1,090 remaining gap days 824
  fall in March and 232 in Oct–Nov — the weeks EU and US clocks differ: built before the 2026-10-01 feed change.
- 🤔 `PercentageBased` commission (`paths.entry_commission`): only reconciled at 0 % (indices); XCUUSD, the one
  asset with a non-zero %, has no harvest. Confirm on its first population. Checked again 2026-10-04: the trades of
  all 70 index harvests fit a commission of 0.000 % (`scratch/golden-drift-2026-10-04/p1_pct_commission.csv`).
- Not fixed here: `portfolio/common/construct/search/stageb_data.py:62` calls `minute_path` without commission.
