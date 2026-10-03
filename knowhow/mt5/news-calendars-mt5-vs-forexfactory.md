---
q: How much of Forex Factory's red folder does MT5's HIGH importance cover, and is either calendar enough for Hantec?
kw: Forex Factory red folder vs MT5 high importance, how many high impact news match, calendar history since 2007, newfac forexfactory_calendar.csv GMT, Hantec news calendar, discrepancies between calendars, speeches missing in MT5 calendar
tag: 🔬  date: 2026-10-02  see: mt5/mt5-calendar-history-clock, mt5/ftmo-news-vs-mt5-importance, mt5/ea-news-filter
---
# MT5's HIGH covers 42 % of Forex Factory's red folder — for Hantec neither calendar stands in for the other
- Both histories start in January 2007 (the terminal answers nothing earlier) and live in `AlgoData/mt5/calendar/`: `mt5_values.parquet` (216,713 releases, 1,508 event types, 88 rated HIGH) and `ff_newfac.csv` (92,733 rows, 19,350 red).
- Per (currency, minute), 2007-01 → 2026-10, 9 currencies: of 14,234 red-folder moments, 41.7 % are HIGH in MT5 that minute, 40.0 % are in MT5 that minute but rated lower (unemployment rate, employment change, retail sales, CPI m/m outside the US), 1.7 % within 15 min, 0.5 % an hour apart, **16.2 % not in MT5 at all** (speeches: Bernanke, BoJ press conference, RBA governor, Trump).
- The other way: of 11,362 MT5 HIGH moments, 52.2 % are red, 36.1 % Forex Factory rates lower (EIA crude stocks, euro-zone CPI y/y, flash PMIs, jobless claims), 9.4 % absent there (bond auctions, Lagarde).
- So Hantec's profile needs both sources (it has them); a rule written as "red folder" cannot be tested with MT5 alone.
- `janickfarrell/newfac` (MIT) publishes the CSV nightly as a release asset; its times are GMT (Forex Factory's own cookie). 378 red rows have no clock time (All Day, Day 2, Tentative) and cannot enter a minute filter.
- The hour-apart cases are single releases one side has wrong (MT5 puts the delayed NFP of 2025-11-20 at 12:30 UTC; it was 13:30), not a clock drift.

## Evidence
2026-10-02: `python3 -m mt5.newsfilter.history`, `… .forexfactory`, `… .cross` → `AlgoData/mt5/calendar/cross.json` (by year) and `cross_unmatched.parquet`. newfac's clock checked against a second scrape stamped in UTC (ehsanrs2's published `high_impact_events_calendar.csv`, 2020-2026, data only — GPL code not run): 3,096 of 3,106 (currency, minute) red moments identical.
