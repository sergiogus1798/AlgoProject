---
q: what timezone are SQX bars and trade times in, is Open time UTC, broker time, EET, Asia/Jerusalem, EETUS, convert trade times to UTC, session of day, feed timezone
tag: 🔬  date: 2026-10-01  see: costs/sessions-per-asset, export/trade-export-columns, sqx-drive/renaming-feeds
---
# SQX stamps every feed in its broker's clock, never UTC — read the zone, then convert
- Bars and trade times (`Open time`, `Close time`) are naive, in the feed's zone: SQX's data registry,
  table `DATA`, column `TIMEZONE` per feed — `sqx.inspect.feeds.timezone(feed)` reads it read-only.
- Metals and indices `EET`; the5ers FX `Asia/Jerusalem`; stocks, USDSEK/SGD, Brent `EETUS` — the name (`XAUUSD_M1`, 2026-10-01) does not say which.
- ⚠️ `EETUS` has no IANA name: it is New York + 7 h — shift −7 h, localize as `America/New_York`.
- ⚠️ The hour a change of time repeats or skips: localize with `ambiguous="NaT"`, count, never guess.
- Without this, anything hour-of-day (sessions, rollover, news) is off by 2–3 h.
- FTMO's and Hantec's MT5 servers are `EETUS` too; SQX ↔ MT5 needs zone conversion, not a shift (`eng/mt5-verify-clock-zones`).

## Evidence
- 2026-09-26, read-only copy of `SQX/user/data/data.db`: rows for `XAUUSD_DukasM1_Infinox` (EET),
  `EURUSD_DukasM1_the5ers` and `USDJPY_DukasM1_the5ers` (Asia/Jerusalem), `BRENTCMDUSD_ftmo` (EETUS).
- `tests/test_conditionalmap.py`: 2021-03-20 23:30 `EETUS` is 16:30 in New York (open); read as
  `EET` it would be 17:30 (closed) — the test fails if EETUS is treated as EET.
- Used by `studies/readings/conditionalMap/sessions.py`.
