---
q: Why does a strategy archived before 2026-10-01 not match the bars now on disk?
kw: archived strategy trades clock vs bars clock; feed renamed 2026-10-01 EETUS; USDJPY_DukasM1_the5ers Asia/Jerusalem; MAE MFE licence refused after feed rename; inputs.source.load clock; sqx.inspect.feeds.timezone current(); universe rebuild differs; portfolio pool m1_test_uno excluded
tag: 🔬  date: 2026-10-02  see: export/feed-clock-timezones, export/mae-mfe-from-m1
---
# A strategy archived before 2026-10-01 no longer matches the bars on disk: trades in the old feed clock, bars in EETUS
`inputs.source.load` reads a member's clock **live** from the master's registry through `core.symbols.current(feed)`; since the
feeds were unified on 2026-10-01 `USDJPY_DukasM1_the5ers` resolves to `USDJPY_M1`, stamped in EETUS, while the archived
trades are still in Asia/Jerusalem. The two agree most of the year and are one hour apart in the weeks Israel and the US
change time apart, so the M1 rebuild is wrong for the trades opened then and the universe **refuses** the member (licence
under 99 %). A pool of strategies archived before that date needs its trades re-harvested on the new feed, or the clock
frozen at archive time and the trades shifted to the bars' clock — not decided; nothing was changed.

## Evidence
- Archived `4d679e…/2026-09-28T0919`, 2026-10-02: `source.load()["clock"]` = `EETUS`; the universes cached on 2026-09-30 say
  `Asia/Jerusalem` in `manifest.json`.
- `equity.excursions.licence` on today's `USDJPY_M1`: MAE exact 94.3 %, MFE 97.4 % (100 % / 99.9 % on 2026-09-30) →
  `licensed: False`. 119 of 2,094 trades miss by more than 1 $, all opened in March (59), September (8), October (42) or
  November (10).
- `equity.days.server_days` today against the three cached universes: 120 of 4,690 server days differ, up to 2,871 $.
- April-October 2014 (both clocks at UTC+3): the exact M1 day low and high equal the cached universe's on 167 of 167 FTMO
  days and 140 of 140 Hantec days (gap 0.0001 $) — `tests/test_portfolio_stageb.test_golden_archived_strategy`.
