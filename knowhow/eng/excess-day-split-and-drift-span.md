---
q: Is the per-day split of the excess exact, and what can `drift_span` not be?
kw: engines variants excess daily per_trade drift_span variant b d sum of days equals sum of trades invariant drift outside trade year refuses
tag: 🔬  date: 2026-10-07 
---
# The per-day split of the excess is exact for all four drift variants; `b` and `d` need the trade's own year
`engines/variants/excess.py`: Σ over days of `daily` = Σ over trades of `per_trade` to the cent, with
each trade's drift spread in equal parts over its bars (the `d` variant included). `drift_span` says
which bars the drift is measured on; the `b` and `d` variants read the drift of the trade's own year, so a
`drift_span` that leaves that year out makes `per_trade` refuse. Use `a` or `c` there.

## Evidence
`tests/test_variant_excess.py` (the invariant, every variant of `studies/screening/gate/config.yaml`
drift). Used by the WFC's annotation «level with the drift of bars before oos2».
