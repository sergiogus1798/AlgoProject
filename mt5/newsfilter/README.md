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
medium, `knowhow/eng/ftmo-news-vs-mt5-importance.md`), crude inventories on oil alone.
**Neither calendar exists in the Strategy Tester.** There the patched EA reads the firm's history
from `Common\Files\AlgoProjectNews_<Firm>.csv` (input `NewsTesterFile`; empty = no filter in the
tester), already in the server's clock; live, it never opens that file. So the cost of the rule is
now a measurement: the same strategy with the filter and without (`reading.py`).
`knowhow/eng/ea-news-filter.md`, `knowhow/eng/mt5-calendar-history-clock.md`.

```
terminal (open) ─ history.py ─▶ AlgoData/mt5/calendar/mt5_{events,values}.parquet  (UTC)
newfac release  ─ forexfactory.py ─▶ …/ff_newfac.csv (GMT)          cross.py ─▶ cross.json
                    testerfile.py <firm> ─▶ Common\Files\AlgoProjectNews_<Firm>.csv (server clock)
terminal (closed) ─ reading.py ─▶ two tester runs ─▶ AlgoData/mt5/newsfilter-readings/<run>/
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `firms.py` | Each firm's window, calendars and symbol → currency map | imported | — |
| `patch.py` | Insert the filter at the four places of an SQX export: inputs, helpers, the call in `OnTick`, a guard in every entry rule; refuses a source it cannot place | imported | .mq5 text → .mq5 text |
| `run.py` | Both EAs per strategy into `MT5_DATA/eas/<Firm>/`; `--compile` copies them to `MQL5/Experts/AlgoProject/<Firm>/` and compiles (terminal closed) | `python3 -m mt5.newsfilter.run hantec <mq5 or folder>... [--compile]` | SQX .mq5 → two .mq5 (+ .ex5) |
| `terminal.py` | A read-only tool of the running terminal's own MCP server (`metatrader5`), called over HTTP from Python: address and token from `$MT5_MCP_URL`/`$MT5_MCP_TOKEN`, else Claude Code's `~/.claude.json` entry for this project | imported | tool + args → JSON |
| `history.py` | The terminal's economic calendar to `MT5_DATA/calendar/`: the event types (code, country, currency, today's importance) and every dated release, **in UTC** — the terminal stamps the whole history at today's server offset, which is subtracted (`stamp` keeps what it showed) | `python3 -m mt5.newsfilter.history [--from YEAR]` (terminal open) | terminal → `mt5_events.parquet`, `mt5_values.parquet` |
| `forexfactory.py` | Forex Factory's history from 2007: janickfarrell/newfac's nightly release (MIT, GMT), downloaded as is and read as UTC rows; untimed rows (All Day, Tentative…) left out and counted; a second scrape's red folder (`ff_ehsanrs2_high.csv`, data only) to check the first one's clock | `python3 -m mt5.newsfilter.forexfactory` | URL → `ff_newfac.csv` |
| `cross.py` | The two histories crossed per (currency, minute), both ways: same minute and top-rated in both, same minute but rated lower by the other, within 15 min, exactly an hour apart, alone | `python3 -m mt5.newsfilter.cross [--from YEAR]` | the two histories → `cross.json`, `cross_unmatched.parquet` |
| `testerfile.py` | A firm's restricted releases over the whole history, as the live filter would have loaded them (FTMO: its codes; Hantec: MT5 HIGH + red folder), converted from UTC to the firm's server clock (`server_zone`, the hour change of THAT day) and written where a tester agent can read | `python3 -m mt5.newsfilter.testerfile <firm>` | histories → `Common\Files\AlgoProjectNews_<Firm>.csv` + copy in `MT5_DATA/calendar/tester/` |
| `gaps.py` | The stretches of a tester run with no M1 history under them, from the patched EA's own `thin history <day> <ticks>` lines in the agent log (last run of that EA); thin days joined across a weekend; the trades that touch none | imported | agent log + trades → stretches, trades kept |
| `windows.py` | The rule in pure Python: which releases move a symbol (the EA's `newsMovesSymbol`), the three windows per release, what the filter does to each trade of an unfiltered run (`expected`: blocked, cut, kept) and the trades of a filtered run that break it (`violations`) | imported | trades + releases → fates, breaches |
| `reading.py` | The reading that decides: both EAs of one strategy in the tester on the firm's account, paired by entry — trades not opened, closed early, changed or new by knock-on — with the change in net result and in worst day, and the filtered run's breaches. Model by default: `real_ticks` when the firm's server answers ticks in the window's first week, else `ohlc_m1`, said in the first line. Trades open inside a stretch without M1 history are left out of both runs and the stretches printed (owner, 2026-10-02) | `python3 -m mt5.newsfilter.reading <firm> <name> --symbol S --timeframe TF --from D --to D --deposit N --leverage L [--model M]` (closes the terminal itself) | two .ex5 → `MT5_DATA/newsfilter-readings/<run>/` |

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
  00:00 UTC. `knowhow/eng/mt5-calendar-history-clock.md`.
- **The 14 EAs of `MT5_DATA/eas/` were regenerated on 2026-10-02** (tester mode, no all-day events) and
  compiled there, next to their sources — not in the terminal's `Experts/`; the previous ones are in
  `MT5_DATA/eas-backup-2026-10-02/`. `run.py --compile` still copies into `Experts/AlgoProject/<Firm>/`,
  which is what `reading.py` runs.
- **Third parties**: nothing is ported. `sushiix-trader/mql5-news-filter` (Apache-2.0) was read as
  the design reference (CSV replay in the tester, live calendar outside it); its CSV assumes the
  calendar's raw stamps are a fixed GMT+3, true only for an export made in summer — ours stores UTC.
