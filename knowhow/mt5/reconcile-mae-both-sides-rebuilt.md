---
q: How should live MAE be compared with the backtest's so the two are comparable?
kw: weeklyReconciler MAE gap live vs backtest; compare live MAE with SQX MAE ($); MFE 3 % lower on USDJPY; SQX fixed conversion rate in MAE; rebuild both sides from M1; mt5.reconcile floating
tag: 🔬  date: 2026-10-02  see: export/mae-mfe-from-m1, costs/sqx-fixed-point-value-jpy, mt5/mt5-verify-clock-zones
---
# Compare live MAE with the backtest's by rebuilding BOTH from the same M1 — never against SQX's `MAE ($)`
SQX's exported `MAE ($)`/`MFE ($)` are priced at its fixed conversion rate; a rebuild at the
asset's `point_value` is priced at another. Put side by side, the ratio of the two point values
reads as a gap in every trade. `mt5.reconcile.judge` therefore rebuilds the SQX trades and the
live trades with the same function (`portfolio…equity.excursions.rebuild`), the same bars and
the same point value; what is left is the fill difference × lot × point value, which is the
real gap. SQX's own column stays what PLAN §14.2 says it is: the licence check of the rebuild.

## Evidence
- 🔬 2026-10-02, `Strategy 10.1.79` USDJPY H1, week 2026-W38, MT5 tester on FTMO standing in
  for live (`AlgoData/mt5/tests/V101227_…_ftmo_…`) vs its SQX retest
  (`AlgoData/mt5/verify/20260930-101227_…/sqx/ftmo/trades.parquet`), 4 trades, 0.1 lots:

  | | trade 1 | 2 | 3 | 4 |
  |---|---|---|---|---|
  | SQX `MFE ($)` exported | 63.17 | 31.91 | 31.98 | 123.79 |
  | SQX MFE rebuilt, point value 631.337 | 60.99 | 30.81 | 30.87 | 119.51 |
  | «live» MFE rebuilt | 60.80 | 30.87 | 30.94 | 119.83 |

  rebuilt ÷ exported = 0.9655 on all four = 631.337 ÷ 653.92 (the rate SQX books USDJPY at).
  Against the export the MFE gap read −1.0 … −4.0; rebuilt both, −0.19 … +0.32 — exactly the
  entry-price gap (+0.3, −0.1, −0.1, −0.5 points) × 0.1 lot × point value.
- 🤔 Not tested on a real account: the bars are the development feed's, not the broker's M1.
