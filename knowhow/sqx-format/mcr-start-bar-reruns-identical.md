---
q: Does MCR 1 Bar (random start bar) change a strategy's trades, so can T3 retention discriminate?
kw: MCR 1 Bar identical re-runs, RandomizeStartingBar, T3 ret_med 1.000, retention median 1.0, ret_p5, start bar control
tag: 🔬  date: 2026-10-07  see: sqx-format/mc-retest-storage, sqx-format/mcr-ohlc-changes-trade-count
---
# MCR 1 Bar re-runs repeat the original inside the common window, so T3's median retention is 1.0
On 26 real strategies, T3 `ret_med` is exactly 1.000 on all 24 with positive excess: 67-100 % of the
re-runs are identical to the original inside the window they share. T3 as defined (median of retention)
therefore does not discriminate; `ret_p5` (0.91-1.00) does vary. The judge's T3 rule never discards.

## Evidence
- Measured 2026-10-07 on 26 harvested strategies, `studies/breakage/mcRetest` ingest + `model/retention.py`.
- Why it is a control: moving the start bar only shifts where the backtest begins; the trades after the
  warm-up coincide, and `config.yaml › fragility.min_tail/min_matched` date a re-run by its tail.
- Judge: `pipeline/autopilot/criteria.yaml` key "14", T3 (`ret_med >= 0.8`, else LIMBO).
