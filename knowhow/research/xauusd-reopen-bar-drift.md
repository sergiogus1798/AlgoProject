---
q: gold Asian session drift, overnight effect XAUUSD, long at 01:00 reopen, daily pause 00:00-01:00 EET, first minutes after reopen jump, hour-of-day entry fake edge, BarHourIs 1, time-of-day template gold
tag: 🔬  date: 2026-10-01  see: costs/darwinex-real-spread, export/feed-clock-timezones, research/m1-feed-anomaly-statistics
---
# On XAUUSD_M1 the gold "Asian drift" lives in the first 5 minutes after the 01:00 EET reopen — treat any edge entered at that bar as suspect
- Long 01:00→10:00 EET (build 2008–2017) books +0.83 $/trade gross, t = 2.95 net of costs; the same window from 02:00 is +0.33 $ gross, **negative net** (t = −1.0).
- +0.40 $ of it comes in 01:00–01:05 (median +0.31), every single year 2008–2017; pre-pause close → 01:00 open is only +0.07.
- Darwinex ticks (2017-Q4 only, 64 days) show the reopen move at +0.045 $ with a 0.148 $ first-tick spread: the Dukascopy bid at the reopen sits low and the "drift" is mostly spread normalisation, not tradeable at the ask. 🤔 Unverifiable before Oct 2017 (no ticks).
- A template or a random condition that enters at the reopen bar (`BarHourIs 1`, a session start at 01:00, H1/H4 bars opening 01:00/00:00) can inherit this as fake edge: price it at the reopen's own spread (hour 00–01 ≈ 1.5–2.2× the day's) before trusting it.

## Evidence
ideaExpert, 2026-10-01, build segment only (`core.assetdata.window(load('XAUUSD'), 'build')`): `core.barstore.read('XAUUSD_M1', 'H1')`, entry at the open of the 01:00 (or 02:00) bar, exit at the close of the 09:00 bar, per calendar day; then `core.barstore.source('XAUUSD_M1')` minute by minute inside the 01:00 hour.
Per year, 01:00 open → 01:05 close mean $: 2008 0.29 · 2009 0.46 · 2010 0.54 · 2011 0.95 · 2012 0.45 · 2013 0.23 · 2014 0.20 · 2015 0.26 · 2016 0.34 · 2017 0.27.
Darwinex vs Dukascopy (2017-10-02 → 2017-12-29 joined on the minute): Duka open − Darwinex bid ≈ −0.09 $ at every hour (a constant offset, not reopen-specific); Duka 01:00→01:05 = +0.083, Darwinex first bid → 01:05 = +0.045.
Costs used: spread 16.37 pt + slippage 2 × 8.19 pt + commission 2 × 0.005 % of price (`assets/symbols/XAUUSD.yaml`, 2026-09-30).
