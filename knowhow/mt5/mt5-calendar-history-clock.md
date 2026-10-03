---
q: How do I convert MT5 calendar history timestamps, which carry today's server offset, to the real past time?
kw: MT5 economic calendar history time zone, CalendarValueHistory past release one hour off in winter, NFP 16:30 instead of 15:30, server time DST calendar, convert calendar to UTC, news CSV for Strategy Tester clock, EETUS news time
tag: 🔬  date: 2026-10-02  see: mt5/ea-news-filter, mt5/mt5-verify-clock-zones, mt5/news-calendars-mt5-vs-forexfactory
---
# MT5 stamps its whole calendar history at TODAY's server offset — convert through UTC, never use the stamp as the past server time
- A past release comes back as UTC + the offset the server has on the day you ask, not the one it had that day. Asked in summer (UTC+3), January's NFP reads 16:30; the server's bars that day put it at 15:30.
- UTC = stamp − (server now − UTC now). `mt5.newsfilter.history` stores `utc` (and the raw `stamp`).
- The server clock of the day = UTC converted with the server's zone: FTMO and Hantec are `EETUS` (New York + 7 h), so 08:30 New York is 15:30 every day of the year, also in the weeks only the US has changed hour. `mt5.newsfilter.testerfile.to_server`.
- Live the filter is unaffected: it asks only ±1 day, where today's offset is the right one (except the days around a change).
- An event with no minute is type "Event takes all day" (`CALENDAR_TIMEMODE_DATE`) AND stamped 00:00 UTC (summits, G20, G7: 190 HIGH). The type alone is wrong: `AU:rba-interest-rate-decision` (210 releases, FTMO-restricted) is filed all-day with its real time. 00:00 UTC alone is wrong too: 26 timed HIGH releases fall there. The EA and the tester file drop only the conjunction (owner, 2026-10-02).
- Importance is the event type's rating today; the calendar keeps no history of it.

## Evidence
2026-10-02, terminal build 6231 on FTMO-Server4 (UTC+3), through the terminal's MCP `economic_calendar_list_values`: `US:nonfarm-payrolls` 2025-01-10 → `16:30`, 2025-07-03 → `15:30`; France industrial production 2025-01-10 (07:45 UTC) → `10:45`. After subtracting 3 h: 13:30 and 12:30 UTC, the BLS times. Cross with Forex Factory's GMT history, 2007-2026 (`python3 -m mt5.newsfilter.cross`): 5,931 red-folder moments fall in the very minute of an MT5 HIGH release, 71 an hour apart, no season to them — the UTC conversion holds summer and winter. Against price: on 125 of the 136 NFP days since 2015 the widest M1 bar of gold within ±3 h (`AlgoData/bars/XAUUSD_M1`, an EETUS feed) is within 2 min of the tester file's time; 1 an hour later, 0 an hour earlier. In the tester the EA closed at 15:25:00 before the CPI of 2025-03-12 (a US-only-DST week). 🤔 not seen: an export made in winter (expected: stamps at UTC+2, same UTC after the subtraction). `tests/test_newsfilter_tester.py` `check_clock`.
