---
q: news filter did not close in the tester some months, open across the release, incumplimientos de la lectura con filtro, tester ticks per bar, missing M1 history on the firm's server, 4 ticks per H1 bar, ohlc_m1 falls back to H1, open_prices model news filter
tag: 🔬  date: 2026-10-02  see: eng/ea-news-filter, eng/mt5-history-depth-first-bar
---
# Where the server has no M1 bars the tester makes 4 ticks per H1 bar — and a minutes-wide window never sees a tick
- `ohlc_m1` (and every-tick) build ticks from M1 bars; in a stretch the server lacks them the tester silently builds from the bar it has: 4 ticks per H1 bar, all on the hour.
- The news filter closes in a 2-3 minute window before a release, so in those stretches it closes nothing and the "filtered" run is the unfiltered one. Same with the `open_prices` model, always.
- `mt5.newsfilter.reading` leaves those stretches out of both runs (owner, 2026-10-02): the patched EA prints `thin history <day> <ticks>` for a day under 600 ticks, `gaps.py` joins the days and drops every trade open inside. 🤔 the EA's line compiles but has not been seen in a tester log yet; a breach left after the exclusion (`incumplimientos` > 0) would say the threshold missed a day.
- Seen: FTMO-Server4, USDJPY, 2023-09-20 → 2023-11-10 (9 breaches in a 2022-06 → 2026-09 run with 145 early closes elsewhere).
- Quick probe for any week: the tester log's `N ticks, M bars generated` — about 235 ticks per H1 bar is M1 data, 4 is not.

## Evidence
2026-10-02, build 6231, `S16976_Hantec.ex5` (Strategy 16.9.76 + Hantec filter) on USDJPY H1, `ohlc_m1`, FTMO account. One-week runs: 2023-08-14→19 `28300 ticks, 120 bars generated` (and a `News filter: closing…` line); 2023-09-18→23 `480 ticks, 120 bars`; 2023-10-23→28 `480 ticks, 120 bars`; 2024-09-23→28 `28245 ticks, 120 bars`. Full run: 6,006,975 ticks for 26,847 bars; no `closing` line in 2023-09, -10, -11. Agent log `Tester/Agent-127.0.0.1-3000/logs/20261002.log`.
