---
q: Must I shift engines.regimes.regime.atr by a day before using it?
kw: atr lag, double lag, conditionalMap, regime atr D-1, garch lagged, look-ahead
tag: 🔬  date: 2026-10-04
---
# `regime.atr` is already lagged one day — never shift it again
Value at D = ATR at close of D-1, like `garch()`. `conditionalMap` shifted again (double lag), fixed. `studies/research/marketProfile/context.py` only takes its mean, unaffected.

## Evidence
2026-10-04 cleanup (`CALC_REVIEW.md`).
