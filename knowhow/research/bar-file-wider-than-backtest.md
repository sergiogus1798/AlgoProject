---
q: exported bars wider than backtest window, random-entry null samples outside backtest, envelope.window slice first entry last exit, market drift mu_m wrong span
tag: 🔬  date: 2026-09-15  see: research/hardest-null, research/random-entry-nulls, research/zero-duration-trades
---
# Slice the bars to the backtest's own span before any null or benchmark
Apply `envelope.window(trades, bars)` once, first: cut to first entry and last exit, per strategy (not per market),
and pass only the slice downstream. General check for any synthetic-event study: could a simulated trade land
where a real one structurally could not?

## Evidence
- `XAUUSD / Retest Markets - Family`: bars 2003-05 → 2026-01, backtests 2008-01 → 2022-12 — a third of every bar file outside the backtest. Nothing crashed.
- Wrong span contaminated: the random-entry null, `mu_m` (Test 1c), blind-window benchmark (Test 1b), structural profile in `drivers.py`, equity-curve x axis.
