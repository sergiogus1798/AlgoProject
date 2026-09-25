---
q: portfolio drawdown bootstrap multiple markets, trade-level bootstrap destroys co-occurrence, calendar block resampling, concurrent positions counted twice close before open lexsort
tag: 🔬  date: 2026-09-16  see: research/robustness-monte-carlo
---
# Bootstrap a multi-market portfolio by whole calendar blocks, never by trades
The dependence that matters is contemporaneous (markets losing the same week). Partition time into N-week
blocks, draw blocks with replacement; all markets' trades in a block travel together. Trade-level reordering
answers a different question ("did sequence matter", net profit invariant) and is no substitute.
Event sweeps: sort closes before opens at equal timestamps (`np.lexsort((moves, times))`).

## Evidence
- `strategies/crossmarket/simulate/portfolio.py`. Trade-level (even block) bootstrap draws trades that never
  co-occurred and reports a falsely narrow drawdown interval.
- 🤔 Sweep over `(open, +1)`/`(close, −1)` reported 4 concurrent positions across 3 markets: re-entry on its own exit bar counted twice.
