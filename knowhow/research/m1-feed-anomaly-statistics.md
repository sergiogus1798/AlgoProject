---
q: feed quality M1 anomalies; bad tick vs flash crash; spike threshold K MAD fat tails; K per feed 20 25 30; frozen price runs; gaps; rollover gaps 00:00; Dukascopy early years; stable year; feed tick vs SQX tick; silver CADJPY spike-and-revert
tag: 🔬  date: 2026-09-26  see: export/bars, export/feed-clock-timezones, costs/sessions-per-asset
---
# On the Dukascopy M1 feed, extreme moves are mostly real events; measure K per feed on a trailing scale
- Top |z| moves are history (flash crashes, Brexit, SNB, BoJ/MoF, FOMC): of 520 reviewed, 383 identified, 42 suspect (38 = CADJPY 2006–08). Mark, never clean.
- ⚠️ A trailing 52-week scale gives MORE calm-year marks than a whole-history one (EURUSD K20: 60 vs 20/yr): K* = 20 in 4 feeds, 25 in 7, 30 in USDJPY/GBPUSD.
- ⚠️ The feed's tick is its smallest move, NOT `assets/` `tick_size`: forex feeds quote a tenth of SQX's pip-tick. A 3-SQX-tick floor hides every forex spike.
- Silver's ~720/yr spike-and-reverts were scale collapse in dead hours (unfloored σ 1.4 ticks): floor → 2/yr. CADJPY's 115/yr was a 2006–08 episode (423 in 2007), not quantisation.
- ⚠️ Since 2020 most in-session "gaps" of the pairs are 5-min silences at 00:00 (AUDJPY 95 of 103 in 2025); EURUSD's 2021–23 frozen episode is all at hour 00. Count the rollover apart.
- Daily pause 00:00–01:00 gold/silver, 00:00–03:00 Brent, all year; it shifts an hour in March (US/EU DST mismatch).
- Gold ≤ 2005 and AUDUSD 2007 (1,293 gaps) are other feeds; Brent 2013 has a 55-day hole.

## Evidence
- 🔬 2026-09-26, `studies/data/feedQuality` (`calibrate`, `scan`, `inject`), 13 feeds of `AlgoData/bars/`.
  Whole-history scale reproduces the report exactly: K20 calm medians XAU 24 / USDJPY 38 / EURUSD 20.
  52 w + floor: XAU N20 76 → K 25; USDJPY 97 → 30; EURUSD 60 → 25; GBPUSD 129 → 30.
- Injection (owner's 2.16 grid, ~12,300 events/feed): recall 100 % at ≥ 1.25 K in all 13 feeds;
  frozen 9|10 and gap 4|5 cut exactly; revert 80 %|70 % separated 100 %|0 %. Real count changes
  ≤ 0.4 %; 1–37 new marks per feed, most a real spike already within 5 % of K (MAD shifts ~1 %). Owner accepted.
- Planted runs merge with adjacent identical real bars; unpaired level-shifts walk the tick floor.
- Tick: EURUSD smallest |ΔC| 0.00001 vs `tick_size` 0.0001; USDJPY 0.001 vs 0.01; metals/Brent equal.
