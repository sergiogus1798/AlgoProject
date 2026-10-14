# mt5/newsfilter — a prop firm's news rule, written into SQX's MQL5 export

SQX exports an EA with no news filter. A funded account at Hantec (or FTMO) may not open or close a
trade within a few minutes of a high-impact release, so every EA that goes to such an account is run
through this first. Per strategy it writes **two** EAs (owner, 2026-09-29): `<name>_<Firm>.mq5` with
the filter, for the funded account, and `<name>_NoNews.mq5`, SQX's own untouched, for the challenge
or an account with the news add-on. Skill: `/ea-news`. Manual: chapter `75-filtro-noticias`.

What the filter does, per firm (`firms.py`): from `close_before` minutes before a release until
`rule_minutes` before it, close this EA's positions and cancel its pending orders (an SL or TP hit
inside the window is a close); from `block_before` before until `block_after` after, open nothing.
Hantec: releases from MT5's calendar (HIGH) and Forex Factory's red folder, counting for a symbol
when their currency is in its name or is the country of its index or commodity (`COUNTRY_OF`).
FTMO: only FTMO's own restricted list (`FTMO_EVENTS`, 37 MT5 event codes — MT5 rates half of them
medium, `knowhow/mt5/ftmo-news-vs-mt5-importance.md`), crude inventories on oil alone.
**Neither calendar exists in the Strategy Tester.** There the patched EA reads the firm's history
from `Common\Files\AlgoProjectNews_<Firm>.csv` (input `NewsTesterFile`; empty = no filter in the
tester), already in the server's clock; live, it never opens that file. So the cost of the rule is
now a measurement: the same strategy with the filter and without (`reading.py`).
`knowhow/mt5/ea-news-filter.md`, `knowhow/mt5/mt5-calendar-history-clock.md`.

```
terminal (open) ─ history.py ─▶ AlgoData/mt5/calendar/mt5_{events,values}.parquet  (UTC)
newfac release  ─ forexfactory.py ─▶ …/ff_newfac.csv (GMT)          cross.py ─▶ cross.json
                    testerfile.py <firm> ─▶ Common\Files\AlgoProjectNews_<Firm>.csv (server clock)
terminal (closed) ─ reading.py ─▶ two tester runs ─▶ AlgoData/mt5/newsfilter-readings/<run>/
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `cross.py` | Cross the two calendar histories: Forex Factory's red folder against MT5's HIGH releases, minute by minute. | `python3 -m mt5.newsfilter.cross [--from YEAR]` | the two histories → `cross.json`, `cross_unmatched.parquet` |
| `firms.py` | Each prop firm's news rule as the EA filter needs it: window, calendars, and what moves each symbol. | imported | — |
| `forexfactory.py` | Forex Factory's calendar history from 2007 (janickfarrell/newfac's daily release, MIT), as UTC rows. | `python3 -m mt5.newsfilter.forexfactory` | URL → `ff_newfac.csv` |
| `gaps.py` | The stretches of a tester run with no M1 history under them, read from the patched EA's own log lines. | imported | agent log + trades → stretches, trades kept |
| `history.py` | Export the MT5 terminal's economic calendar to AlgoData in UTC: every event type and every dated release. | `python3 -m mt5.newsfilter.history [--from YEAR]` (terminal open) | terminal → `mt5_events.parquet`, `mt5_values.parquet` |
| `patch.py` | Insert a prop firm's news filter into the MQL5 source SQX exports, at the four places it needs. | imported | .mq5 text → .mq5 text |
| `reading.py` | What a firm's news rule costs one strategy: its EA in the Strategy Tester with the filter and without, trade by trade. | `python3 -m mt5.newsfilter.reading <firm> <name> --symbol S --timeframe TF --from D --to D --deposit N --leverage L [--model M]` (closes the terminal itself) | two .ex5 → `MT5_DATA/newsfilter-readings/<run>/` |
| `run.py` | Turn SQX-exported EAs into two per strategy — one with a firm's news filter, one without — and compile them. | `python3 -m mt5.newsfilter.run hantec <mq5 or folder>... [--compile]` | SQX .mq5 → two .mq5 (+ .ex5) |
| `terminal.py` | Call a read-only tool of the running MT5 terminal's own MCP server over HTTP, from Python. | imported | tool + args → JSON |
| `testerfile.py` | Write a firm's restricted releases, in its server's clock, as the CSV the patched EA reads inside the Strategy Tester. | `python3 -m mt5.newsfilter.testerfile <firm>` | histories → `Common\Files\AlgoProjectNews_<Firm>.csv` + copy in `MT5_DATA/calendar/tester/` |
| `windows.py` | The news rule on a trade list, in pure Python: which releases move a symbol, and what the filter does to each trade. | imported | trades + releases → fates, breaches |

`mql/` holds the MQL5 the filter is made of, as `string.Template` text (`$label`, `$rule_minutes`…).
Tests: `tests/test_newsfilter.py`, against the hand-made FTMO patch kept in
`MT5_DATA/newsfilter-reference/`; `tests/test_newsfilter_tester.py`, the tester mode on synthetic
releases (the server clock across the US-only weeks, each firm's list, one release whose reading is
known by construction).

- **The tester model must give ticks inside the minute** (`real_ticks`, `every_tick`, `ohlc_m1`): with
  `open_prices` no tick falls in the close window and the filter only blocks entries.
- **Events with no minute are dropped, live and in the tester file** (owner, 2026-10-02): type all-day
  (`CALENDAR_TIMEMODE_DATE`) AND stamped 00:00 UTC. Both tests are needed — MetaQuotes files the RBA
  rate decision (FTMO-restricted) as all-day with its real time, and timed releases do fall on
  00:00 UTC. `knowhow/mt5/mt5-calendar-history-clock.md`.
- **The 14 EAs of `MT5_DATA/eas/` were regenerated on 2026-10-02** (tester mode, no all-day events) and
  compiled there, next to their sources — not in the terminal's `Experts/`; the previous ones are in
  `MT5_DATA/eas-backup-2026-10-02/`. `run.py --compile` still copies into `Experts/AlgoProject/<Firm>/`,
  which is what `reading.py` runs.
- **Third parties**: nothing is ported. `sushiix-trader/mql5-news-filter` (Apache-2.0) was read as
  the design reference (CSV replay in the tester, live calendar outside it); its CSV assumes the
  calendar's raw stamps are a fixed GMT+3, true only for an export made in summer — ours stores UTC.
