---
q: Does MCR 7 OHLC keep the original's trades, and do the harvest's IS trades match sqxretest.original()?
kw: MCR 7 OHLC trade count changes, RandomizeHistoryDataOHLC, ret_med_aprox, T2 approximate excess, ingest build trades, load_trades only OOS
tag: 🔬  date: 2026-10-07  see: sqx-format/mc-retest-storage, sqx-format/mcr-start-bar-reruns-identical
---
# MCR 7 OHLC changes the trade count in most re-runs, so T2's excess is approximate
In most MCR 7 re-runs the number of trades differs from the original's (median deviation 0-3 %), so a
re-run's drift cannot be computed: T2 assumes the original's drift and calls the result `ret_med_aprox`
(0.73-1.10 on 26 strategies). `load_trades` holds only OOS trades; the harvest's IS trades match
`core.sqxretest.original()` one to one, and the ingest now stores them: projects ingested before
2026-10-07 need a re-ingest before T2/T3 can be read.

## Evidence
- Measured 2026-10-07 on 26 real strategies (harvest vs `core.sqxretest.original()`, trade by trade).
- Rule: `pipeline/autopilot/criteria.yaml` key "14", T2 (`>= 0.6` pass, `>= 0.25` limbo; provisional).
