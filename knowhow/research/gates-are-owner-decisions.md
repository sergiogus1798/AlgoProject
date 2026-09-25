---
q: gate threshold that excludes evidence, MIN_MARKETS, NO EVALUABLE, who decides thresholds, soft screen passed 0, ledger funnel 45 → 0, backfill score distribution
tag: 🔬  date: 2026-09-24  see: research/post-selection-bias, research/pooling-moments
---
# A threshold that removes data is the owner's decision; analysis reports, it doesn't drop
Report every measurement with every reason to distrust it beside it (`inference.warnings()`); hide nothing, decide nothing.
A soft screen removes nobody: aggregators must know which screens act and which only report (`passed` means whatever
the screen decided). Record at run time: a backfilled study keeps only its last gate run's scores (rows stamped `backfill`).

## Evidence
- `strategies/crossmarket/` first build dropped markets with < 30 trades or < 95 % entries on bar open; < 4 surviving markets → NO EVALUABLE.
  `Strategy 24.14.35` NO EVALUABLE despite p = 0.005 on Brent under every null, because 8.6 % of Brent entries were pending fills.
  `MIN_MARKETS = 4` vs the two markets the retest ran → NO EVALUABLE for every XAUUSD strategy forever, silently.
- `XAU_ISOOS_ejemplo` into the global ledger: 120 in, 45 out over eight screens. `familia` (BH over survivors) is `soft`
  ("informa, no elimina"); `funnel.csv` records entered 45, passed 0. Literal → ledger reads 45 → 0. Recorded as `n_out = n_in`, informative count in the note → 45 → 45.
- `backfill` recovers only what artefacts wrote: a funnel stores counts, not scores → accumulated N = last gate run's N, one search of eight.
