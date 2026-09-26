---
q: feed quality M1 anomalies; bad tick vs flash crash; spike threshold K MAD fat tails; frozen price runs; gaps; Dukascopy early years; feed timezone UTC+2 rollover
tag: 🔬  date: 2026-09-26  see: export/bars, costs/sessions-per-asset
---
# On the Dukascopy M1 feed, extreme moves are mostly real events, and a Gaussian K is meaningless
- Beyond 10 hour-of-week MADs: 22,660 XAUUSD closes (normal expects 0). Pick `K` by marks per year, not by probability.
- Top |z| moves are history (Brexit, JPY flash crash 2019-01-03, 2011 quake, gold 2013/2021-08-09) and revert like bad ticks; only USDJPY 2009-01-01 19:43 (±1.9 % in 3 min, New Year) looks like an error.
- ⚠️ A whole-history scale flags volatile years, not bad ones: XAUUSD K10 = 33 in 2018 vs 2,758 in 2026 (9 months). Use a trailing scale.
- ⚠️ XAUUSD before 2006 is a different feed: 5.8–11.6 k in-week gaps ≥ 5 min/yr vs ~210/yr since 2013 (the daily break).
- Feed clock is UTC+2 (JPY flash crash at 00:35 feed = 22:35 UTC); flat bars peak at feed hour 0 (USDJPY 10 %) = NY rollover.
- 13 feeds: K = 20 keeps calm years < 1 mark/week in 12 (GBPUSD needs 25); m = 3, L = 10 hold for all. ⚠️ Outliers:
  XAGUSD ~720 and CADJPY ~115 K20 spike-and-reverts/yr (others 9–33); Brent ~900 gaps/yr; EURUSD frozen runs cluster in 2021–23.

## Evidence
- 🔬 2026-09-26, `core.barstore.source`, contiguous M1 closes, MAD × 1.4826 per (weekday, hour) over the whole history.
  Calm-year (2013–2019) median marks/yr at K = 15 / 20: XAU 63 / 24, USDJPY 94 / 38, EURUSD 55 / 20.
  K20 spike-and-revert (≥ 80 % back) in 1 / 3 / 5 min: XAU 69 / 239 / 356 of 1,379; no plateau.
- Identical-OHLC runs ≥ 10 min: XAU 16, USDJPY 77, EURUSD 109 (85 of them in 2021–2023).
- Full tables and the 16 proposed thresholds: `docs/AgentPDFs/calidad-del-feed-decisiones-2026-09-26.md`.
