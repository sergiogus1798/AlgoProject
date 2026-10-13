---
q: Why does a strategy archived before 2026-10-01 not match the bars now on disk?
kw: clock.reclock; golden drift; point value alone clock alone; archived strategy trades clock vs bars clock; feed renamed 2026-10-01 EETUS; USDJPY_DukasM1_the5ers Asia/Jerusalem; MAE MFE licence refused after feed rename; inputs.source.load clock; sqx.inspect.feeds.timezone current(); universe rebuild differs; portfolio pool m1_test_uno excluded
tag: 🔬  date: 2026-10-04  see: export/feed-clock-timezones, export/mae-mfe-from-m1, sqx-format/equity-reconstruction-usdjpy-gap
---
# A strategy archived before 2026-10-01 no longer matches the bars on disk: trades in the old feed clock, bars in EETUS
Since 2026-10-01 `USDJPY_DukasM1_the5ers` resolves to `USDJPY_M1`, stamped in EETUS, while trades archived before are in
Asia/Jerusalem — one hour apart in the weeks Israel and the US change time apart, so the rebuild misses and the universe refuses
the member (licence < 99 %). 🔬 The clock is the WHOLE cause: `equity.clock.reclock(bars, "EETUS", "Asia/Jerusalem")` gives back 100 %.
Since 2026-10-13 (owner) clock and commission are FROZEN in the manifest (`manifest.frozen`), `inputs/source.py` reads them
(`archive_read.frozen`, raises without them, no live fallback). Older members: `python3 -m portfolio.common.construct.inputs.backfill`
fills what the member's own `asset/card.json` proves (clock only for projects created on/after 2026-10-01) and lists the rest.
Backfill 2026-10-13: 68 filled (the 30 old-feed USDJPY got EETUS by owner order, `OLD_FEED_CLOCK` — wrong, see Evidence); 5 stay unfilled.

## Evidence
- 🔬 2026-10-13, 3 of the 30 old-feed members: rebuild vs SQX daily lows, max_gap 0.3-3 $ with Asia/Jerusalem, 430-2000 $ with EETUS (commission charged).
- 🔬 2026-10-04, golden `4d679e…/2026-09-28T0919`, daily low vs SQX within 1 $ (`AlgoData/scratch/golden-drift-2026-10-04/d1_explain.py`):

  | point value | bars as on disk (EETUS) | re-stamped to Asia/Jerusalem |
  |---|---|---|
  | measured off the trades = archived card, 653.92 | 3,777 of 3,906 days (96.7 %), max 2,871 $; MAE 94.3 % | **3,983 of 3,983 (100 %), max 0.16 $; MAE 100 %** |
  | today's card, 631.34 | 44.1 %; MAE 3.8 % | 45.4 % |

  The 129 missing days: March 61, October 48, November 11, September 8 (Israel changed in September before 2013), April 1.
  No old-feed bars are left on disk (`bars/USDJPY_M1` only). Jerusalem − EETUS: 0 h on 90.6 % of minutes, −1 h on 9.3 %
  (US already on summer time and Israel not, or Israel back and the US not), +1 h on 0.03 %.
- Same golden with today's card commission (5 $/lot) charged as `universe._commission` does: 44.7 % / 40.0 % — it was
  built at 0 (`closecurve.measured` reads 0.00). `source.load`'s `calibrate.point_value` (a plain fit) is biased once
  trades carry commission and swap: 631.06 against 631.34 on a current strategy, MFE licence 98.9 % instead of 99.7 %.
- Tests: the old golden pinned on its clock (`tests/test_portfolio_mtm.py`, `test_portfolio_universe.py`), the current
  feed's own golden in `tests/test_portfolio_golden_current.py`.
- Archived `4d679e…/2026-09-28T0919`, 2026-10-02: `source.load()["clock"]` = `EETUS`; the universes cached on 2026-09-30 say
  `Asia/Jerusalem` in `manifest.json`.
- `equity.excursions.licence` on today's `USDJPY_M1`: MAE exact 94.3 %, MFE 97.4 % (100 % / 99.9 % on 2026-09-30) →
  `licensed: False`. 119 of 2,094 trades miss by more than 1 $, all opened in March (59), September (8), October (42) or
  November (10).
- `equity.days.server_days` today against the three cached universes: 120 of 4,690 server days differ, up to 2,871 $.
- April-October 2014 (both clocks at UTC+3): the exact M1 day low and high equal the cached universe's on 167 of 167 FTMO
  days and 140 of 140 Hantec days (gap 0.0001 $) — `tests/test_portfolio_stageb.test_golden_archived_strategy`.
