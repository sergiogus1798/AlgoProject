---
q: FTMO restricted news list vs MT5 calendar HIGH importance, which FTMO events MT5 marks medium, FOMC minutes AUD CPI employment missed, news filter misses events, CalendarEventByCountry importance, FTMO restricted instruments US30 US2000 DXY USOIL
tag: 🔬  date: 2026-09-29  see: eng/ea-news-filter
---
# MT5's HIGH importance misses part of FTMO's restricted list — a HIGH-only filter is not FTMO-safe
- FTMO restricts a closed list (ftmo.com/en/faq/can-i-trade-news/, events tagged "Restricted event" in ftmo.com/en/calendar/), not "high impact".
- MetaQuotes rates as **medium (2)**: FOMC Minutes; AUD CPI, Employment Change, Unemployment Rate, GDP q/q; CAD CPI m/m, Employment Change, Unemployment Rate; NZD CPI q/q, GDP q/q. A filter on `CALENDAR_IMPORTANCE_HIGH` never blocks them.
- Covered at HIGH (itself or a HIGH release at the same minute): Fed/ECB/BoE/BoC/RBA/RBNZ/SNB rate decisions, NFP, US unemployment, US CPI y/y, US GDP, UK CPI y/y, NZ Employment Change q/q, EIA Crude Oil Stocks Change.
- `mt5.newsfilter`'s FTMO profile therefore matches FTMO's list by MT5 `event_code` (`firms.FTMO_EVENTS`; the name is in the terminal's language). AUD's monthly CPI has no `cpi-mm` code: `cpi-index-number`, `cpi-qq`, `cpi-yy` are all listed.
- FTMO's instrument table also restricts US30, US2000, DXY on USD news and USOIL/UKOIL on Crude Oil Inventories — the hand FTMO patch mapped only US100/US500; the profile now maps all of them.

## Evidence
MQL5 script `CalendarEventByCountry` over US, EU, GB, CA, AU, NZ, CH, JP, run 2026-09-29 on the local terminal (build 5830): 855 event types, saved to `AlgoData/mt5/newsfilter-reference/mt5-calendar-events-2026-09-29.csv` (country|id|importance|code|name). FTMO's table read from its FAQ page the same day.
