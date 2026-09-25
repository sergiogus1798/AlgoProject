---
q: entry quality e-ratio MFE/MAE vs random entries, entryQuality, entries carry least edge, long gold 2020 bar-count exit, no SL TP in corpus
tag: 🔬  date: 2026-09-24  see: research/random-entry-nulls, research/cusum-blind-spot
---
# On this corpus the entries carry least: read null, e-ratio and concentration together
An entry can be indistinguishable from chance while the strategy makes money. The control that settles it is a
random-entry benchmark with the same exits (`PARAMETER_SPACE_TESTS.pdf` D3, `docs/encargos/12`).

## Evidence
- `Strategy 35.44.31` (`studies/readings/entryQuality/`): e-ratio (mean favourable / mean adverse excursion, ATR units) inside the
  5–95 % band of random entries matched on hour of day and long/short split at k = 1, 5, 10, 20, 50; below it at k = 1. Still profitable.
- `studies/readings/monkey/`: only 51 % of 757 XAUUSD strategies beat their null on Sharpe.
- All long (1,119 of 1,119); exits `Exit After X Bars`, `Exit Signal`, `End Of Friday` — no SL/TP in any of 960,705 exported trades; 99 % of profit from one year.
- 🤔 What is measured is closer to "long gold in 2020 with a bar-count exit" than an entry edge. Not a reason to discard the population.
