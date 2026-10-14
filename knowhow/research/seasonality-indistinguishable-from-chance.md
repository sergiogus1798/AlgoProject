---
q: Does a strategy's oos1 result concentrate in a month, weekday or hour beyond chance, and how is that tested?
kw: seasonality breakdown; calendar concentration; hour of day P&L; day of week; month of year; BuildAlpha seasonality; stratified permutation; block relabel null; time filter rule 15; one hot July
tag: 🔬  date: 2026-10-14  see: research/fdr-raises-on-nan-p, export/feed-clock-timezones
---
# In two populations the oos1 calendar is indistinguishable from chance; a per-trade shuffle would have named one hot July a season
- `studies.readings.seasonality`: P&L per lot, hours and weekdays shuffled inside each UTC year-month, months relabelled as whole year-month blocks, BH over every tested cell of a strategy (q 0.05, ≥ 30 trades a cell). Calibrated on noise: any-discovery 4.7 %.
- XAUUSD donchian2 H1: 1 of 300 strategies with a discovered cell (chance ceiling 15); USDCAD reversion M30: 0 of 64 (3.2). Stratum by month, quarter, year or none: 0-4 found — the stratum does not decide.
- A trade-level shuffle names a single July with a big result as a season (p < 0.001); the block relabel does not (p > 0.05). Months need the block null.
- Rule 15: a calendar reading is reported, never fed back to a build as a time filter (owner D-1).

## Evidence
`python3 -m studies.readings.seasonality.report --project Test_XAUUSD_donchianUpperCrossUp2_H1 --databank Results --feed XAUUSD_M1`
(and `Test_USDCAD_M30_reversionL_cal2`, `USDCAD_M1`), reports of 2026-10-14; noise calibration: 150 synthetic
strategies of `tests/test_seasonality.py::trades`, 2,000 draws; `test_one_hot_july_is_not_a_season`.
