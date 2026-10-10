---
q: Why did the spp report crash with "unsupported operand NoneType * float" on a distribution overlay?
kw: unsupported operand type(s) for *: 'NoneType' and 'float', blockcheck, distribution(series=, shared bins, p0.5-99.5, counts NaN, IS vs OOS1 overlay, step 16, 0/0
tag: 🔬  date: 2026-10-10  see: pipeline/study-partial-evidence-counts-as-done
---
# A series lying wholly outside the shared bins is a flat zero, not 0/0
`core/study/blocks.py` `distribution(series=…)` takes its bins from the union of the series clipped to
p0.5-99.5. A series with no value inside them gave counts NaN, which JSON turns into None, and
`core/study/blockcheck.py` raised the `TypeError` above (step 16, IS vs OOS1 overlay, 4th of 10
strategies). Fix: such a series is a flat zero and the check accepts an all-zero series (test in
`tests/test_blocks_shared.py`).

## Evidence
`python3 -m studies.breakage.spp.report --project Test_DAX40_M30_momentumL_mc3 --databank SPP_IS`
after the fix: 10 of 10 strategies, 25 s (before: crashed after 3).
